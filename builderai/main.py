import numpy as np
import json
import re
import string
from IPython.display import display, HTML
import tensorflow as tf
from tensorflow.keras import layers, models, losses, callbacks
from Transformer import TransformerBlock, TransformerStack
from TokenAndPositionEmbedding import TokenAndPositionEmbedding
from BuildingGenerator import BuildingGenerator

from Tokenizer import Tokenizer

VOCAB_SIZE = 10000
MAX_LEN = 4096
EMBEDDING_DIM = 256
KEY_DIM = 256
N_HEADS = 8
FEED_FORWARD_DIM = 1024
N_LAYERS = 4
VALIDATION_SPLIT = 0.2
SEED = 42
LOAD_MODEL = False
BATCH_SIZE = 2
ACCUM_STEPS = 4  # Gradient accumulation: effective batch = BATCH_SIZE * ACCUM_STEPS = 8
EPOCHS = 100

tokenizer = Tokenizer()

with open("./data.json") as json_data:
    dataset = json.load(json_data)

tokenizedData = tokenizer.tokenize_dataset(dataset)

text_ds = (
    tf.data.Dataset.from_tensor_slices(tokenizedData)
    .batch(BATCH_SIZE)
    .shuffle(1000)
)

vectorize_layer = layers.TextVectorization(
    standardize="lower",
    max_tokens=VOCAB_SIZE,
    output_mode="int",
    output_sequence_length=MAX_LEN + 1,
)

vectorize_layer.adapt(text_ds)
vocab = vectorize_layer.get_vocabulary()

def prepare_inputs(text):
    text = tf.expand_dims(text, -1)
    tokenized_sentences = vectorize_layer(text)
    x = tokenized_sentences[:, :-1]
    y = tokenized_sentences[:, 1:]
    return x, y


total_samples = len(tokenizedData)
val_size = int(total_samples * VALIDATION_SPLIT)
train_data = tokenizedData[val_size:]
val_data = tokenizedData[:val_size]

train_ds = (
    tf.data.Dataset.from_tensor_slices(train_data)
    .batch(BATCH_SIZE)
    .shuffle(1000)
    .map(prepare_inputs)
)

val_ds = (
    tf.data.Dataset.from_tensor_slices(val_data)
    .batch(BATCH_SIZE)
    .map(prepare_inputs)
)

def causal_attention_mask(batch_size, n_dest, n_src, dtype):
    i = tf.range(n_dest)[:, None]
    j = tf.range(n_src)
    m = i >= j - n_src + n_dest
    mask = tf.cast(m, dtype)
    mask = tf.reshape(mask, [1, n_dest, n_src])
    mult = tf.concat(
        [tf.expand_dims(batch_size, -1), tf.constant([1, 1], dtype=tf.int32)], 0
    )
    return tf.tile(mask, mult)


np.transpose(causal_attention_mask(1, 10, 10, dtype=tf.int32)[0])

class WarmupCosineDecay(tf.keras.optimizers.schedules.LearningRateSchedule):
    def __init__(self, base_lr, warmup_steps, total_steps):
        self.base_lr = base_lr
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps

    def __call__(self, step):
        step = tf.cast(step, tf.float32)
        warmup = tf.minimum(step / self.warmup_steps, 1.0)
        cosine = 0.5 * (1 + tf.cos(3.14159 * step / self.total_steps))
        return self.base_lr * warmup * cosine

    def get_config(self):
        return {
            "base_lr": self.base_lr,
            "warmup_steps": self.warmup_steps,
            "total_steps": self.total_steps,
        }

lr_schedule = WarmupCosineDecay(
    base_lr=1e-3,
    warmup_steps=1000,
    total_steps=EPOCHS * len(train_data) // BATCH_SIZE,
)

inputs = layers.Input(shape=(None,), dtype=tf.int32)
x = TokenAndPositionEmbedding(MAX_LEN, VOCAB_SIZE, EMBEDDING_DIM)(inputs)
x, attention_scores = TransformerStack(
    N_LAYERS, N_HEADS, KEY_DIM, EMBEDDING_DIM, FEED_FORWARD_DIM
)(x)
outputs = layers.Dense(VOCAB_SIZE, activation="softmax")(x)
gpt = models.Model(inputs=inputs, outputs=[outputs, attention_scores])

optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule)
loss_fn = losses.SparseCategoricalCrossentropy()

if LOAD_MODEL:
    gpt = models.load_model("./models/gpt.keras", compile=True)

# Tokenize starting prompt
text_generator = BuildingGenerator(vocab)

# --- Custom training loop with gradient accumulation ---
train_summary_writer = tf.summary.create_file_writer("./logs/train")
val_summary_writer = tf.summary.create_file_writer("./logs/val")

best_val_loss = float("inf")
patience_counter = 0
PATIENCE = 10
best_weights = None

for epoch in range(EPOCHS):
    print(f"\nEpoch {epoch + 1}/{EPOCHS}")

    # --- Training ---
    epoch_loss = tf.keras.metrics.Mean()
    accum_gradients = [tf.zeros_like(v) for v in gpt.trainable_variables]
    step_in_accum = 0

    for step, (x_batch, y_batch) in enumerate(train_ds):
        with tf.GradientTape() as tape:
            preds, _ = gpt(x_batch, training=True)
            loss = loss_fn(y_batch, preds)
            scaled_loss = loss / ACCUM_STEPS

        grads = tape.gradient(scaled_loss, gpt.trainable_variables)
        accum_gradients = [a + g for a, g in zip(accum_gradients, grads)]
        step_in_accum += 1

        if step_in_accum == ACCUM_STEPS:
            optimizer.apply_gradients(zip(accum_gradients, gpt.trainable_variables))
            accum_gradients = [tf.zeros_like(v) for v in gpt.trainable_variables]
            step_in_accum = 0

        epoch_loss.update_state(loss)

    # Apply remaining accumulated gradients
    if step_in_accum > 0:
        optimizer.apply_gradients(zip(accum_gradients, gpt.trainable_variables))

    train_loss = epoch_loss.result().numpy()

    # --- Validation ---
    val_loss_metric = tf.keras.metrics.Mean()
    for x_batch, y_batch in val_ds:
        preds, _ = gpt(x_batch, training=False)
        val_loss_metric.update_state(loss_fn(y_batch, preds))

    val_loss = val_loss_metric.result().numpy()

    print(f"  train_loss: {train_loss:.4f} - val_loss: {val_loss:.4f}")

    # TensorBoard logging
    with train_summary_writer.as_default():
        tf.summary.scalar("loss", train_loss, step=epoch)
    with val_summary_writer.as_default():
        tf.summary.scalar("loss", val_loss, step=epoch)

    # Early stopping
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        best_weights = gpt.get_weights()
        gpt.save_weights("./checkpoint/checkpoint.weights.h5")
    else:
        patience_counter += 1
        if patience_counter >= PATIENCE:
            print(f"  Early stopping at epoch {epoch + 1}")
            break

    # Generate sample building each epoch
    text_generator.model = gpt
    text_generator.on_epoch_end(epoch)

# Restore best weights
if best_weights is not None:
    gpt.set_weights(best_weights)

# Save with compile for easy reloading
gpt.compile(optimizer, loss=[loss_fn, None])
gpt.save("./models/gpt.keras")

def print_probs(info, vocab, top_k=5):
    for i in info:
        highlighted_text = []
        for word, att_score in zip(
            i["prompt"].split(), np.mean(i["atts"], axis=0)
        ):
            highlighted_text.append(
                '<span style="background-color:rgba(135,206,250,'
                + str(att_score / max(np.mean(i["atts"], axis=0)))
                + ');">'
                + word
                + "</span>"
            )
        highlighted_text = " ".join(highlighted_text)
        display(HTML(highlighted_text))

        word_probs = i["word_probs"]
        p_sorted = np.sort(word_probs)[::-1][:top_k]
        i_sorted = np.argsort(word_probs)[::-1][:top_k]
        for p, i in zip(p_sorted, i_sorted):
            print(f"{vocab[i]}:   \t{np.round(100*p,2)}%")
        print("--------\n")

info = text_generator.generate(
    "<start> name=new_house dim=10x6x8 <blocks>", max_tokens=200, temperature=1.0
)

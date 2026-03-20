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
MAX_LEN = 8192
EMBEDDING_DIM = 256
KEY_DIM = 256
N_HEADS = 8
FEED_FORWARD_DIM = 1024
N_LAYERS = 4
VALIDATION_SPLIT = 0.2
SEED = 42
LOAD_MODEL = False
BATCH_SIZE = 8
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
gpt.compile(
    tf.keras.optimizers.Adam(learning_rate=lr_schedule),
    loss=[losses.SparseCategoricalCrossentropy(), None],
)

if LOAD_MODEL:
    # model.load_weights('./models/model')
    gpt = models.load_model("./models/gpt.keras", compile=True)

model_checkpoint_callback = callbacks.ModelCheckpoint(
    filepath="./checkpoint/checkpoint.weights.h5",
    save_weights_only=True,
    save_freq="epoch",
    verbose=0,
)

tensorboard_callback = callbacks.TensorBoard(log_dir="./logs")

early_stopping_callback = callbacks.EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True,
)

# Tokenize starting prompt
text_generator = BuildingGenerator(vocab)

gpt.fit(
    train_ds,
    epochs=EPOCHS,
    validation_data=val_ds,
    callbacks=[model_checkpoint_callback, tensorboard_callback, text_generator, early_stopping_callback],
)
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

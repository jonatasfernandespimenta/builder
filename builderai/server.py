"""
AI server for the Minecraft BuilderBot.
Loads the trained model and exposes a /generate endpoint.

Usage:
    python server.py

The bot calls this with --ai flag:
    node index.js --ai
"""

import json
import os
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from http.server import HTTPServer, BaseHTTPRequestHandler

from Tokenizer import Tokenizer
from Transformer import TransformerBlock
from TokenAndPositionEmbedding import TokenAndPositionEmbedding

HOST = "0.0.0.0"
PORT = 5050

VOCAB_SIZE = 10000
MAX_LEN = 4096
EMBEDDING_DIM = 256
KEY_DIM = 256
N_HEADS = 4
FEED_FORWARD_DIM = 512

# Style -> prompt mapping
STYLE_PROMPTS = {
    "house": "<start> name=new_house dim=10x8x10 <blocks>",
    "tower": "<start> name=new_tower dim=8x20x8 <blocks>",
    "castle": "<start> name=new_castle dim=20x15x20 <blocks>",
    "medieval": "<start> name=medieval_house dim=12x10x12 <blocks>",
    "fantasy": "<start> name=fantasy_building dim=14x12x14 <blocks>",
    "modern": "<start> name=modern_house dim=12x8x12 <blocks>",
    "church": "<start> name=small_church dim=10x14x16 <blocks>",
    "bridge": "<start> name=stone_bridge dim=20x6x6 <blocks>",
    "wall": "<start> name=castle_wall dim=20x8x4 <blocks>",
    "hut": "<start> name=small_hut dim=6x5x6 <blocks>",
}


def load_model():
    """Load the trained model and vocabulary."""
    weights_path = os.path.join(os.path.dirname(__file__), "checkpoint", "checkpoint.weights.h5")
    data_path = os.path.join(os.path.dirname(__file__), "data.json")

    if not os.path.exists(weights_path):
        print(f"ERROR: No trained weights found at {weights_path}")
        print("Train the model first with: python main.py")
        sys.exit(1)

    # Rebuild the vectorize layer with the same data to get the vocab
    tokenizer = Tokenizer()
    with open(data_path) as f:
        dataset = json.load(f)

    tokenized_data = tokenizer.tokenize_dataset(dataset)

    vectorize_layer = layers.TextVectorization(
        standardize="lower",
        max_tokens=VOCAB_SIZE,
        output_mode="int",
        output_sequence_length=MAX_LEN + 1,
    )

    text_ds = tf.data.Dataset.from_tensor_slices(tokenized_data).batch(32)
    vectorize_layer.adapt(text_ds)
    vocab = vectorize_layer.get_vocabulary()

    # Rebuild model architecture and load weights
    inputs = layers.Input(shape=(None,), dtype=tf.int32)
    x = TokenAndPositionEmbedding(MAX_LEN, VOCAB_SIZE, EMBEDDING_DIM)(inputs)
    x, attention_scores = TransformerBlock(N_HEADS, KEY_DIM, EMBEDDING_DIM, FEED_FORWARD_DIM)(x)
    outputs = layers.Dense(VOCAB_SIZE, activation="softmax")(x)
    gpt = models.Model(inputs=inputs, outputs=[outputs, attention_scores])
    gpt.load_weights(weights_path)
    print(f"Model loaded from {weights_path}")

    return gpt, vocab, tokenizer


def generate_building_stream(model, vocab, prompt, max_tokens=4096, temperature=0.8):
    """Generate tokens one by one, yielding complete blocks as they form.
    Uses a sliding window to keep memory bounded."""
    WINDOW_SIZE = 512
    word_to_index = {word: i for i, word in enumerate(vocab)}

    start_tokens = [word_to_index.get(x, 1) for x in prompt.split()]

    sample_token = None
    # Buffer to accumulate tokens for current block (m# x# y# z#)
    block_buf = []

    while len(start_tokens) < max_tokens and sample_token != 0:
        window = start_tokens[-WINDOW_SIZE:]
        x = np.array([window])
        y, _ = model.predict(x, verbose=0)

        probs = y[0][-1][:len(vocab)]
        probs = probs ** (1 / temperature)
        probs = probs / np.sum(probs)
        sample_token = np.random.choice(len(probs), p=probs)

        start_tokens.append(sample_token)
        word = vocab[sample_token]

        if len(start_tokens) % 100 == 0:
            print(f"  {len(start_tokens)} tokens...")
        if len(start_tokens) <= 30:
            print(f"  token: '{word}'")

        if word == "<end>":
            break

        # Skip header tokens
        if word in ("<start>", "<blocks>") or word.startswith("name=") or word.startswith("dim=") or word.startswith("tag="):
            continue

        # When we see a new m# token, start a fresh buffer
        if word.startswith("m") and word[1:].isdigit():
            block_buf = [word]
        else:
            block_buf.append(word)

        # A complete block is: m# x# y# z# (4 tokens)
        if len(block_buf) == 4 and block_buf[0].startswith("m") and block_buf[1].startswith("x") and block_buf[2].startswith("y") and block_buf[3].startswith("z"):
            try:
                mat_id = block_buf[0][1:]
                bx = int(block_buf[1][1:])
                by = int(block_buf[2][1:])
                bz = int(block_buf[3][1:])
                block_buf = []
                block = {"mat_id": mat_id, "x": bx, "y": by, "z": bz}
                print(f"  block: {block}")
                yield block
            except (ValueError, IndexError):
                block_buf = []

        # Reset buffer if it gets too long (malformed tokens)
        if len(block_buf) > 8:
            print(f"  dropping malformed: {block_buf}")
            block_buf = []

    print(f"Generated {len(start_tokens)} tokens")


def generate_building(model, vocab, tokenizer, prompt, max_tokens=800, temperature=0.5):
    """Generate a building using full context (no sliding window). Keep max_tokens <= 800 on M2."""
    word_to_index = {word: i for i, word in enumerate(vocab)}

    start_tokens = [word_to_index.get(x, 1) for x in prompt.split()]
    generated = prompt

    sample_token = None
    while len(start_tokens) < max_tokens and sample_token != 0:
        x = np.array([start_tokens])
        y, _ = model.predict(x, verbose=0)

        probs = y[0][-1][:len(vocab)]
        probs = probs ** (1 / temperature)
        probs = probs / np.sum(probs)
        sample_token = np.random.choice(len(probs), p=probs)

        start_tokens.append(sample_token)
        word = vocab[sample_token]
        generated += " " + word

        if len(start_tokens) % 100 == 0:
            print(f"  {len(start_tokens)} tokens...")

        if word == "<end>":
            break

    print(f"Generated {len(start_tokens)} tokens")
    building = tokenizer.detokenize(generated)
    return building


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/generate":
            self._handle_generate()
        elif self.path == "/generate/stream":
            self._handle_stream()
        else:
            self.send_error(404)

    def _handle_generate(self):
        """Original non-streaming endpoint."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        style = body.get("style", "house")
        max_tokens = min(body.get("max_tokens", 800), 800)
        temperature = body.get("temperature", 0.5)
        prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["house"])

        print(f"Generating: style={style}, max_tokens={max_tokens}, temp={temperature}")
        building = generate_building(
            self.server.model, self.server.vocab, self.server.tokenizer,
            prompt, max_tokens, temperature,
        )
        response = json.dumps(building)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode())

    def _handle_stream(self):
        """Streaming endpoint — sends one JSON block per line as generated."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        style = body.get("style", "house")
        max_tokens = min(body.get("max_tokens", 4096), 4096)
        temperature = body.get("temperature", 0.5)
        prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["house"])

        print(f"Streaming: style={style}, max_tokens={max_tokens}, temp={temperature}")

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        count = 0
        for block in generate_building_stream(
            self.server.model, self.server.vocab, prompt, max_tokens, temperature,
        ):
            line = json.dumps(block) + "\n"
            self.wfile.write(line.encode())
            self.wfile.flush()
            count += 1

        print(f"Streamed {count} blocks")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif self.path == "/styles":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(list(STYLE_PROMPTS.keys())).encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print(f"[server] {args[0]}")


def main():
    print("Loading model...")
    model, vocab, tokenizer = load_model()

    server = HTTPServer((HOST, PORT), Handler)
    server.model = model
    server.vocab = vocab
    server.tokenizer = tokenizer

    # Warmup: compile the TF graph so first request isn't slow
    print("Warming up model...")
    dummy = np.array([[1, 2, 3]])
    model.predict(dummy, verbose=0)
    print("Ready!")

    print(f"AI server running on http://{HOST}:{PORT}")
    print(f"Endpoints:")
    print(f"  POST /generate  - Generate a building")
    print(f"  GET  /styles    - List available styles")
    print(f"  GET  /health    - Health check")
    server.serve_forever()


if __name__ == "__main__":
    main()

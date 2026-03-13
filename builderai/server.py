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
PORT = 5000

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
    model_path = os.path.join(os.path.dirname(__file__), "models", "gpt")
    data_path = os.path.join(os.path.dirname(__file__), "data.json")

    if not os.path.exists(model_path):
        print(f"ERROR: No trained model found at {model_path}")
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

    # Load the trained model
    gpt = models.load_model(model_path, compile=False)
    print(f"Model loaded from {model_path}")

    return gpt, vocab, tokenizer


def generate_building(model, vocab, tokenizer, prompt, max_tokens=4096, temperature=0.8):
    """Generate a building from a prompt string."""
    word_to_index = {word: i for i, word in enumerate(vocab)}

    start_tokens = [word_to_index.get(x, 1) for x in prompt.split()]
    generated = prompt

    sample_token = None
    while len(start_tokens) < max_tokens and sample_token != 0:
        x = np.array([start_tokens])
        y, _ = model.predict(x, verbose=0)

        probs = y[0][-1]
        probs = probs ** (1 / temperature)
        probs = probs / np.sum(probs)
        sample_token = np.random.choice(len(probs), p=probs)

        start_tokens.append(sample_token)
        word = vocab[sample_token]
        generated += " " + word

        # Stop if we hit <end>
        if word == "<end>":
            break

    print(f"Generated {len(start_tokens)} tokens")
    building = tokenizer.detokenize(generated)
    return building


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        style = body.get("style", "house")
        max_tokens = min(body.get("max_tokens", 4096), MAX_LEN)
        temperature = body.get("temperature", 0.8)

        # Build the prompt from the style
        prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["house"])

        print(f"Generating: style={style}, max_tokens={max_tokens}, temp={temperature}")
        building = generate_building(
            self.server.model,
            self.server.vocab,
            self.server.tokenizer,
            prompt,
            max_tokens,
            temperature,
        )

        response = json.dumps(building)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode())

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

    print(f"AI server running on http://{HOST}:{PORT}")
    print(f"Endpoints:")
    print(f"  POST /generate  - Generate a building")
    print(f"  GET  /styles    - List available styles")
    print(f"  GET  /health    - Health check")
    server.serve_forever()


if __name__ == "__main__":
    main()

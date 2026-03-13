"""
Prepares data.json from the raw grabcraft_data.json.
Filters out broken entries and buildings that exceed MAX_LEN tokens.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from Tokenizer import Tokenizer

MAX_LEN = 4096
INPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "grabcraft-scrapper", "grabcraft_data.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data.json")

def main():
    with open(INPUT_PATH) as f:
        raw = json.load(f)

    print(f"Raw buildings: {len(raw)}")

    tokenizer = Tokenizer()
    clean = []
    skipped_empty = 0
    skipped_long = 0

    for building in raw:
        # Skip broken entries (scraping errors, no blocks, missing dims)
        if not building.get("blocks") or building["dimensions"].get("width") is None:
            skipped_empty += 1
            continue

        count = tokenizer.token_count(building)
        if count > MAX_LEN:
            skipped_long += 1
            continue

        clean.append(building)

    print(f"Skipped (empty/broken): {skipped_empty}")
    print(f"Skipped (>{MAX_LEN} tokens): {skipped_long}")
    print(f"Kept: {len(clean)}")

    # Show stats
    counts = [tokenizer.token_count(b) for b in clean]
    counts.sort()
    print(f"Token range: {counts[0]} - {counts[-1]}")
    print(f"Median tokens: {counts[len(counts)//2]}")

    # Show some examples
    print("\nSample buildings:")
    for b in clean[:3]:
        tok = tokenizer.tokenize_construction(b)
        print(f"  {b['name']}: {tokenizer.token_count(b)} tokens, {len(b['blocks'])} blocks")
        print(f"    First 100 chars: {tok[:100]}...")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(clean, f)

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"\nSaved {OUTPUT_PATH} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()

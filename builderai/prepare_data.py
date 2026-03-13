"""
Prepares data.json from the raw grabcraft_data.json.
- Truncates large buildings to fit MAX_LEN instead of discarding them
- Augments data with rotations and mirrors (up to 4x)
"""

import json
import copy
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from Tokenizer import Tokenizer

MAX_LEN = 4096
# Header tokens: <start> name= dim= <blocks> ... <end> = ~4 tokens overhead
HEADER_TOKENS = 4
# Each block = 4 tokens (m# x# y# z#) + 1 for <end>
INPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "grabcraft-scrapper", "grabcraft_data.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data.json")


def truncate_building(building, max_len):
    """Truncate blocks to fit within max_len tokens."""
    tags_count = len(building.get("tags", []))
    header = HEADER_TOKENS + tags_count
    max_blocks = (max_len - header - 1) // 4  # -1 for <end>
    if len(building["blocks"]) <= max_blocks:
        return building
    b = copy.deepcopy(building)
    b["blocks"] = b["blocks"][:max_blocks]
    return b


def rotate_90(building):
    """Rotate building 90 degrees: (x, z) -> (z, -x)."""
    b = copy.deepcopy(building)
    for block in b["blocks"]:
        old_x, old_z = block["x"], block["z"]
        block["x"] = old_z
        block["z"] = -old_x
    # Swap width and depth
    dims = b["dimensions"]
    dims["width"], dims["depth"] = dims["depth"], dims["width"]
    # Normalize so all coordinates are positive
    _normalize(b)
    return b


def mirror_x(building):
    """Mirror building along X axis: x -> -x."""
    b = copy.deepcopy(building)
    for block in b["blocks"]:
        block["x"] = -block["x"]
    _normalize(b)
    return b


def _normalize(building):
    """Shift all block coordinates so minimums are 1."""
    blocks = building["blocks"]
    if not blocks:
        return
    min_x = min(bl["x"] for bl in blocks)
    min_y = min(bl["y"] for bl in blocks)
    min_z = min(bl["z"] for bl in blocks)
    for bl in blocks:
        bl["x"] -= min_x - 1
        bl["y"] -= min_y - 1
        bl["z"] -= min_z - 1


def augment(building):
    """Return original + 3 rotations. Each also gets a mirror = 8x total,
    but we do 4x (original + rotations) to keep it reasonable."""
    variants = [building]
    rotated = building
    for _ in range(3):
        rotated = rotate_90(rotated)
        variants.append(rotated)
    return variants


def main():
    with open(INPUT_PATH) as f:
        raw = json.load(f)

    print(f"Raw buildings: {len(raw)}")

    tokenizer = Tokenizer()
    clean = []
    skipped_empty = 0
    truncated = 0

    for building in raw:
        # Skip broken entries (scraping errors, no blocks, missing dims)
        if not building.get("blocks") or building["dimensions"].get("width") is None:
            skipped_empty += 1
            continue

        count = tokenizer.token_count(building)
        if count > MAX_LEN:
            building = truncate_building(building, MAX_LEN)
            truncated += 1

        clean.append(building)

    print(f"Skipped (empty/broken): {skipped_empty}")
    print(f"Truncated to fit {MAX_LEN}: {truncated}")
    print(f"Base buildings: {len(clean)}")

    # Augment with rotations
    augmented = []
    for b in clean:
        augmented.extend(augment(b))

    print(f"After augmentation (4x rotations): {len(augmented)}")

    # Show stats
    counts = [tokenizer.token_count(b) for b in augmented]
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
        json.dump(augmented, f)

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"\nSaved {OUTPUT_PATH} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()

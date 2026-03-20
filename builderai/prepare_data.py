"""
Prepares data.json from the raw grabcraft_data.json.
- Filters buildings exceeding MAX_BLOCKS
- Truncates large buildings to fit MAX_LEN instead of discarding them
- Augments data with rotations and mirrors (8x)
"""

import json
import copy
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from Tokenizer import Tokenizer

MAX_LEN = 4096
MAX_BLOCKS = 1000
# Header tokens: <start> name= dim= <blocks> ... <end> = ~4 tokens overhead
HEADER_TOKENS = 4
# Each block = 4 tokens (m# x# y# z#) + 1 for <end>
INPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "grabcraft-scrapper", "grabcraft_data.json")
SCHEMATICS_PATH = os.path.join(os.path.dirname(__file__), "schematics_data.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data.json")


def sort_blocks_spatially(building):
    """Sort blocks by y (bottom-up), then x, then z for spatial locality."""
    b = copy.deepcopy(building)
    b["blocks"] = sorted(b["blocks"], key=lambda bl: (bl["y"], bl["x"], bl["z"]))
    return b


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


def mirror_z(building):
    """Mirror building along Z axis: z -> -z."""
    b = copy.deepcopy(building)
    for block in b["blocks"]:
        block["z"] = -block["z"]
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
    """Return original + 3 rotations, each with its mirror = 8x total."""
    rotations = [building]
    rotated = building
    for _ in range(3):
        rotated = rotate_90(rotated)
        rotations.append(rotated)
    variants = []
    for r in rotations:
        variants.append(r)
        variants.append(mirror_x(r))
    return variants


def main():
    with open(INPUT_PATH) as f:
        raw = json.load(f)

    # Also load schematics data if available
    if os.path.exists(SCHEMATICS_PATH):
        with open(SCHEMATICS_PATH) as f:
            schematics = json.load(f)
        print(f"Schematics buildings: {len(schematics)}")
        raw.extend(schematics)

    print(f"Raw buildings: {len(raw)}")

    # Filter buildings with too many blocks
    before_filter = len(raw)
    raw = [b for b in raw if len(b.get("blocks", [])) <= MAX_BLOCKS]
    filtered_out = before_filter - len(raw)
    print(f"Filtered out (>{MAX_BLOCKS} blocks): {filtered_out}")

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

    # Sort blocks spatially for better sequence locality
    clean = [sort_blocks_spatially(b) for b in clean]
    print("Applied spatial ordering (y → x → z)")

    # Augment with rotations
    augmented = []
    for b in clean:
        augmented.extend(augment(b))

    print(f"After augmentation (8x rotations+mirrors): {len(augmented)}")

    # Show stats
    counts = [tokenizer.token_count(b) for b in augmented]
    counts.sort()
    print(f"Token range: {counts[0]} - {counts[-1]}")
    print(f"Median tokens: {counts[len(counts)//2]}")

    # Token count distribution
    buckets = {"0-1000": 0, "1000-2000": 0, "2000-4000": 0, "4000-8000": 0, "8000+": 0}
    for c in counts:
        if c < 1000:
            buckets["0-1000"] += 1
        elif c < 2000:
            buckets["1000-2000"] += 1
        elif c < 4000:
            buckets["2000-4000"] += 1
        elif c < 8000:
            buckets["4000-8000"] += 1
        else:
            buckets["8000+"] += 1
    print("Token distribution:")
    for bucket, count in buckets.items():
        print(f"  {bucket}: {count}")

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

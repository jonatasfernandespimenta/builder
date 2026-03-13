"""
Import .schem and .schematic files into our training data format.
Converts Minecraft schematics to the same JSON format as grabcraft data.

Usage:
    python import_schematics.py <path_to_schematics_folder>

Outputs buildings to schematics_data.json, then run prepare_data.py to merge.
"""

import json
import os
import sys
import gzip
import nbtlib

# Minecraft block ID -> our mat_id mapping (reverse of block-map.json)
# Load from block-map.json to stay consistent
BLOCK_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "builder-bot", "block-map.json")


def load_reverse_block_map():
    """Create minecraft_name -> mat_id mapping from block-map.json."""
    if not os.path.exists(BLOCK_MAP_PATH):
        print(f"WARNING: {BLOCK_MAP_PATH} not found, using block names as mat_id")
        return {}

    with open(BLOCK_MAP_PATH) as f:
        block_map = json.load(f)

    # Reverse: minecraft_name -> mat_id
    reverse = {}
    for mat_id, mc_name in block_map.items():
        reverse[mc_name] = mat_id
        reverse[f"minecraft:{mc_name}"] = mat_id
    return reverse


def parse_schem(filepath, reverse_map):
    """Parse a .schem (Sponge format) file."""
    try:
        nbt = nbtlib.load(filepath)
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return None

    # Navigate to the schematic root
    root = nbt
    if "Schematic" in root:
        root = root["Schematic"]

    width = int(root.get("Width", 0))
    height = int(root.get("Height", 0))
    length = int(root.get("Length", 0))

    if not width or not height or not length:
        return None

    # Get palette
    palette_tag = root.get("Palette", {})
    # Palette maps block_state_string -> index
    # We need index -> block_state_string
    palette = {}
    for block_state, index in palette_tag.items():
        palette[int(index)] = str(block_state)

    # Get block data
    block_data = root.get("BlockData", [])
    if not block_data:
        block_data = root.get("Data", [])

    blocks = []
    i = 0
    for y in range(height):
        for z in range(length):
            for x in range(width):
                if i >= len(block_data):
                    break

                # Handle varint encoding
                value = 0
                shift = 0
                while True:
                    if i >= len(block_data):
                        break
                    b = int(block_data[i]) & 0xFF
                    i += 1
                    value |= (b & 0x7F) << shift
                    if (b & 0x80) == 0:
                        break
                    shift += 7

                block_state = palette.get(value, "minecraft:air")

                # Skip air blocks
                mc_name = block_state.split("[")[0]  # Remove block state properties
                mc_name = mc_name.replace("minecraft:", "")
                if mc_name == "air" or mc_name == "cave_air" or mc_name == "void_air":
                    continue

                # Map to our mat_id
                mat_id = reverse_map.get(mc_name, reverse_map.get(f"minecraft:{mc_name}"))
                if mat_id is None:
                    # Use a hash as fallback mat_id
                    mat_id = str(abs(hash(mc_name)) % 2000)

                blocks.append({
                    "x": x + 1,
                    "y": y + 1,
                    "z": z + 1,
                    "mat_id": mat_id,
                })

    if not blocks:
        return None

    name = os.path.splitext(os.path.basename(filepath))[0]
    name = name.replace("_", " ").replace("-", " ")

    return {
        "name": name,
        "tags": [],
        "dimensions": {
            "width": width,
            "height": height,
            "depth": length,
        },
        "blocks": blocks,
    }


def parse_schematic(filepath, reverse_map):
    """Parse a .schematic (MCEdit legacy format) file."""
    try:
        nbt = nbtlib.load(filepath)
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return None

    root = nbt
    if "Schematic" in root:
        root = root["Schematic"]

    width = int(root.get("Width", 0))
    height = int(root.get("Height", 0))
    length = int(root.get("Length", 0))

    if not width or not height or not length:
        return None

    block_ids = root.get("Blocks", [])
    block_data = root.get("Data", [])

    blocks = []
    for y in range(height):
        for z in range(length):
            for x in range(width):
                idx = (y * length + z) * width + x
                if idx >= len(block_ids):
                    break

                block_id = int(block_ids[idx]) & 0xFF
                if block_id == 0:  # air
                    continue

                mat_id = str(block_id)

                blocks.append({
                    "x": x + 1,
                    "y": y + 1,
                    "z": z + 1,
                    "mat_id": mat_id,
                })

    if not blocks:
        return None

    name = os.path.splitext(os.path.basename(filepath))[0]
    name = name.replace("_", " ").replace("-", " ")

    return {
        "name": name,
        "tags": [],
        "dimensions": {
            "width": width,
            "height": height,
            "depth": length,
        },
        "blocks": blocks,
    }


def import_folder(folder_path):
    """Import all schematics from a folder."""
    reverse_map = load_reverse_block_map()
    buildings = []
    errors = 0

    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for f in filenames:
            if f.endswith(".schem") or f.endswith(".schematic"):
                files.append(os.path.join(root, f))

    print(f"Found {len(files)} schematic files")

    for filepath in files:
        ext = os.path.splitext(filepath)[1]
        try:
            if ext == ".schem":
                building = parse_schem(filepath, reverse_map)
            else:
                building = parse_schematic(filepath, reverse_map)

            if building and building["blocks"]:
                buildings.append(building)
                print(f"  OK: {building['name']} ({len(building['blocks'])} blocks)")
            else:
                errors += 1
        except Exception as e:
            print(f"  FAIL: {filepath}: {e}")
            errors += 1

    return buildings, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_schematics.py <folder_with_schematics>")
        print("\nDownload schematics from sites like:")
        print("  - Planet Minecraft (planetminecraft.com)")
        print("  - Minecraft Schematics (minecraft-schematics.com)")
        print("\nPlace .schem or .schematic files in a folder and point to it.")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a directory")
        sys.exit(1)

    buildings, errors = import_folder(folder)

    output_path = os.path.join(os.path.dirname(__file__), "schematics_data.json")
    with open(output_path, "w") as f:
        json.dump(buildings, f)

    print(f"\nImported: {len(buildings)}")
    print(f"Errors: {errors}")
    print(f"Saved to: {output_path}")
    print(f"\nNow update prepare_data.py to also load schematics_data.json,")
    print(f"or merge it with grabcraft_data.json manually.")


if __name__ == "__main__":
    main()

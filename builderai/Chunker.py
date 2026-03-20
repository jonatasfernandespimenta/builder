import numpy as np
from typing import List, Dict, Tuple


class Chunker:
    """Divides buildings into spatial chunks (like ViT patches but in 3D).

    Instead of serializing every block individually, groups blocks into
    chunk_size x chunk_size x chunk_size sub-volumes. Each chunk becomes
    a unit in the sequence, dramatically reducing sequence length while
    preserving spatial structure.
    """

    def __init__(self, chunk_size: int = 4):
        self.chunk_size = chunk_size

    def get_chunk_id(self, x: int, y: int, z: int) -> Tuple[int, int, int]:
        """Map a block coordinate to its chunk coordinate."""
        return (
            x // self.chunk_size,
            y // self.chunk_size,
            z // self.chunk_size,
        )

    def chunk_building(self, building: dict) -> List[dict]:
        """Group blocks into spatial chunks.

        Returns a list of chunk dicts, each with:
        - chunk_pos: (cx, cy, cz) chunk coordinates
        - blocks: list of blocks in this chunk (with LOCAL coordinates within the chunk)
        """
        chunks = {}

        for block in building["blocks"]:
            bx, by, bz = block["x"], block["y"], block["z"]
            chunk_id = self.get_chunk_id(bx, by, bz)

            if chunk_id not in chunks:
                chunks[chunk_id] = {
                    "chunk_pos": chunk_id,
                    "blocks": [],
                }

            # Store block with LOCAL coordinates (relative to chunk origin)
            local_block = {
                "mat_id": block.get("mat_id", "0"),
                "name": block.get("name", ""),
                "x": bx % self.chunk_size,
                "y": by % self.chunk_size,
                "z": bz % self.chunk_size,
            }
            chunks[chunk_id]["blocks"].append(local_block)

        # Sort chunks spatially: by y (bottom-up), then x, then z
        sorted_chunks = sorted(
            chunks.values(),
            key=lambda c: (c["chunk_pos"][1], c["chunk_pos"][0], c["chunk_pos"][2])
        )

        return sorted_chunks

    def tokenize_chunked(self, building: dict, tokenizer) -> str:
        """Tokenize a building using chunk boundaries.

        Format:
        <start> name=X dim=WxHxD <blocks>
        <chunk> cx0 cy0 cz0 m_stone lx0 ly0 lz0 m_planks lx1 ly1 lz1 </chunk>
        <chunk> cx1 cy1 cz1 ... </chunk>
        <end>

        The <chunk> / </chunk> delimiters let the model learn chunk boundaries.
        Local coordinates (l prefix) are 0 to chunk_size-1, much smaller numbers.
        """
        tokens = []
        tokens.append("<start>")
        tokens.append(f"name={tokenizer.sanitize(building['name'])}")

        for tag in building.get("tags", []):
            tokens.append(f"tag={tokenizer.sanitize(tag)}")

        dims = building["dimensions"]
        tokens.append(f"dim={dims['width']}x{dims['height']}x{dims['depth']}")
        tokens.append("<blocks>")

        chunks = self.chunk_building(building)

        for chunk in chunks:
            cx, cy, cz = chunk["chunk_pos"]
            tokens.append("<chunk>")
            tokens.append(f"cx{cx}")
            tokens.append(f"cy{cy}")
            tokens.append(f"cz{cz}")

            for block in chunk["blocks"]:
                tokens.append(tokenizer.cluster_material(block))
                tokens.append(f"lx{block['x']}")
                tokens.append(f"ly{block['y']}")
                tokens.append(f"lz{block['z']}")

            tokens.append("</chunk>")

        tokens.append("<end>")
        return " ".join(tokens)

    def detokenize_chunked(self, text: str) -> dict:
        """Convert chunked token string back to a building dict."""
        tokens = text.split()
        building = {"name": "", "tags": [], "dimensions": {}, "blocks": []}

        i = 0
        current_chunk_pos = None

        while i < len(tokens):
            t = tokens[i]

            if t in ("<start>", "<end>", "<blocks>"):
                i += 1
            elif t.startswith("name="):
                building["name"] = t[5:].replace("_", " ")
                i += 1
            elif t.startswith("tag="):
                building["tags"].append(t[4:].replace("_", " "))
                i += 1
            elif t.startswith("dim="):
                parts = t[4:].split("x")
                if len(parts) == 3:
                    building["dimensions"] = {
                        "width": int(parts[0]),
                        "height": int(parts[1]),
                        "depth": int(parts[2]),
                    }
                i += 1
            elif t == "<chunk>":
                # Next 3 tokens are cx, cy, cz
                if i + 3 < len(tokens):
                    try:
                        cx = int(tokens[i + 1][2:])
                        cy = int(tokens[i + 2][2:])
                        cz = int(tokens[i + 3][2:])
                        current_chunk_pos = (cx, cy, cz)
                        i += 4
                    except (ValueError, IndexError):
                        i += 1
                else:
                    i += 1
            elif t == "</chunk>":
                current_chunk_pos = None
                i += 1
            elif t.startswith("m_") and current_chunk_pos and i + 3 < len(tokens):
                try:
                    mat_cluster = t
                    lx = int(tokens[i + 1][2:])  # strip "lx"
                    ly = int(tokens[i + 2][2:])  # strip "ly"
                    lz = int(tokens[i + 3][2:])  # strip "lz"

                    # Convert local coords back to global
                    cx, cy, cz = current_chunk_pos
                    global_x = cx * self.chunk_size + lx
                    global_y = cy * self.chunk_size + ly
                    global_z = cz * self.chunk_size + lz

                    building["blocks"].append({
                        "mat_id": mat_cluster,
                        "x": global_x,
                        "y": global_y,
                        "z": global_z,
                    })
                    i += 4
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1

        return building

    def chunked_token_count(self, building: dict) -> int:
        """Estimate token count for chunked representation."""
        chunks = self.chunk_building(building)
        header = 3 + len(building.get("tags", []))  # <start> name= dim=
        blocks_section = 1  # <blocks>

        for chunk in chunks:
            blocks_section += 5  # <chunk> cx cy cz ... </chunk>
            blocks_section += len(chunk["blocks"]) * 4  # mat lx ly lz per block

        return header + blocks_section + 1  # +1 for <end>

    def stats(self, building: dict) -> dict:
        """Return chunking statistics for a building."""
        chunks = self.chunk_building(building)
        blocks_per_chunk = [len(c["blocks"]) for c in chunks]
        return {
            "total_blocks": len(building["blocks"]),
            "num_chunks": len(chunks),
            "avg_blocks_per_chunk": sum(blocks_per_chunk) / len(blocks_per_chunk) if blocks_per_chunk else 0,
            "max_blocks_per_chunk": max(blocks_per_chunk) if blocks_per_chunk else 0,
            "min_blocks_per_chunk": min(blocks_per_chunk) if blocks_per_chunk else 0,
            "chunk_size": self.chunk_size,
        }

class Tokenizer:
    def __init__(self):
        pass

    def sanitize(self, value: str) -> str:
        return value.strip().replace(" ", "_")

    def tokenize_construction(self, construction: dict) -> str:
        tokens = []

        tokens.append("<start>")
        tokens.append(f"name={self.sanitize(construction['name'])}")

        for tag in construction.get("tags", []):
            tokens.append(f"tag={self.sanitize(tag)}")

        dims = construction["dimensions"]
        tokens.append(f"dim={dims['width']}x{dims['height']}x{dims['depth']}")

        tokens.append("<blocks>")
        for block in construction["blocks"]:
            tokens.append(f"m{block.get('mat_id', '0')}")
            tokens.append(f"x{block['x']}")
            tokens.append(f"y{block['y']}")
            tokens.append(f"z{block['z']}")
        tokens.append("<end>")

        return " ".join(tokens)

    def token_count(self, construction: dict) -> int:
        """Return the number of tokens without building the full string."""
        header = 3  # <start> name= dim=
        header += len(construction.get("tags", []))
        blocks = len(construction["blocks"]) * 4
        return header + 1 + blocks + 1  # <blocks> + <end>

    def detokenize(self, text: str) -> dict:
        """Convert a generated token string back into a building dict."""
        tokens = text.split()
        building = {"name": "", "tags": [], "dimensions": {}, "blocks": []}

        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t == "<start>" or t == "<end>":
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
            elif t == "<blocks>":
                i += 1
            elif t.startswith("m") and i + 3 < len(tokens):
                try:
                    mat_id = t[1:]
                    x = int(tokens[i + 1][1:])
                    y = int(tokens[i + 2][1:])
                    z = int(tokens[i + 3][1:])
                    building["blocks"].append(
                        {"mat_id": mat_id, "x": x, "y": y, "z": z}
                    )
                    i += 4
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1

        return building

    def tokenize_dataset(self, data: list[dict]) -> list[str]:
        return [self.tokenize_construction(item) for item in data]

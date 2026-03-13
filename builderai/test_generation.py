"""
Quick test: detokenize the first epoch's generated text and print the building JSON.
Pass the output to the bot or inspect it directly.
"""

import json
import os
from Tokenizer import Tokenizer

generated_text = "<start> name=small_house dim=6x5x6 <blocks> m14 x1 y1 z14 m32 x1 y3 z9 m19 x11 y1 z1 m4 x14 y1 z12 m14 x2 y1 z6 m325 x3 y1 z13 m60 m15 x9 y28 z14 m15 x12 y1 z4 m53 x6 y1 z11 m133 m93 x10 y14 z10 m53 x13 y3 z9 m205 x9 y1 z7 m14 x3 y2 z2 m53 x4 y1 z12"

tokenizer = Tokenizer()
building = tokenizer.detokenize(generated_text)

output_path = os.path.join(os.path.dirname(__file__), "..", "builder-bot", "generation.json")
with open(output_path, "w") as f:
    json.dump(building, f, indent=2)

print(json.dumps(building, indent=2))
print(f"\nTotal blocks: {len(building['blocks'])}")
print(f"Dimensions: {building['dimensions']}")
print(f"\nSaved to {output_path}")

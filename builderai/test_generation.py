"""
Quick test: detokenize the first epoch's generated text and print the building JSON.
Pass the output to the bot or inspect it directly.
"""

import json
import os
from Tokenizer import Tokenizer

generated_text = "<start> name=small_house dim=6x5x6 <blocks> m4 x4 y1 z6 m4 x2 y1 z8 m15 x4 y1 z1 m14 x4 y1 z1 m15 x4 y1 z4 m15 x4 y1 z6 m15 x4 y1 z6 m15 x4 y1 z2 m15 x4 y1 z2 m15 x4 y1 z6 m14 x4 y1 z4 m15 x4 y1 z3 m15 x4 y1 z4 m15 x4 y1 z6 m15 x3 y1 z5 m15 x3 y1 z6 m15 x3 y1 z8 m15 x4 y1 z3 m15 x4 y1 z1 m14 x4 y1 z3 m18 x4 y1 z8 m14 x4 y1 z1 m15 x4 y1 z2 m14 x4 y1 z9 m15 x4 y1 z2 m15 x4 y1 z1 m15 x4 y1 z6 m15 x4 y1 z8 m15 x6 y1 z1 m14 x9 y1 z8 m14 x9 y1 z1 m15 x9 y1 z5 m15 x9 y1 z5 m15 x10 y1 z1 m14 x10 y1 z9 m15 x10 y1 z2 m15 x10 y1 z3 m15 x10 y1 z7 m15 x10 y1 z2 m15 x10 y1 z1 m15 x7 y1 z1 m15 x8 y1 z9 m15 x8 y1 z2 m14 x7 y1 z1 m15 x7 y1 z1 m15 x7 y1 z4 m15 x7 y1 z8 m15 x7 y1 z7 m15 x6 y1 z7"

tokenizer = Tokenizer()
building = tokenizer.detokenize(generated_text)

output_path = os.path.join(os.path.dirname(__file__), "..", "builder-bot", "generation.json")
with open(output_path, "w") as f:
    json.dump(building, f, indent=2)

print(json.dumps(building, indent=2))
print(f"\nTotal blocks: {len(building['blocks'])}")
print(f"Dimensions: {building['dimensions']}")
print(f"\nSaved to {output_path}")

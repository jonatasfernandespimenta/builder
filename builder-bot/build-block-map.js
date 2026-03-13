/**
 * Generates block-map.json: maps grabcraft mat_id -> minecraft block name.
 * Run once: node build-block-map.js
 *
 * Uses fuzzy name matching between grabcraft names and minecraft-data block names.
 */

const fs = require("fs");
const mcData = require("minecraft-data")("1.21.1");
const grabcraftBlocks = require("./grabcraft-blocks.json");

// Build lookup from minecraft-data
const mcBlocks = mcData.blocksArray;

function normalize(name) {
  return name
    .toLowerCase()
    .replace(/[_\-()]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// Create multiple lookup strategies
const exactMap = {};
const wordMap = {};

for (const block of mcBlocks) {
  const display = normalize(block.displayName || "");
  const id = normalize(block.name || "");
  exactMap[display] = block.name;
  exactMap[id] = block.name;

  // Also index by key words
  for (const word of display.split(" ")) {
    if (word.length > 2) {
      if (!wordMap[word]) wordMap[word] = [];
      wordMap[word].push(block);
    }
  }
}

// Common name translations from grabcraft -> minecraft
const manualOverrides = {
  "Oak Wood Plank": "oak_planks",
  "Spruce Wood Plank": "spruce_planks",
  "Birch Wood Plank": "birch_planks",
  "Jungle Wood Plank": "jungle_planks",
  "Acacia Wood Plank": "acacia_planks",
  "Dark Oak Wood Plank": "dark_oak_planks",
  "Oak Wood": "oak_log",
  "Spruce Wood": "spruce_log",
  "Birch Wood": "birch_log",
  "Jungle Wood": "jungle_log",
  "Acacia Wood": "acacia_log",
  "Dark Oak Wood": "dark_oak_log",
  "Oak Leaves": "oak_leaves",
  "Spruce Leaves": "spruce_leaves",
  "Birch Leaves": "birch_leaves",
  "Jungle Leaves": "jungle_leaves",
  "Oak Wood Stair": "oak_stairs",
  "Spruce Wood Stair": "spruce_stairs",
  "Birch Wood Stair": "birch_stairs",
  "Jungle Wood Stair": "jungle_stairs",
  "Acacia Wood Stair": "acacia_stairs",
  "Dark Oak Wood Stair": "dark_oak_stairs",
  "Stone Brick Stairs": "stone_brick_stairs",
  "Cobblestone Stairs": "cobblestone_stairs",
  "Sandstone Stairs": "sandstone_stairs",
  "Nether Brick Stairs": "nether_brick_stairs",
  "Quartz Stairs": "quartz_stairs",
  "Oak Fence": "oak_fence",
  "Spruce Fence": "spruce_fence",
  "Birch Fence": "birch_fence",
  "Jungle Fence": "jungle_fence",
  "Acacia Fence": "acacia_fence",
  "Dark Oak Fence": "dark_oak_fence",
  "Nether Brick Fence": "nether_brick_fence",
  "Oak Door": "oak_door",
  "Spruce Door": "spruce_door",
  "Birch Door": "birch_door",
  "Jungle Door": "jungle_door",
  "Acacia Door": "acacia_door",
  "Dark Oak Door": "dark_oak_door",
  "Iron Door": "iron_door",
  "Wooden Trapdoor": "oak_trapdoor",
  "Iron Trapdoor": "iron_trapdoor",
  "Glass Pane": "glass_pane",
  "Cobblestone Wall": "cobblestone_wall",
  "Mossy Cobblestone Wall": "mossy_cobblestone_wall",
  "Stone Brick": "stone_bricks",
  "Mossy Stone Brick": "mossy_stone_bricks",
  "Cracked Stone Brick": "cracked_stone_bricks",
  "Stone Slab": "stone_slab",
  "Oak Wood Slab": "oak_slab",
  "Spruce Wood Slab": "spruce_slab",
  "Birch Wood Slab": "birch_slab",
  "Jungle Wood Slab": "jungle_slab",
  "Acacia Wood Slab": "acacia_slab",
  "Dark Oak Wood Slab": "dark_oak_slab",
  "Cobblestone Slab": "cobblestone_slab",
  "Stone Brick Slab": "stone_brick_slab",
  "Sandstone Slab": "sandstone_slab",
  "Nether Brick Slab": "nether_brick_slab",
  "Quartz Slab": "quartz_slab",
  "Torch": "torch",
  "Glowstone": "glowstone",
  "White Wool": "white_wool",
  "Orange Wool": "orange_wool",
  "Magenta Wool": "magenta_wool",
  "Light Blue Wool": "light_blue_wool",
  "Yellow Wool": "yellow_wool",
  "Lime Wool": "lime_wool",
  "Pink Wool": "pink_wool",
  "Gray Wool": "gray_wool",
  "Light Gray Wool": "light_gray_wool",
  "Cyan Wool": "cyan_wool",
  "Purple Wool": "purple_wool",
  "Blue Wool": "blue_wool",
  "Brown Wool": "brown_wool",
  "Green Wool": "green_wool",
  "Red Wool": "red_wool",
  "Black Wool": "black_wool",
  "White Stained Glass": "white_stained_glass",
  "White Stained Glass Pane": "white_stained_glass_pane",
  "Grass": "grass_block",
  "Polished Granite": "polished_granite",
  "Polished Andesite": "polished_andesite",
  "Polished Diorite": "polished_diorite",
  "Crafting Table": "crafting_table",
  "Furnace": "furnace",
  "Bookshelf": "bookshelf",
  "Hay Block": "hay_block",
  "Redstone Lamp": "redstone_lamp",
  "Flower Pot": "flower_pot",
  "Anvil": "anvil",
  "Brewing Stand": "brewing_stand",
  "Cauldron": "cauldron",
  "Enchanting Table": "enchanting_table",
  "Iron Bars": "iron_bars",
  "Ladder": "ladder",
  "Lever": "lever",
  "Snow Layer": "snow",
  "Ice": "ice",
  "Packed Ice": "packed_ice",
  "Clay": "clay",
  "Hardened Clay": "terracotta",
  "White Hardened Clay": "white_terracotta",
  "Smooth Sandstone": "smooth_sandstone",
  "Red Sandstone": "red_sandstone",
  "Chiseled Sandstone": "chiseled_sandstone",
  "Chiseled Red Sandstone": "chiseled_red_sandstone",
  "Stone Button": "stone_button",
  "Wooden Button": "oak_button",
  "Stone Pressure Plate": "stone_pressure_plate",
  "Wooden Pressure Plate": "oak_pressure_plate",
  "Chest": "chest",
  "Trapped Chest": "trapped_chest",
  "Ender Chest": "ender_chest",
  "Bed": "red_bed",
  "Mossy Cobblestone": "mossy_cobblestone",
  "Obsidian": "obsidian",
  "End Stone": "end_stone",
  "End Stone Brick": "end_stone_bricks",
  "Purpur Block": "purpur_block",
  "Purpur Pillar": "purpur_pillar",
  "Purpur Stairs": "purpur_stairs",
  "Purpur Slab": "purpur_slab",
  "Prismarine": "prismarine",
  "Dark Prismarine": "dark_prismarine",
  "Sea Lantern": "sea_lantern",
  "Nether Brick": "nether_bricks",
  "Red Nether Brick": "red_nether_bricks",
  "Quartz Block": "quartz_block",
  "Chiseled Quartz Block": "chiseled_quartz_block",
  "Pillar Quartz Block": "quartz_pillar",
};

function fuzzyMatch(grabcraftName) {
  // 0. Strip parenthesized state info: "Oak Door (Facing West, Closed)" -> "Oak Door"
  const baseName = grabcraftName.replace(/\s*\(.*\)\s*$/, "").trim();

  // 1. Manual override (try both original and stripped)
  if (manualOverrides[grabcraftName]) return manualOverrides[grabcraftName];
  if (manualOverrides[baseName]) return manualOverrides[baseName];

  const norm = normalize(baseName);

  // 2. Exact match on display name or ID
  if (exactMap[norm]) return exactMap[norm];

  // 3. Try converting to minecraft-style ID
  const asId = baseName.toLowerCase().replace(/\s+/g, "_");
  if (exactMap[asId]) return exactMap[asId];

  // 4. Try removing common suffixes/prefixes
  const cleaned = norm
    .replace(/\b(block|tile)\b/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (exactMap[cleaned]) return exactMap[cleaned];

  // 5. Word overlap scoring
  const words = norm.split(" ").filter((w) => w.length > 2);
  let bestScore = 0;
  let bestMatch = null;

  for (const block of mcBlocks) {
    const blockNorm = normalize(block.displayName || "");
    const blockWords = blockNorm.split(" ");
    const overlap = words.filter((w) => blockWords.includes(w)).length;
    const score = overlap / Math.max(words.length, blockWords.length);
    if (score > bestScore && score >= 0.5) {
      bestScore = score;
      bestMatch = block.name;
    }
  }

  return bestMatch;
}

// Build the map
const blockMap = {};
let matched = 0;
let unmatched = 0;
const unmatchedNames = [];

for (const [matId, grabcraftName] of Object.entries(grabcraftBlocks)) {
  const mcName = fuzzyMatch(grabcraftName);
  if (mcName) {
    blockMap[matId] = mcName;
    matched++;
  } else {
    blockMap[matId] = "stone"; // fallback
    unmatchedNames.push(grabcraftName);
    unmatched++;
  }
}

fs.writeFileSync("block-map.json", JSON.stringify(blockMap, null, 2));
console.log(`Matched: ${matched}/${matched + unmatched}`);
console.log(`Unmatched (defaulting to stone): ${unmatched}`);
if (unmatchedNames.length) {
  console.log("\nUnmatched names:");
  unmatchedNames.slice(0, 30).forEach((n) => console.log(`  - ${n}`));
  if (unmatchedNames.length > 30) {
    console.log(`  ... and ${unmatchedNames.length - 30} more`);
  }
}

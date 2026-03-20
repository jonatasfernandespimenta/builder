class Tokenizer:
    # Maps name substrings/suffixes to cluster names.
    # Order matters: first match wins, so more specific patterns come first.
    MATERIAL_CLUSTERS = {
        "oak_planks": "m_planks", "spruce_planks": "m_planks",
        "birch_planks": "m_planks", "jungle_planks": "m_planks",
        "acacia_planks": "m_planks", "dark_oak_planks": "m_planks",
        "crimson_planks": "m_planks", "warped_planks": "m_planks",
        "mangrove_planks": "m_planks", "cherry_planks": "m_planks",
        "bamboo_planks": "m_planks", "planks": "m_planks",

        "oak_log": "m_log", "spruce_log": "m_log", "birch_log": "m_log",
        "jungle_log": "m_log", "acacia_log": "m_log", "dark_oak_log": "m_log",
        "crimson_stem": "m_log", "warped_stem": "m_log",
        "mangrove_log": "m_log", "cherry_log": "m_log",
        "stripped_oak_log": "m_log", "stripped_spruce_log": "m_log",
        "stripped_birch_log": "m_log", "stripped_jungle_log": "m_log",
        "stripped_acacia_log": "m_log", "stripped_dark_oak_log": "m_log",
        "log": "m_log", "stem": "m_log", "wood": "m_log",

        "oak_stairs": "m_stairs", "spruce_stairs": "m_stairs",
        "birch_stairs": "m_stairs", "stone_stairs": "m_stairs",
        "brick_stairs": "m_stairs", "cobblestone_stairs": "m_stairs",
        "nether_brick_stairs": "m_stairs", "sandstone_stairs": "m_stairs",
        "quartz_stairs": "m_stairs", "stairs": "m_stairs",

        "oak_slab": "m_slab", "spruce_slab": "m_slab",
        "birch_slab": "m_slab", "stone_slab": "m_slab",
        "brick_slab": "m_slab", "cobblestone_slab": "m_slab",
        "sandstone_slab": "m_slab", "quartz_slab": "m_slab",
        "slab": "m_slab",

        "oak_fence": "m_fence", "spruce_fence": "m_fence",
        "birch_fence": "m_fence", "nether_brick_fence": "m_fence",
        "fence_gate": "m_fence_gate", "fence": "m_fence",

        "oak_door": "m_door", "spruce_door": "m_door",
        "birch_door": "m_door", "iron_door": "m_door",
        "door": "m_door",

        "oak_trapdoor": "m_trapdoor", "spruce_trapdoor": "m_trapdoor",
        "birch_trapdoor": "m_trapdoor", "iron_trapdoor": "m_trapdoor",
        "trapdoor": "m_trapdoor",

        "oak_button": "m_button", "stone_button": "m_button",
        "button": "m_button",

        "oak_pressure_plate": "m_pressure_plate",
        "stone_pressure_plate": "m_pressure_plate",
        "pressure_plate": "m_pressure_plate",

        "oak_sign": "m_sign", "spruce_sign": "m_sign",
        "wall_sign": "m_sign", "sign": "m_sign",

        "oak_leaves": "m_leaves", "spruce_leaves": "m_leaves",
        "birch_leaves": "m_leaves", "jungle_leaves": "m_leaves",
        "acacia_leaves": "m_leaves", "dark_oak_leaves": "m_leaves",
        "leaves": "m_leaves",

        "white_wool": "m_wool", "orange_wool": "m_wool",
        "magenta_wool": "m_wool", "light_blue_wool": "m_wool",
        "yellow_wool": "m_wool", "lime_wool": "m_wool",
        "pink_wool": "m_wool", "gray_wool": "m_wool",
        "cyan_wool": "m_wool", "purple_wool": "m_wool",
        "blue_wool": "m_wool", "brown_wool": "m_wool",
        "green_wool": "m_wool", "red_wool": "m_wool",
        "black_wool": "m_wool", "wool": "m_wool",

        "white_carpet": "m_carpet", "carpet": "m_carpet",

        "white_concrete": "m_concrete", "concrete_powder": "m_concrete_powder",
        "concrete": "m_concrete",

        "white_terracotta": "m_terracotta", "glazed_terracotta": "m_terracotta",
        "terracotta": "m_terracotta",

        "stained_glass_pane": "m_glass_pane", "glass_pane": "m_glass_pane",
        "stained_glass": "m_glass", "tinted_glass": "m_glass", "glass": "m_glass",

        "stone_bricks": "m_stone_bricks", "mossy_stone_bricks": "m_stone_bricks",
        "cracked_stone_bricks": "m_stone_bricks", "chiseled_stone_bricks": "m_stone_bricks",
        "stone_brick": "m_stone_bricks",

        "smooth_stone": "m_stone", "stone": "m_stone",
        "cobblestone": "m_cobblestone", "mossy_cobblestone": "m_cobblestone",

        "deepslate": "m_deepslate",
        "granite": "m_granite", "polished_granite": "m_granite",
        "diorite": "m_diorite", "polished_diorite": "m_diorite",
        "andesite": "m_andesite", "polished_andesite": "m_andesite",

        "sandstone": "m_sandstone", "red_sandstone": "m_sandstone",
        "smooth_sandstone": "m_sandstone", "chiseled_sandstone": "m_sandstone",
        "cut_sandstone": "m_sandstone",

        "bricks": "m_bricks", "brick": "m_bricks",
        "nether_bricks": "m_nether_bricks", "nether_brick": "m_nether_bricks",
        "quartz_block": "m_quartz", "quartz_pillar": "m_quartz",
        "smooth_quartz": "m_quartz", "chiseled_quartz": "m_quartz",
        "quartz": "m_quartz",

        "prismarine": "m_prismarine",
        "purpur": "m_purpur",
        "end_stone": "m_end_stone",
        "obsidian": "m_obsidian",
        "netherrack": "m_netherrack",
        "basalt": "m_basalt", "blackstone": "m_blackstone",

        "iron_block": "m_metal_block", "gold_block": "m_metal_block",
        "diamond_block": "m_metal_block", "emerald_block": "m_metal_block",
        "lapis_block": "m_metal_block", "copper_block": "m_metal_block",
        "netherite_block": "m_metal_block",

        "iron_bars": "m_iron_bars",
        "chain": "m_chain",
        "lantern": "m_lantern", "soul_lantern": "m_lantern",
        "torch": "m_torch", "wall_torch": "m_torch",
        "soul_torch": "m_torch", "redstone_torch": "m_torch",

        "white_bed": "m_bed", "bed": "m_bed",
        "chest": "m_chest", "barrel": "m_chest",
        "furnace": "m_furnace", "blast_furnace": "m_furnace", "smoker": "m_furnace",
        "crafting_table": "m_workstation", "smithing_table": "m_workstation",
        "cartography_table": "m_workstation", "fletching_table": "m_workstation",
        "loom": "m_workstation", "stonecutter": "m_workstation",
        "grindstone": "m_workstation", "anvil": "m_workstation",
        "enchanting_table": "m_workstation", "brewing_stand": "m_workstation",
        "lectern": "m_workstation",

        "campfire": "m_campfire", "soul_campfire": "m_campfire",
        "ladder": "m_ladder",
        "scaffolding": "m_scaffolding",
        "rail": "m_rail", "powered_rail": "m_rail", "detector_rail": "m_rail",
        "activator_rail": "m_rail",

        "white_banner": "m_banner", "banner": "m_banner",
        "flower_pot": "m_flower_pot",
        "item_frame": "m_item_frame",
        "armor_stand": "m_armor_stand",
        "painting": "m_painting",

        "water": "m_water", "lava": "m_lava",
        "air": "m_air",
        "dirt": "m_dirt", "coarse_dirt": "m_dirt", "rooted_dirt": "m_dirt",
        "grass_block": "m_grass", "podzol": "m_grass", "mycelium": "m_grass",
        "sand": "m_sand", "red_sand": "m_sand", "gravel": "m_gravel",
        "clay": "m_clay",
        "snow": "m_snow", "snow_block": "m_snow", "ice": "m_ice",
        "packed_ice": "m_ice", "blue_ice": "m_ice",

        "oak_wall": "m_wall", "cobblestone_wall": "m_wall",
        "brick_wall": "m_wall", "wall": "m_wall",

        "redstone_wire": "m_redstone", "redstone_block": "m_redstone",
        "redstone_lamp": "m_redstone", "repeater": "m_redstone",
        "comparator": "m_redstone", "piston": "m_redstone",
        "sticky_piston": "m_redstone", "observer": "m_redstone",
        "dispenser": "m_redstone", "dropper": "m_redstone",
        "hopper": "m_redstone", "redstone": "m_redstone",

        "tnt": "m_tnt",
        "bookshelf": "m_bookshelf",
        "hay_block": "m_hay",
        "melon": "m_crop", "pumpkin": "m_crop", "carved_pumpkin": "m_crop",
        "jack_o_lantern": "m_crop", "wheat": "m_crop",
        "cactus": "m_plant", "bamboo": "m_plant", "sugar_cane": "m_plant",
        "vine": "m_plant", "lily_pad": "m_plant",
        "flower": "m_flower", "dandelion": "m_flower", "poppy": "m_flower",
        "rose": "m_flower", "tulip": "m_flower", "orchid": "m_flower",
        "allium": "m_flower", "cornflower": "m_flower", "sunflower": "m_flower",

        "glowstone": "m_light", "sea_lantern": "m_light",
        "shroomlight": "m_light", "end_rod": "m_light",

        "spawner": "m_spawner",
        "bell": "m_bell",
        "cauldron": "m_cauldron",
        "composter": "m_composter",
        "beehive": "m_beehive", "bee_nest": "m_beehive",
    }

    # Suffix-based fallback patterns: (suffix, cluster_name)
    _SUFFIX_PATTERNS = [
        ("_planks", "m_planks"), ("_log", "m_log"), ("_wood", "m_log"),
        ("_stem", "m_log"), ("_stairs", "m_stairs"), ("_slab", "m_slab"),
        ("_fence_gate", "m_fence_gate"), ("_fence", "m_fence"),
        ("_door", "m_door"), ("_trapdoor", "m_trapdoor"),
        ("_button", "m_button"), ("_pressure_plate", "m_pressure_plate"),
        ("_sign", "m_sign"), ("_leaves", "m_leaves"),
        ("_wool", "m_wool"), ("_carpet", "m_carpet"),
        ("_concrete_powder", "m_concrete_powder"), ("_concrete", "m_concrete"),
        ("_terracotta", "m_terracotta"),
        ("_glass_pane", "m_glass_pane"), ("_glass", "m_glass"),
        ("_wall", "m_wall"), ("_banner", "m_banner"),
        ("_bed", "m_bed"), ("_candle", "m_candle"),
        ("_coral", "m_coral"), ("_ore", "m_ore"),
    ]

    def __init__(self):
        # Maps raw mat_id (str) -> cluster name (str, e.g. "m_planks")
        self.material_map: dict[str, str] = {}

    def sanitize(self, value: str) -> str:
        return value.strip().replace(" ", "_")

    # ------------------------------------------------------------------
    # Material clustering
    # ------------------------------------------------------------------

    def _name_to_cluster(self, name: str) -> str:
        """Resolve a Minecraft block name to a cluster label."""
        name = name.lower().strip().replace(" ", "_").replace("minecraft:", "")

        # Exact / substring lookup in the static map
        if name in self.MATERIAL_CLUSTERS:
            return self.MATERIAL_CLUSTERS[name]

        # Suffix-based fallback
        for suffix, cluster in self._SUFFIX_PATTERNS:
            if name.endswith(suffix):
                return cluster

        # Last-resort: use the full name prefixed with m_
        return f"m_{name}"

    def build_material_map(self, dataset: list) -> None:
        """Scan *dataset* (list of construction dicts) and populate
        ``self.material_map`` by mapping each unique mat_id to a cluster
        name derived from the block's ``name`` field (if present)."""
        for construction in dataset:
            for block in construction.get("blocks", []):
                mat_id = str(block.get("mat_id", "0"))
                if mat_id in self.material_map:
                    continue  # already resolved

                block_name = block.get("name", "")
                if block_name:
                    self.material_map[mat_id] = self._name_to_cluster(block_name)
                # If no name field, leave unmapped (cluster_material will
                # return m_unknown at query time).

    def cluster_material(self, block: dict) -> str:
        """Return the cluster token for *block*.

        Resolution order:
        1. ``self.material_map`` (populated by ``build_material_map``).
        2. The block's own ``name`` field (resolved on-the-fly).
        3. ``m_unknown`` as a fallback.
        """
        mat_id = str(block.get("mat_id", "0"))

        # Fast path: already in the map
        if mat_id in self.material_map:
            return self.material_map[mat_id]

        # Try to resolve from the block's name right now
        block_name = block.get("name", "")
        if block_name:
            cluster = self._name_to_cluster(block_name)
            self.material_map[mat_id] = cluster  # cache for next time
            return cluster

        return "m_unknown"

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
            tokens.append(self.cluster_material(block))
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
            elif t.startswith("m_") and i + 3 < len(tokens):
                try:
                    mat_cluster = t  # e.g. "m_planks", "m_unknown"
                    x = int(tokens[i + 1][1:])
                    y = int(tokens[i + 2][1:])
                    z = int(tokens[i + 3][1:])
                    building["blocks"].append(
                        {"mat_id": mat_cluster, "x": x, "y": y, "z": z}
                    )
                    i += 4
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1

        return building

    def tokenize_dataset(self, data: list[dict]) -> list[str]:
        return [self.tokenize_construction(item) for item in data]

const vec3 = require("vec3");
const fs = require("fs");
const path = require("path");

const blockMapPath = path.join(__dirname, "block-map.json");
const blockMap = fs.existsSync(blockMapPath) ? require(blockMapPath) : {};

class BuildQueue {
  constructor(bot) {
    this.bot = bot;
    this.queue = [];
    this.placedPositions = [];
    this.placed = 0;
    this.active = false;
    this.cancelled = false;
    this.undoing = false;
  }

  start(blocks, onDone) {
    this.queue = blocks;
    this.placedPositions = [];
    this.placed = 0;
    this.active = true;
    this.cancelled = false;
    this._processQueue(onDone);
  }

  stop() {
    this.cancelled = true;
    this.active = false;
  }

  getProgress() {
    if (!this.active) return { active: false };
    const total = this.queue.length;
    return {
      active: true,
      placed: this.placed,
      total,
      percent: Math.round((this.placed / total) * 100),
    };
  }

  async _processQueue(onDone) {
    for (let i = 0; i < this.queue.length; i++) {
      if (this.cancelled) return;

      const { position, mat_id } = this.queue[i];

      // Resolve grabcraft mat_id -> minecraft block name via block-map.json
      const mcBlockName = blockMap[mat_id];
      if (!mcBlockName) {
        this.placed++;
        continue;
      }

      try {
        await this._placeBlock(position, mcBlockName);
        this.placedPositions.push(position);
      } catch (err) {
        console.error(
          `Failed to place ${mcBlockName} at ${position}: ${err.message}`
        );
      }

      this.placed++;

      // Progress update every 50 blocks
      if (this.placed % 50 === 0) {
        const pct = Math.round((this.placed / this.queue.length) * 100);
        this.bot.chat(`Progress: ${this.placed}/${this.queue.length} (${pct}%)`);
      }

      // Small delay to avoid server throttling
      await this._sleep(50);
    }

    this.active = false;
    if (!this.cancelled && onDone) onDone();
  }

  async _placeBlock(position, mcBlockName) {
    // Use /setblock command (requires OP or creative mode)
    const { x, y, z } = position;
    this.bot.chat(`/setblock ${Math.floor(x)} ${Math.floor(y)} ${Math.floor(z)} minecraft:${mcBlockName}`);
    await this._sleep(50);
  }

  async undo(onDone) {
    if (this.placedPositions.length === 0) return false;
    if (this.undoing) return false;

    this.stop();
    this.undoing = true;
    const total = this.placedPositions.length;

    for (let i = 0; i < this.placedPositions.length; i++) {
      if (!this.undoing) return;
      const { x, y, z } = this.placedPositions[i];
      this.bot.chat(`/setblock ${Math.floor(x)} ${Math.floor(y)} ${Math.floor(z)} minecraft:air`);
      await this._sleep(50);

      if ((i + 1) % 50 === 0) {
        const pct = Math.round(((i + 1) / total) * 100);
        this.bot.chat(`Undo progress: ${i + 1}/${total} (${pct}%)`);
      }
    }

    const cleared = this.placedPositions.length;
    this.placedPositions = [];
    this.undoing = false;
    if (onDone) onDone(cleared);
    return true;
  }

  _sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

module.exports = BuildQueue;

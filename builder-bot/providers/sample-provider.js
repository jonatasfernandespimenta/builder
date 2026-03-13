const fs = require("fs");
const path = require("path");

const DATA_PATH = path.join(__dirname, "..", "..", "builderai", "data.json");

class SampleProvider {
  constructor() {
    this.buildings = JSON.parse(fs.readFileSync(DATA_PATH, "utf8"));
    this.index = this._buildIndex();
  }

  _buildIndex() {
    // Index buildings by keywords from their name
    const index = {};
    for (const b of this.buildings) {
      const words = b.name.toLowerCase().split(/\s+/);
      for (const word of words) {
        if (!index[word]) index[word] = [];
        index[word].push(b);
      }
    }
    return index;
  }

  async listStyles() {
    // Extract common keywords from building names
    const counts = {};
    for (const b of this.buildings) {
      const words = b.name.toLowerCase().split(/\s+/);
      for (const word of words) {
        if (word.length > 3) {
          counts[word] = (counts[word] || 0) + 1;
        }
      }
    }
    return Object.entries(counts)
      .filter(([, c]) => c >= 3)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15)
      .map(([word, count]) => `${word}(${count})`);
  }

  async generate(style) {
    if (style === "random") {
      const pick = this.buildings[Math.floor(Math.random() * this.buildings.length)];
      return pick;
    }

    // Search by keyword matching
    const keywords = style.toLowerCase().split(/\s+/);
    let matches = [];

    for (const building of this.buildings) {
      const name = building.name.toLowerCase();
      const score = keywords.filter((kw) => name.includes(kw)).length;
      if (score > 0) {
        matches.push({ building, score });
      }
    }

    if (matches.length === 0) {
      // Fallback to random
      const pick = this.buildings[Math.floor(Math.random() * this.buildings.length)];
      return pick;
    }

    // Pick best match, random among ties
    matches.sort((a, b) => b.score - a.score);
    const best = matches.filter((m) => m.score === matches[0].score);
    return best[Math.floor(Math.random() * best.length)].building;
  }
}

module.exports = SampleProvider;

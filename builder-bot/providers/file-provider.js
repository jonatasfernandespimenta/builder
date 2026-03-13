const fs = require("fs");
const path = require("path");

class FileProvider {
  constructor(filePath) {
    this.filePath = path.resolve(filePath);
    this.building = JSON.parse(fs.readFileSync(this.filePath, "utf8"));
    console.log(
      `Loaded building from ${this.filePath}: "${this.building.name}" (${this.building.blocks.length} blocks)`
    );
  }

  async listStyles() {
    return [this.building.name || "from-file"];
  }

  async generate(_style) {
    return this.building;
  }
}

module.exports = FileProvider;

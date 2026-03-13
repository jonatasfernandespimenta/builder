const http = require("http");

class AIProvider {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
  }

  async listStyles() {
    try {
      const data = await this._get("/styles");
      return data;
    } catch {
      return ["house", "tower", "castle", "medieval", "fantasy", "modern", "church", "bridge", "wall", "hut"];
    }
  }

  async generate(style) {
    const body = JSON.stringify({ style, max_tokens: 4096, temperature: 0.5 });
    const data = await this._post("/generate", body);
    return data;
  }

  /**
   * Stream blocks from the AI server. Calls onBlock(block) for each block
   * as it's generated, and onDone() when generation finishes.
   */
  streamGenerate(style, onBlock, onDone) {
    const body = JSON.stringify({ style, max_tokens: 4096, temperature: 0.8 });
    const url = new URL("/generate/stream", this.serverUrl);
    const options = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(body),
      },
    };

    const req = http.request(url, options, (res) => {
      let buffer = "";
      res.on("data", (chunk) => {
        buffer += chunk;
        const lines = buffer.split("\n");
        // Keep the last incomplete line in the buffer
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const block = JSON.parse(line);
            onBlock(block);
          } catch (e) {
            // skip malformed lines
          }
        }
      });
      res.on("end", () => {
        // Process any remaining data
        if (buffer.trim()) {
          try {
            onBlock(JSON.parse(buffer));
          } catch (e) {}
        }
        onDone();
      });
    });

    req.on("error", (e) => {
      console.error(`AI stream error: ${e.message}`);
      onDone();
    });

    req.write(body);
    req.end();
  }

  _request(method, path, body) {
    return new Promise((resolve, reject) => {
      const url = new URL(path, this.serverUrl);
      const options = { method, headers: {} };
      if (body) {
        options.headers["Content-Type"] = "application/json";
        options.headers["Content-Length"] = Buffer.byteLength(body);
      }
      const req = http.request(url, options, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error(`Invalid response from AI server: ${data.slice(0, 200)}`));
          }
        });
      });
      req.on("error", (e) =>
        reject(new Error(`AI server unreachable at ${this.serverUrl}: ${e.message}`))
      );
      if (body) req.write(body);
      req.end();
    });
  }

  _get(path) {
    return this._request("GET", path);
  }

  _post(path, body) {
    return this._request("POST", path, body);
  }
}

module.exports = AIProvider;

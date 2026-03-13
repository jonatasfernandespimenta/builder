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
    const body = JSON.stringify({ style, max_tokens: 4096, temperature: 0.8 });
    const data = await this._post("/generate", body);
    return data;
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

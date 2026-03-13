const mineflayer = require("mineflayer");
const { pathfinder, Movements, goals } = require("mineflayer-pathfinder");
const vec3 = require("vec3");
const fs = require("fs");
const path = require("path");
const config = require("./config.json");
const BuildQueue = require("./build-queue");
const SampleProvider = require("./providers/sample-provider");
const AIProvider = require("./providers/ai-provider");
const FileProvider = require("./providers/file-provider");

// Load grabcraft mat_id -> minecraft block name mapping
const blockMapPath = path.join(__dirname, "block-map.json");
const blockMap = fs.existsSync(blockMapPath) ? require(blockMapPath) : {};
const grabcraftNames = fs.existsSync(path.join(__dirname, "grabcraft-blocks.json"))
  ? require("./grabcraft-blocks.json")
  : {};

const bot = mineflayer.createBot({
  host: config.host,
  port: config.port,
  username: config.username,
  version: config.version,
});

bot.loadPlugin(pathfinder);

const fileArgIdx = process.argv.indexOf("--file");
const provider = fileArgIdx !== -1
  ? new FileProvider(process.argv[fileArgIdx + 1])
  : process.argv.includes("--ai")
    ? new AIProvider(config.aiServerUrl)
    : new SampleProvider();

const buildQueue = new BuildQueue(bot);

// Track pending build sessions per player
const sessions = {};

// Catch uncaught errors so the bot doesn't crash
process.on("uncaughtException", (err) => {
  console.error("Uncaught:", err.message);
});

bot.once("spawn", () => {
  console.log(`Bot spawned at ${bot.entity.position}`);

  // Delay first chat to let the server settle
  setTimeout(() => {
    bot.chat("BuilderBot online! Use: !build <style> | !list | !help");
  }, 2000);
});

// Use messagestr instead of chat — more resilient to chat format changes
bot.on("messagestr", async (message, messagePosition, jsonMsg) => {
  // messagestr gives the full line like "<player> message" or system messages
  // Parse out the username and message from the <username> format
  const match = message.match(/^<(\w+)>\s+(.+)$/);
  if (!match) return;

  const username = match[1];
  if (username === bot.username) return;

  const text = match[2];
  const args = text.trim().split(/\s+/);
  const cmd = args[0].toLowerCase();

  try {
    switch (cmd) {
      case "!help":
        handleHelp();
        break;
      case "!list":
        await handleList();
        break;
      case "!build":
        await handleBuild(username, args.slice(1));
        break;
      case "!pos":
        handlePos(username, args.slice(1));
        break;
      case "!cancel":
        handleCancel(username);
        break;
      case "!undo":
        await handleUndo(username);
        break;
      case "!status":
        handleStatus();
        break;
    }
  } catch (err) {
    console.error(err);
    bot.chat(`Error: ${err.message}`);
  }
});

function handleHelp() {
  bot.chat("--- BuilderBot Commands ---");
  bot.chat("!build <style> - Generate a building (e.g. !build medieval)");
  bot.chat("!list - Show available building styles");
  bot.chat("!pos <x> <y> <z> - Set build position and start building");
  bot.chat("!cancel - Cancel current build");
  bot.chat("!undo - Clear the last build");
  bot.chat("!status - Show build progress");
}

async function handleList() {
  const styles = await provider.listStyles();
  bot.chat(`Available styles: ${styles.join(", ")}`);
}

async function handleBuild(username, args) {
  if (sessions[username]?.active) {
    bot.chat(`${username}, you already have an active build. Use !cancel first.`);
    return;
  }

  const style = args.join(" ") || "random";
  bot.chat(`Generating "${style}" building...`);

  const building = await provider.generate(style);
  if (!building || !building.blocks.length) {
    bot.chat("Failed to generate a building. Try a different style.");
    return;
  }

  sessions[username] = { building };

  bot.chat(`--- ${building.name} ---`);
  bot.chat(
    `Size: ${building.dimensions.width}x${building.dimensions.height}x${building.dimensions.depth} | Blocks: ${building.blocks.length}`
  );
  bot.chat(`${username}, give me a position with: !pos <x> <y> <z>`);
}

function handlePos(username, args) {
  const session = sessions[username];
  if (!session || !session.building) {
    bot.chat(`${username}, generate a building first with !build <style>`);
    return;
  }

  if (args.length < 3) {
    bot.chat("Usage: !pos <x> <y> <z>");
    return;
  }

  const [x, y, z] = args.map(Number);
  if ([x, y, z].some(isNaN)) {
    bot.chat("Invalid coordinates. Use numbers: !pos 100 64 200");
    return;
  }

  const building = session.building;
  session.active = true;

  bot.chat(`Building "${building.name || "structure"}" at ${x} ${y} ${z}...`);

  // Sort blocks bottom-to-top (by Y) for stable placement
  const sorted = [...building.blocks].sort((a, b) => {
    if (a.y !== b.y) return a.y - b.y;
    if (a.x !== b.x) return a.x - b.x;
    return a.z - b.z;
  });

  // Normalize positions (start from 0,0,0) then offset by origin
  const minX = Math.min(...sorted.map((b) => b.x));
  const minY = Math.min(...sorted.map((b) => b.y));
  const minZ = Math.min(...sorted.map((b) => b.z));

  const placed = sorted.map((block) => ({
    position: vec3(block.x - minX + x, block.y - minY + y, block.z - minZ + z),
    mat_id: block.mat_id,
  }));

  buildQueue.start(placed, () => {
    bot.chat(`Done! Placed ${placed.length} blocks.`);
    delete sessions[username];
  });
}

function handleCancel(username) {
  if (sessions[username]) {
    buildQueue.stop();
    delete sessions[username];
    bot.chat(`${username}'s build cancelled.`);
  } else {
    bot.chat(`${username}, nothing to cancel.`);
  }
}

async function handleUndo(username) {
  bot.chat("Undoing last build...");
  const ok = await buildQueue.undo((cleared) => {
    bot.chat(`Done! Cleared ${cleared} blocks.`);
    delete sessions[username];
  });
  if (!ok) {
    bot.chat("Nothing to undo.");
  }
}

function handleStatus() {
  const progress = buildQueue.getProgress();
  if (!progress.active) {
    bot.chat("No active build.");
  } else {
    bot.chat(
      `Building: ${progress.placed}/${progress.total} blocks (${progress.percent}%)`
    );
  }
}

function resolveBlockName(matId) {
  // Use grabcraft name mapping (more readable for chat)
  if (grabcraftNames[matId]) return grabcraftNames[matId];
  // Fallback to block-map minecraft name
  if (blockMap[matId]) return blockMap[matId];
  return `block_${matId}`;
}

bot.on("error", (err) => console.error("Bot error:", err));
bot.on("kicked", (reason) => console.log("Kicked:", reason));
bot.on("end", () => console.log("Disconnected."));

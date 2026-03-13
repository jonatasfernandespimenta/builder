# BuilderBot - AI-Powered Minecraft Building Bot

A Minecraft bot that uses a custom-trained transformer neural network to generate and build structures autonomously. Tell it what to build, give it coordinates, and watch it go.

## How It Works

```
Player types "!build medieval" in Minecraft chat
        |
        v
  Mineflayer Bot (Node.js) -----> AI Server (Python/TensorFlow)
        |                              |
        |                   Transformer generates building
        |                   as a sequence of block tokens
        |                              |
        |    <--- building JSON -------+
        |
  Bot shows materials list in chat
  Player gives coordinates: "!pos 100 -60 200"
        |
        v
  Bot places blocks using /setblock commands
        |
        v
  Building appears in Minecraft
```

## Project Structure

```
builder/
├── builderai/               # AI model (Python/TensorFlow)
│   ├── main.py              # Training pipeline
│   ├── server.py            # HTTP server for the bot to call
│   ├── Transformer.py       # Transformer block with causal attention
│   ├── TokenAndPositionEmbedding.py
│   ├── BuildingGenerator.py # Text generation with temperature sampling
│   ├── Tokenizer.py         # Building <-> token sequence conversion
│   ├── prepare_data.py      # Cleans raw data into training data
│   └── data.json            # Cleaned training dataset (259 buildings)
│
├── builder-bot/             # Minecraft bot (Node.js/Mineflayer)
│   ├── index.js             # Main bot - chat commands, session management
│   ├── build-queue.js       # Block placement engine using /setblock
│   ├── config.json          # Server connection settings
│   ├── block-map.json       # Grabcraft mat_id -> Minecraft block name (560 blocks)
│   └── providers/
│       ├── sample-provider.js  # Uses real buildings from dataset (default)
│       └── ai-provider.js     # Calls the AI server for generation
│
├── grabcraft-scrapper/      # Web scraper (Python/Selenium)
│   ├── main.py              # Scrapes building designs from grabcraft.com
│   └── grabcraft_data.json  # 756 scraped buildings (274 MB)
│
├── builder-webscrap/        # Data conversion utilities
│   ├── converter.js         # Nested block format -> flat format
│   └── minecraft-items.json # Minecraft block ID reference
│
└── mc-server/               # Local Minecraft server for testing
    ├── start.sh             # Launch script (Java 21+)
    └── server.properties    # Creative mode, flat world, offline
```

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- Java 21+ (for Minecraft server)
- TensorFlow (`pip3 install tensorflow`)
- Minecraft Java Edition 1.21.1

### 1. Start the Minecraft Server

```bash
cd mc-server
./start.sh
```

Wait for `Done! For help, type "help"`, then OP the bot in the server console:

```
op BuilderBot
```

### 2. Start the Bot (Sample Mode)

Sample mode uses real buildings from the scraped dataset — no trained model needed.

```bash
cd builder-bot
npm install
node index.js
```

### 3. Play

Open Minecraft 1.21.1, connect to `localhost`, and chat:

```
!help                    Show all commands
!list                    Show available building styles
!build medieval          Generate a medieval building
!build tower             Generate a tower
!build random            Pick a random building
!pos 100 -60 200         Build at these coordinates
!status                  Check build progress
!cancel                  Stop current build
```

## AI Mode

Once the model is trained, you can use AI-generated buildings instead of samples from the dataset.

### Train the Model

```bash
cd builderai
python3 prepare_data.py    # Generate cleaned data.json (only needed once)
python3 main.py            # Train - 50 epochs, saves to ./models/gpt
```

Monitor training with TensorBoard:

```bash
tensorboard --logdir=./logs
# Open http://localhost:6006
```

### Run with AI

Three terminals:

```bash
# Terminal 1: Minecraft server
cd mc-server && ./start.sh

# Terminal 2: AI server
cd builderai && python3 server.py

# Terminal 3: Bot in AI mode
cd builder-bot && node index.js --ai
```

## The AI Model

### Architecture

A GPT-style autoregressive transformer that generates buildings as token sequences.

- **Embedding**: 256-dim token + positional embeddings
- **Transformer**: 4-head attention, 512-dim feed-forward, causal masking
- **Output**: Softmax over 10,000 token vocabulary
- **Sequence length**: 4,096 tokens max

### Tokenization

Buildings are encoded as compact token sequences:

```
<start> name=medieval_house dim=12x10x12 <blocks> m29 x2 y1 z3 m206 x3 y1 z2 m907 x9 y1 z1 ... <end>
```

Each block is 4 tokens: `m{material_id} x{x} y{y} z{z}`. This compact format fits buildings up to ~1,000 blocks within the 4,096 token limit.

### Dataset

- **Source**: 756 buildings scraped from grabcraft.com
- **After filtering**: 259 buildings (removed broken entries and buildings exceeding token limit)
- **Token range**: 349 - 4,093 tokens per building
- **Block types**: 560 unique materials mapped to Minecraft blocks (95.4% match rate)

## Bot Commands Reference

| Command | Description |
|---------|-------------|
| `!help` | Show all available commands |
| `!list` | List building styles with counts |
| `!build <style>` | Generate a building by style keyword |
| `!pos <x> <y> <z>` | Set position and start building |
| `!status` | Show placement progress |
| `!cancel` | Cancel current build |

## Configuration

Edit `builder-bot/config.json`:

```json
{
  "host": "localhost",
  "port": 25565,
  "username": "BuilderBot",
  "version": "1.21.1",
  "owner": "jhonny",
  "aiServerUrl": "http://localhost:5000"
}
```

The bot requires **OP permissions** on the server since it uses `/setblock` commands to place blocks.

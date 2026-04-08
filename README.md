# Sigmoidian

A multiplayer Discord bot built with [PyCord](https://pycord.dev/) that hosts a **Word Chain** game — a collaborative challenge where each word must start with the last letter of the previous word.

## How to Play

Players take turns adding 5-letter words to a growing chain. Each word must begin with the **last letter** of the previous word:

```
SENSE → ENTER → ROVER → RANGE → EMBER → ...
```

- Words must be valid 5-letter English words
- No repeating words in the same game
- Any server member can join — just use `/chain play`
- **Scoring:** +1 pt per valid word · +2 bonus pts every 5 words in the chain

---

## Commands

### Chain Game

| Command | Description |
|---------|-------------|
| `/chain start` | Start a new chain game in this channel |
| `/chain play <word>` | Add a word to the active chain |
| `/chain status` | View the current chain and participants |
| `/chain end` | End the game and show per-player results |
| `/chain help` | Rules and scoring recap |

### Stats

| Command | Description |
|---------|-------------|
| `/stats` | Your personal chain stats (private) |
| `/leaderboard` | Server-wide points leaderboard |
| `/topwords` | Most used words in this server |
| `/dictionary` | Dictionary info and word count |

### Word Management *(admin only)*

| Command | Description |
|---------|-------------|
| `/addword <word>` | Add a missing word to the dictionary |
| `/removeword <word>` | Remove a word from the dictionary |
| `/checkword <word>` | Check if a word is accepted |

---

## Setup

### Prerequisites

- Python 3.10+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))

### 1. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. **Bot** tab → **Add Bot** → copy the token
3. Under **Privileged Gateway Intents**, no extra intents are needed
4. **OAuth2 → URL Generator**: select scopes `bot` + `applications.commands`
5. Bot permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
6. Copy the generated URL, open it, and invite the bot to your server

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your token:

```env
DISCORD_TOKEN=your_bot_token_here
PORT=8080

# Optional: instant slash command registration for one guild (testing)
DISCORD_GUILD_ID=your_guild_id_here
```

> **Tip:** Without `DISCORD_GUILD_ID`, slash commands propagate globally and may take up to 1 hour to appear. Set it to your server's ID for instant registration while testing.

### 3. Run

**macOS / Linux**

```bash
./start.sh
```

**Windows**

```bat
start.bat
```

The scripts automatically:
- Check if the configured port is in use and free it
- Create/activate a Python virtual environment
- Install dependencies from `requirements.txt`
- Start the bot

**Manual run**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

---

## Status Dashboard

While the bot is running, a lightweight status page is available at:

```
http://localhost:8080/
http://localhost:8080/health    ← JSON health check
```

The dashboard shows connection status, guild count, latency, and uptime. It auto-refreshes every 10 seconds and works even before a Discord token is configured.

---

## Dictionary

The word list lives in `data/words.txt` — one uppercase word per line, sorted alphabetically. It ships with **3,300+** valid 5-letter English words.

To add words permanently, either:
- Use `/addword <word>` in Discord (admin only) — writes to the file immediately
- Edit `data/words.txt` directly and restart the bot

---

## Project Structure

```
sigmoidian/
├── bot.py              ← entry point, web server, event handlers
├── config.py           ← environment config
├── start.sh            ← macOS/Linux launcher
├── start.bat           ← Windows launcher
├── requirements.txt
├── .env.example
├── data/
│   └── words.txt       ← 5-letter word dictionary (3,300+ words)
├── cogs/
│   ├── chain_cog.py    ← /chain commands + word admin commands
│   └── stats_cog.py    ← /stats /leaderboard /topwords /dictionary
├── game/
│   └── chain.py        ← chain game logic (validation, scoring)
└── utils/
    ├── database.py     ← async SQLite helpers (aiosqlite, WAL mode)
    ├── words.py        ← word list loader and manager
    └── display.py      ← Discord embed builders
```

---

## Tech Stack

| Library | Purpose |
|---------|---------|
| [py-cord](https://pycord.dev/) | Discord bot framework (slash commands) |
| [aiosqlite](https://aiosqlite.omnilib.dev/) | Async SQLite for game state and stats |
| [aiohttp](https://docs.aiohttp.org/) | Status dashboard web server |
| [python-dotenv](https://saurabh-kumar.com/python-dotenv/) | Environment variable loading |
| [certifi](https://pypi.org/project/certifi/) | SSL certificates (macOS fix) |

---

## License

MIT

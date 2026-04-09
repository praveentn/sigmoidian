# Sigmoidian

Sigmoidian is a multiplayer Discord word-chain bot where players collaborate to build chains of 5-letter words. Each word must start with the next letter determined by the game mode. Words score 1–3 pts based on letter rarity (Scrabble-style), with +2 milestone bonuses every 5 moves. Compete on leaderboards, track stats, and race the clock before the dictionary runs dry.

## How to Play

Players take turns adding 5-letter words to a growing chain. Each word must begin with the letter determined by the **game mode** (last letter by default):

```
SENSE → ENTER → ROVER → RANGE → EMBER → ...
```

- Words must be valid 5-letter English words (5,900+ word dictionary)
- No repeating words in the same game
- Any server member can join — just use `/chain play`
- **Scoring:** words earn 1–3 pts based on letter rarity · +2 milestone bonus every 5 words
- **Modes:** `last` (default), `random`, `2nd`, `3rd`, `4th` letter

---

## Commands

### Chain Game

| Command | Description |
|---------|-------------|
| `/chain start [mode]` | Start a new chain game (optional mode: `last`/`random`/`2nd`/`3rd`/`4th`) |
| `/chain play <word>` | Add a word to the active chain |
| `/chain status` | View the current chain, next letter, and words remaining |
| `/chain words <letter>` | List words used starting with a letter + how many are left |
| `/chain hint` | Ask for a hint — reveals the 2nd letter of valid words (e.g. `E N _ _ _`), **visible to all** |
| `/chain end` | End the game and show per-player results |
| `/chain help` | Rules, scoring, and mode reference |

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

### Scoring

Words are scored by **letter rarity** using Scrabble tile values:

| Tier | Scrabble letter sum | Points |
|------|---------------------|--------|
| ★☆☆ Common | ≤ 7 | +1 pt |
| ★★☆ Moderate | 8–12 | +2 pts |
| ★★★ Rare | ≥ 13 | +3 pts |

Plus a **+2 milestone bonus** every 5 words added to the chain.

### Game Modes

| Mode | Next letter comes from… |
|------|------------------------|
| `last` *(default)* | Last letter of the word |
| `random` | A random letter from the word (prefers letters with remaining words) |
| `2nd` | Second letter |
| `3rd` | Third (middle) letter |
| `4th` | Fourth letter |

### Hints

`/chain hint` is **visible to everyone in the channel** — so using it is a public admission of being stuck. It picks one word per difficulty tier and reveals only the **2nd letter** (the starting letter is already shown in the game state):

```
Words starting with E — second letter revealed:
★☆☆  E N _ _ _  — Common  (+1 pt)
★★☆  E H _ _ _  — Moderate (+2 pts)
★★★  E X _ _ _  — Rare    (+3 pts)
```

Each call picks a fresh random word per tier.

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

The word list lives in `data/words.txt` — one uppercase word per line, sorted alphabetically. It ships with **5,900+** valid 5-letter English words, merged from multiple public word lists.

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

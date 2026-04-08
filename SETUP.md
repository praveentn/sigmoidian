# Sigmoidian — Discord Wordle Bot

## Quick Start (Windows)

### 1. Create a Discord Application

1. Go to https://discord.com/developers/applications
2. Click **New Application** → give it a name (e.g. "Sigmoidian")
3. Go to **Bot** tab → click **Add Bot** → confirm
4. Under **Token** click **Reset Token** and copy it
5. Under **Privileged Gateway Intents** you don't need anything extra (no message content needed)

### 2. Invite the bot to your server

Still in the Developer Portal:

1. Go to **OAuth2 → URL Generator**
2. Scopes: ✅ `bot` ✅ `applications.commands`
3. Bot Permissions: ✅ `Send Messages` ✅ `Embed Links` ✅ `Use Slash Commands`
4. Copy the generated URL → open in browser → select your server → Authorize

### 3. Set up the project

```cmd
cd path\to\sigmoidian

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and paste your bot token:

```
DISCORD_TOKEN=your_actual_token_here
```

### 4. Run the bot

```cmd
python bot.py
```

You should see:
```
✅  Logged in as YourBot#1234 (ID: ...)
    Connected to 1 guild(s)
    Database initialised.
```

Slash commands register globally and may take **up to 1 hour** to appear on Discord.
To test immediately, you can restrict registration to one guild (see bot.py comment).

---

## Commands

### Wordle (solo)
| Command | Description |
|---------|-------------|
| `/wordle start` | Start a new game (one per user per server) |
| `/wordle guess <word>` | Submit a 5-letter guess |
| `/wordle status` | View your current board |
| `/wordle giveup` | Reveal the answer and abandon |
| `/wordle help` | Rules recap |

### Word Chain (multiplayer)
| Command | Description |
|---------|-------------|
| `/chain start` | Start a chain game in this channel |
| `/chain play <word>` | Add your word to the chain |
| `/chain status` | View current chain |
| `/chain end` | End the game and show results |
| `/chain help` | Rules recap |

**Chain rules:** Each word must start with the last letter of the previous word.
Example: `SENSE` → `ENTER` → `ROVER` → `RANGE` → `EMBER` → …

**Scoring:** +1 pt per valid word · +2 bonus pts every 5 words in the chain

### Stats
| Command | Description |
|---------|-------------|
| `/stats` | Your personal stats (private) |
| `/leaderboard` | Server leaderboard |
| `/topwords` | Most guessed words in this server |

---

## Expanding the word list

Add one word per line to `words.txt` in the project root — the bot loads it on startup.

```
STOVE
CLEFT
FJORD
```

---

## File structure

```
sigmoidian/
├── bot.py              ← entry point
├── config.py           ← constants
├── wordle_bot.db       ← SQLite database (auto-created)
├── words.txt           ← optional extra words
├── cogs/
│   ├── wordle_cog.py   ← /wordle commands
│   ├── chain_cog.py    ← /chain commands
│   └── stats_cog.py    ← /stats /leaderboard /topwords
├── game/
│   ├── wordle.py       ← Wordle logic
│   └── chain.py        ← Chain game logic
└── utils/
    ├── database.py     ← SQLite helpers
    ├── words.py        ← word lists
    └── display.py      ← embed / emoji grid builders
```

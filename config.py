import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.path.join("data", "wordle_bot.db")
MAX_ATTEMPTS = 600
WORD_LENGTH = 5
CHAIN_TIMEOUT = 600  # seconds per turn (informational only, not enforced by timer)

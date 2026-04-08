import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = "wordle_bot.db"
MAX_ATTEMPTS = 6
WORD_LENGTH = 5
CHAIN_TIMEOUT = 120  # seconds per turn (informational only, not enforced by timer)

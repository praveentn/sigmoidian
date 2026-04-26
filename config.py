import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
MAX_ATTEMPTS = 600
WORD_LENGTH = 5
CHAIN_TIMEOUT = 600  # seconds per turn (informational only, not enforced by timer)

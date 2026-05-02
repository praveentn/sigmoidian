import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
MAX_ATTEMPTS = 600
WORD_LENGTH = 5
CHAIN_TIMEOUT = 600  # seconds per turn (informational only, not enforced by timer)

# ── External Leaderboards ──────────────────────────────────────────────────────
# Comma-separated list of external leaderboard service names to enable.
# Each service needs a corresponding <NAME>_ENABLED, <NAME>_URL, and <NAME>_API_KEY env var.
# Example: EXTERNAL_LEADERBOARDS="SIGMAFEUD,NAVI"
EXTERNAL_LEADERBOARDS = [
    s.strip() for s in os.getenv("EXTERNAL_LEADERBOARDS", "").split(",") if s.strip()
]

def _leaderboard_config(name: str) -> dict | None:
    """Return config for a named leaderboard service if it's enabled, else None."""
    enabled = os.getenv(f"{name}_ENABLED", "false").lower() in ("1", "true", "yes")
    if not enabled:
        return None
    url = os.getenv(f"{name}_URL", "").strip()
    key = os.getenv(f"{name}_API_KEY", "").strip()
    if not url or not key:
        return None
    raw_guilds = os.getenv(f"{name}_GUILDS", "").strip()
    guilds = {g.strip() for g in raw_guilds.split(",") if g.strip()} if raw_guilds else set()
    return {"url": url, "api_key": key, "guilds": guilds}  # empty set = all guilds allowed

LEADERBOARD_SERVICES: dict[str, dict] = {
    name: cfg
    for name in EXTERNAL_LEADERBOARDS
    if (cfg := _leaderboard_config(name)) is not None
}

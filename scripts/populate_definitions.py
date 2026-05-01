#!/usr/bin/env python3
"""
One-time script: populate word_definitions table from the Free Dictionary API.

Run this BEFORE starting the bot to pre-populate definitions for every word
in data/words.txt. The bot reads only from the DB at runtime — no live API calls.

Usage:
    python scripts/populate_definitions.py                # fetch all missing words
    python scripts/populate_definitions.py --refetch      # re-fetch everything
    python scripts/populate_definitions.py --limit 500    # fetch at most N words

Requires DATABASE_URL env var (same as the bot).
"""
import argparse
import asyncio
import logging
import os
import pathlib
import sys

import aiohttp
import asyncpg
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("populate_definitions")

_WORDS_FILE = pathlib.Path(__file__).parent.parent / "data" / "words.txt"
_API_URL    = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
_DELAY      = 0.25   # seconds between API requests — stay well under free-tier limits
_TIMEOUT    = aiohttp.ClientTimeout(total=6)


# ── API fetch ──────────────────────────────────────────────────────────────────

async def fetch_one(session: aiohttp.ClientSession, word: str) -> dict | None:
    """
    Fetch the first usable definition for `word`.
    Returns {pos, meaning, example} or None if not found / error.
    """
    url = _API_URL.format(word=word.lower())
    try:
        async with session.get(url, timeout=_TIMEOUT) as resp:
            if resp.status == 404:
                return None          # word simply not in this dictionary
            if resp.status != 200:
                log.warning("HTTP %s for %s", resp.status, word)
                return None
            data = await resp.json()
    except asyncio.TimeoutError:
        log.warning("Timeout fetching %s", word)
        return None
    except Exception as exc:
        log.warning("Error fetching %s: %s", word, exc)
        return None

    if not isinstance(data, list) or not data:
        return None

    for entry in data:
        for meaning in entry.get("meanings", []):
            pos  = meaning.get("partOfSpeech", "")
            defs = meaning.get("definitions", [])
            if not defs:
                continue
            d       = defs[0]
            text    = (d.get("definition") or "").strip()
            example = (d.get("example") or "").strip()
            if text:
                return {
                    "pos":     pos,
                    "meaning": text[:220],
                    "example": example[:140] if example else "",
                }
    return None


# ── DB helpers ─────────────────────────────────────────────────────────────────

async def ensure_table(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS word_definitions (
            word     TEXT PRIMARY KEY,
            pos      TEXT NOT NULL DEFAULT '',
            meaning  TEXT NOT NULL DEFAULT '',
            example  TEXT NOT NULL DEFAULT ''
        )
    """)


async def already_defined(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT word FROM word_definitions")
    return {r["word"] for r in rows}


async def save(conn: asyncpg.Connection, word: str, defn: dict) -> None:
    await conn.execute(
        """INSERT INTO word_definitions (word, pos, meaning, example)
           VALUES ($1,$2,$3,$4)
           ON CONFLICT(word) DO UPDATE SET
               pos=EXCLUDED.pos,
               meaning=EXCLUDED.meaning,
               example=EXCLUDED.example""",
        word, defn["pos"], defn["meaning"], defn["example"],
    )


# ── Main ───────────────────────────────────────────────────────────────────────

async def main(refetch: bool, limit: int | None) -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("ERROR: DATABASE_URL environment variable is not set.")

    if not _WORDS_FILE.exists():
        sys.exit(f"ERROR: Word list not found at {_WORDS_FILE}")

    # Load word list
    words: list[str] = []
    with _WORDS_FILE.open() as f:
        for line in f:
            w = line.strip().upper()
            if len(w) == 5 and w.isalpha():
                words.append(w)
    log.info("Word list: %d words loaded from %s", len(words), _WORDS_FILE.name)

    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=3)
    async with pool.acquire() as conn:
        await ensure_table(conn)
        defined = set() if refetch else await already_defined(conn)

    todo = [w for w in words if w not in defined]
    if limit:
        todo = todo[:limit]

    log.info(
        "DB has %d definitions · %d words to fetch%s",
        len(defined), len(todo),
        f" (capped at {limit})" if limit else "",
    )

    if not todo:
        log.info("Nothing to do — all words already have definitions.")
        await pool.close()
        return

    found = skipped = errors = 0

    async with aiohttp.ClientSession() as session:
        for i, word in enumerate(todo, start=1):
            defn = await fetch_one(session, word)

            if defn:
                async with pool.acquire() as conn:
                    await save(conn, word, defn)
                found += 1
            else:
                skipped += 1

            # Progress log every 100 words
            if i % 100 == 0 or i == len(todo):
                pct = i * 100 // len(todo)
                log.info(
                    "[%3d%%] %d/%d — found: %d  skipped: %d",
                    pct, i, len(todo), found, skipped,
                )

            await asyncio.sleep(_DELAY)

    log.info(
        "Done.  Definitions added: %d  |  Not found: %d  |  Total in DB: ~%d",
        found, skipped, len(defined) + found,
    )
    await pool.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate word_definitions table")
    parser.add_argument(
        "--refetch",
        action="store_true",
        help="Re-fetch and overwrite all existing definitions",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Fetch at most N words (useful for testing)",
    )
    args = parser.parse_args()
    asyncio.run(main(refetch=args.refetch, limit=args.limit))

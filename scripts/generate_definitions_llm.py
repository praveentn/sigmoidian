#!/usr/bin/env python3
"""
Generate pos, meaning, and example for words in words.txt using the Anthropic API,
then upsert them into the word_definitions table.

Words already in word_definitions (with a non-empty meaning) are skipped by default.
Words listed in exclude_words.txt are always skipped.

Usage:
    python scripts/generate_definitions_llm.py [options]

Options:
    --words-file PATH       Source word list  (default: data/words.txt)
    --exclude-file PATH     Exclusion list    (default: data/exclude_words.txt)
    --batch-size N          Words per API call (default: 30)
    --limit N               Stop after N words (0 = all)
    --overwrite             Re-generate even if a definition already exists
    --dry-run               Print what would be done but don't write to DB
    --output-file PATH      Also append results as JSON-lines to this file
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import anthropic
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DEFAULT_WORDS   = ROOT / "data" / "words.txt"
DEFAULT_EXCLUDE = ROOT / "data" / "exclude_words.txt"

# ── Anthropic ──────────────────────────────────────────────────────────────────
MODEL   = "claude-haiku-4-5-20251001"   # fast + cheap; swap to sonnet for better quality
client  = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = (
    "You are a concise dictionary editor. "
    "For each word supplied, return a JSON array where every element is an object with keys: "
    "\"word\", \"pos\" (part of speech abbreviation, e.g. n., v., adj., adv., prep., conj., interj.), "
    "\"meaning\" (one plain-English sentence, ≤ 20 words), "
    "\"example\" (one short example sentence using the word, ≤ 15 words). "
    "Preserve the exact order of the words. "
    "Return ONLY the JSON array — no prose, no markdown fences."
)


def _build_user_prompt(words: list[str]) -> str:
    return "Words: " + ", ".join(words)


def _call_api(words: list[str]) -> list[dict]:
    """Call the Anthropic API for a batch of words. Returns list of dicts."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(words)}],
    )
    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Strip accidental markdown fences if the model slips up
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            data = json.loads(raw.strip())
        else:
            raise
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got: {type(data)}")
    return data


# ── DB ─────────────────────────────────────────────────────────────────────────

async def _get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=5)


async def _get_existing_words(pool: asyncpg.Pool) -> set[str]:
    """Words that already have a non-empty meaning in the DB."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT word FROM word_definitions WHERE meaning != ''"
        )
    return {r["word"] for r in rows}


async def _upsert_definition(pool: asyncpg.Pool, word: str, pos: str, meaning: str, example: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO word_definitions (word, pos, meaning, example)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (word) DO UPDATE
                   SET pos=EXCLUDED.pos, meaning=EXCLUDED.meaning, example=EXCLUDED.example""",
            word.upper(), pos, meaning, example,
        )


# ── Main ───────────────────────────────────────────────────────────────────────

async def main(args: argparse.Namespace) -> None:
    # ── Load word list ────────────────────────────────────────────────────────
    words_path = Path(args.words_file)
    if not words_path.exists():
        sys.exit(f"Words file not found: {words_path}")
    all_words = [w.strip().upper() for w in words_path.read_text().splitlines() if w.strip()]

    # ── Load exclusions ───────────────────────────────────────────────────────
    exclude_path = Path(args.exclude_file)
    excluded: set[str] = set()
    if exclude_path.exists():
        excluded = {w.strip().upper() for w in exclude_path.read_text().splitlines() if w.strip()}
        print(f"Exclusion list loaded: {len(excluded)} word(s) from {exclude_path}")
    else:
        print(f"No exclusion file at {exclude_path} — skipping exclusion step")

    # ── Connect to DB ─────────────────────────────────────────────────────────
    pool = await _get_pool()

    existing: set[str] = set()
    if not args.overwrite:
        existing = await _get_existing_words(pool)
        print(f"Already defined in DB: {len(existing)} word(s) — will skip (use --overwrite to redo)")

    # ── Filter words to process ───────────────────────────────────────────────
    to_process = [
        w for w in all_words
        if w not in excluded and (args.overwrite or w not in existing)
    ]

    if args.limit:
        to_process = to_process[: args.limit]

    print(f"Words to process: {len(to_process)}")
    if not to_process:
        print("Nothing to do.")
        await pool.close()
        return

    # ── Output file ───────────────────────────────────────────────────────────
    out_fh = None
    if args.output_file:
        out_fh = open(args.output_file, "a", encoding="utf-8")

    # ── Process in batches ────────────────────────────────────────────────────
    batch_size = max(1, args.batch_size)
    total_done = 0
    total_failed = 0

    for i in range(0, len(to_process), batch_size):
        batch = to_process[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(to_process) + batch_size - 1) // batch_size
        print(f"\nBatch {batch_num}/{total_batches}: {batch}")

        for attempt in range(1, 4):
            try:
                results = _call_api(batch)
                break
            except Exception as exc:
                print(f"  Attempt {attempt} failed: {exc}")
                if attempt == 3:
                    print(f"  Skipping batch after 3 failures.")
                    total_failed += len(batch)
                    results = []
                else:
                    time.sleep(5 * attempt)

        for entry in results:
            word    = str(entry.get("word", "")).strip().upper()
            pos     = str(entry.get("pos", "")).strip()
            meaning = str(entry.get("meaning", "")).strip()
            example = str(entry.get("example", "")).strip()

            if not word or not meaning:
                print(f"  Skipping incomplete entry: {entry}")
                total_failed += 1
                continue

            if args.dry_run:
                print(f"  [DRY-RUN] {word}: {pos} | {meaning} | {example}")
            else:
                await _upsert_definition(pool, word, pos, meaning, example)
                print(f"  ✓ {word}: {pos} — {meaning}")

            if out_fh:
                out_fh.write(json.dumps({"word": word, "pos": pos, "meaning": meaning, "example": example}) + "\n")

            total_done += 1

        # Small pause between batches to be kind to rate limits
        if i + batch_size < len(to_process):
            time.sleep(1)

    if out_fh:
        out_fh.close()

    await pool.close()

    print(f"\nDone. Processed: {total_done}  Failed: {total_failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate definitions via Anthropic API")
    parser.add_argument("--words-file",   default=str(DEFAULT_WORDS))
    parser.add_argument("--exclude-file", default=str(DEFAULT_EXCLUDE))
    parser.add_argument("--batch-size",   type=int, default=30)
    parser.add_argument("--limit",        type=int, default=0, help="0 = no limit")
    parser.add_argument("--overwrite",    action="store_true")
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--output-file",  default="", help="Also write JSON-lines here")
    args = parser.parse_args()
    asyncio.run(main(args))

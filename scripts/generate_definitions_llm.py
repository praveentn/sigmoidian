#!/usr/bin/env python3
"""
Generate pos, meaning, and example for every word in words.txt (minus exclude_words.txt)
using the Anthropic API, inserting each batch into word_definitions immediately after the
LLM responds — no waiting for the full run to finish.

Words already in word_definitions (non-empty meaning) are skipped by default.
Words in exclude_words.txt are always skipped.

Usage:
    python scripts/generate_definitions_llm.py [options]

Options:
    --words-file PATH       Source word list  (default: data/words.txt)
    --exclude-file PATH     Exclusion list    (default: data/exclude_words.txt)
    --batch-size N          Words per API call (default: 30)
    --limit N               Stop after N words (0 = all)
    --overwrite             Re-generate even if a definition already exists in DB
    --dry-run               Print results but do not write to DB
    --output-file PATH      Also append results as JSON-lines to this file
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT            = Path(__file__).parent.parent
DEFAULT_WORDS   = ROOT / "data" / "words.txt"
DEFAULT_EXCLUDE = ROOT / "data" / "exclude_words.txt"

# ── Anthropic ──────────────────────────────────────────────────────────────────
MODEL  = "claude-haiku-4-5-20251001"   # fast + cheap; change to claude-sonnet-4-6 for higher quality
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = (
    "You are a concise dictionary editor. "
    "For each word supplied, return a JSON array where every element has keys: "
    "\"word\", \"pos\" (part of speech abbreviation, e.g. n., v., adj., adv., prep., conj., interj.), "
    "\"meaning\" (one plain-English sentence, ≤ 20 words), "
    "\"example\" (one short sentence using the word, ≤ 15 words). "
    "Preserve the exact order of the input words. "
    "Return ONLY the JSON array — no prose, no markdown fences."
)


def _call_api(words: list[str]) -> list[dict]:
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Words: " + ", ".join(words)}],
    )
    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Strip accidental markdown fences
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
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT word FROM word_definitions WHERE meaning != ''")
    return {r["word"] for r in rows}


async def _insert_batch(pool: asyncpg.Pool, entries: list[dict]) -> int:
    """
    Upsert a list of definition dicts into the DB in a single transaction.
    Returns number of rows written.
    """
    if not entries:
        return 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """INSERT INTO word_definitions (word, pos, meaning, example)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (word) DO UPDATE
                       SET pos=EXCLUDED.pos,
                           meaning=EXCLUDED.meaning,
                           example=EXCLUDED.example""",
                [
                    (e["word"].upper(), e["pos"], e["meaning"], e["example"])
                    for e in entries
                ],
            )
    return len(entries)


# ── Main ───────────────────────────────────────────────────────────────────────

async def main(args: argparse.Namespace) -> None:
    # ── Load word list ────────────────────────────────────────────────────────
    words_path = Path(args.words_file)
    if not words_path.exists():
        sys.exit(f"Words file not found: {words_path}")
    all_words = [w.strip().upper() for w in words_path.read_text().splitlines() if w.strip()]
    print(f"Total words in {words_path.name}: {len(all_words)}")

    # ── Load exclusions ───────────────────────────────────────────────────────
    exclude_path = Path(args.exclude_file)
    excluded: set[str] = set()
    if exclude_path.exists():
        excluded = {w.strip().upper() for w in exclude_path.read_text().splitlines() if w.strip()}
        print(f"Exclusion list: {len(excluded)} word(s) from {exclude_path.name}")
    else:
        print(f"No exclusion file at {exclude_path} — no words excluded")

    # ── Connect to DB ─────────────────────────────────────────────────────────
    pool = await _get_pool()

    existing: set[str] = set()
    if not args.overwrite:
        existing = await _get_existing_words(pool)
        print(f"Already in DB (will skip): {len(existing)} word(s)  — use --overwrite to redo")

    # ── Build the final list to process ──────────────────────────────────────
    to_process = [
        w for w in all_words
        if w not in excluded and (args.overwrite or w not in existing)
    ]
    if args.limit:
        to_process = to_process[: args.limit]

    total = len(to_process)
    print(f"Words to generate definitions for: {total}")
    if not total:
        print("Nothing to do.")
        await pool.close()
        return

    # ── Output file ───────────────────────────────────────────────────────────
    out_fh = open(args.output_file, "a", encoding="utf-8") if args.output_file else None

    # ── Process batches — insert to DB immediately after each LLM response ────
    batch_size    = max(1, args.batch_size)
    total_batches = (total + batch_size - 1) // batch_size
    inserted      = 0
    failed        = 0

    print(f"\nProcessing {total_batches} batch(es) of up to {batch_size} words each.\n")

    for batch_num, i in enumerate(range(0, total, batch_size), start=1):
        batch  = to_process[i : i + batch_size]
        ts     = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Batch {batch_num}/{total_batches} ({len(batch)} words) → calling LLM ...")

        # Call API with retry
        results = []
        for attempt in range(1, 4):
            try:
                results = _call_api(batch)
                break
            except Exception as exc:
                print(f"  Attempt {attempt} failed: {exc}")
                if attempt == 3:
                    print(f"  Giving up on this batch — {len(batch)} words skipped.")
                    failed += len(batch)
                else:
                    time.sleep(5 * attempt)

        if not results:
            continue

        # Validate entries
        valid_entries = []
        for entry in results:
            word    = str(entry.get("word", "")).strip().upper()
            pos     = str(entry.get("pos", "")).strip()
            meaning = str(entry.get("meaning", "")).strip()
            example = str(entry.get("example", "")).strip()
            if not word or not meaning:
                print(f"  ⚠ Skipping incomplete entry: {entry}")
                failed += 1
                continue
            valid_entries.append({"word": word, "pos": pos, "meaning": meaning, "example": example})

        # Insert this batch immediately
        if not args.dry_run:
            n = await _insert_batch(pool, valid_entries)
            inserted += n
            print(f"  ✓ Inserted {n} definition(s) into DB  [total so far: {inserted}/{total}]")
        else:
            for e in valid_entries:
                print(f"  [DRY-RUN] {e['word']}: {e['pos']} | {e['meaning']}")
            inserted += len(valid_entries)

        # Write to output file if requested
        if out_fh:
            for e in valid_entries:
                out_fh.write(json.dumps(e) + "\n")
            out_fh.flush()

        # Brief pause between batches to stay within rate limits
        if i + batch_size < total:
            time.sleep(1)

    if out_fh:
        out_fh.close()

    await pool.close()

    print(f"\n{'='*50}")
    print(f"Finished. Inserted: {inserted}  Failed/skipped: {failed}  Total words: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate word definitions via Anthropic API")
    parser.add_argument("--words-file",   default=str(DEFAULT_WORDS))
    parser.add_argument("--exclude-file", default=str(DEFAULT_EXCLUDE))
    parser.add_argument("--batch-size",   type=int, default=30)
    parser.add_argument("--limit",        type=int, default=0, help="0 = no limit")
    parser.add_argument("--overwrite",    action="store_true")
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--output-file",  default="", help="Also write JSON-lines here")
    args = parser.parse_args()
    asyncio.run(main(args))

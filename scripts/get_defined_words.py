#!/usr/bin/env python3
"""
Query the word_definitions table and write all words to a file.

Usage (on the server):
    python scripts/get_defined_words.py [--output defined_words.txt]
"""
import argparse
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def main(output_path: str) -> None:
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=3)
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT word FROM word_definitions ORDER BY word")
    await pool.close()

    words = [row["word"] for row in rows]
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(words) + "\n")

    print(f"Written {len(words)} words to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="defined_words.txt")
    args = parser.parse_args()
    asyncio.run(main(args.output))

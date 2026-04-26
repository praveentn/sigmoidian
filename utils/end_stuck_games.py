"""
Migration script to end all old chain games that are still 'active' but have no possible moves left (i.e., the chain is stuck or exhausted).
"""
import asyncio
import asyncpg
import os
import json
from utils.words import remaining_for_letter

async def main():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    async with pool.acquire() as conn:
        # Find all active games
        games = await conn.fetch(
            "SELECT id, words_used, next_letter FROM chain_games WHERE status='active'"
        )
        print(f"Found {len(games)} active games.")
        ended = 0
        for game in games:
            words_used = json.loads(game["words_used"])
            next_letter = game["next_letter"]
            # If no next_letter, game just started, skip
            if not next_letter:
                continue
            # Use your word list logic to check if any words remain
            used_set = set(words_used)
            if remaining_for_letter(next_letter, used_set) == 0:
                await conn.execute(
                    "UPDATE chain_games SET status='ended' WHERE id=$1",
                    game["id"],
                )
                ended += 1
        print(f"Ended {ended} games.")
    await pool.close()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())

"""
Recalculate and update longest_chain for all users based on historical chain games.
Run this script after migrating old data to fix longest_chain values.
"""
import asyncio
import asyncpg
import os
import json

async def main():
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    async with pool.acquire() as conn:
        # Get all guilds
        guilds = await conn.fetch("SELECT DISTINCT guild_id FROM chain_games")
        for g in guilds:
            guild_id = g["guild_id"]
            print(f"Processing guild {guild_id}")
            # Get all ended games for this guild
            games = await conn.fetch(
                "SELECT id, words_used FROM chain_games WHERE guild_id=$1 AND status='ended'",
                guild_id,
            )
            # Map user_id to their max chain length
            user_max = {}
            for game in games:
                game_id = game["id"]
                words_used = json.loads(game["words_used"])
                chain_length = len(words_used)
                # Get all unique users in this game
                moves = await conn.fetch(
                    "SELECT DISTINCT user_id FROM chain_moves WHERE game_id=$1",
                    game_id,
                )
                for m in moves:
                    uid = m["user_id"]
                    user_max[uid] = max(user_max.get(uid, 0), chain_length)
            # Update user_stats for this guild
            for uid, maxlen in user_max.items():
                await conn.execute(
                    "UPDATE user_stats SET longest_chain=$1 WHERE user_id=$2 AND guild_id=$3",
                    maxlen, uid, guild_id,
                )
    await pool.close()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())

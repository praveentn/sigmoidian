"""
One-time migration script: SQLite → PostgreSQL.

Usage:
    DATABASE_URL="postgresql://..." python migrate_to_postgres.py [path/to/wordle_bot.db]

Defaults to data/wordle_bot.db if no path is given.
"""
import asyncio
import json
import os
import sys

import aiosqlite
import asyncpg


SQLITE_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "wordle_bot.db")
PG_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:oooGXUxPrQkDiQhJZKADAgTbswqtbOJH@postgres.railway.internal:5432/railway")

if not PG_URL:
    print("ERROR: Set DATABASE_URL env var to your PostgreSQL connection string.")
    sys.exit(1)


async def migrate():
    print(f"Opening SQLite DB: {SQLITE_PATH}")
    sqlite = await aiosqlite.connect(SQLITE_PATH)
    sqlite.row_factory = aiosqlite.Row

    print(f"Connecting to PostgreSQL...")
    pg = await asyncpg.connect(PG_URL)

    # ── 1. Create tables (same DDL as init_db) ────────────────────────────────
    print("Creating tables...")
    await pg.execute("""
        CREATE TABLE IF NOT EXISTS chain_games (
            id          SERIAL PRIMARY KEY,
            guild_id    TEXT NOT NULL,
            channel_id  TEXT NOT NULL,
            words_used  TEXT NOT NULL DEFAULT '[]',
            next_letter TEXT,
            game_mode   TEXT NOT NULL DEFAULT 'last',
            started_by  TEXT NOT NULL DEFAULT '',
            status      TEXT NOT NULL DEFAULT 'active',
            created_at  TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS chain_moves (
            id        SERIAL PRIMARY KEY,
            game_id   INTEGER NOT NULL,
            user_id   TEXT NOT NULL,
            username  TEXT,
            word      TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id        TEXT NOT NULL,
            guild_id       TEXT NOT NULL,
            username       TEXT,
            chain_points   INTEGER DEFAULT 0,
            chain_words    INTEGER DEFAULT 0,
            longest_chain  INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        );
        CREATE TABLE IF NOT EXISTS word_log (
            id        SERIAL PRIMARY KEY,
            guild_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            word      TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id            TEXT PRIMARY KEY,
            reminder_channel_id TEXT,
            timezone            TEXT NOT NULL DEFAULT 'UTC',
            last_reminder_date  TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_chain_games_lookup
            ON chain_games(guild_id, channel_id, status);
        CREATE INDEX IF NOT EXISTS idx_chain_moves_game
            ON chain_moves(game_id);
        CREATE INDEX IF NOT EXISTS idx_word_log_guild
            ON word_log(guild_id);
        CREATE INDEX IF NOT EXISTS idx_user_stats_lb
            ON user_stats(guild_id, chain_points DESC);
    """)

    # ── 2. Migrate chain_games ─────────────────────────────────────────────────
    print("Migrating chain_games...")
    async with sqlite.execute("SELECT * FROM chain_games ORDER BY id") as cur:
        rows = await cur.fetchall()
    if rows:
        await pg.executemany(
            """INSERT INTO chain_games (id, guild_id, channel_id, words_used, next_letter,
                                        game_mode, started_by, status, created_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
               ON CONFLICT (id) DO NOTHING""",
            [
                (
                    r["id"], r["guild_id"], r["channel_id"],
                    r["words_used"] or "[]", r["next_letter"],
                    r["game_mode"] or "last", r["started_by"] or "",
                    r["status"] or "active", r["created_at"],
                )
                for r in rows
            ],
        )
        # Reset serial sequence to max id
        max_id = max(r["id"] for r in rows)
        await pg.execute(f"SELECT setval('chain_games_id_seq', {max_id})")
    print(f"  → {len(rows)} chain_games rows")

    # ── 3. Migrate chain_moves ─────────────────────────────────────────────────
    print("Migrating chain_moves...")
    async with sqlite.execute("SELECT * FROM chain_moves ORDER BY id") as cur:
        rows = await cur.fetchall()
    if rows:
        await pg.executemany(
            """INSERT INTO chain_moves (id, game_id, user_id, username, word, timestamp)
               VALUES ($1,$2,$3,$4,$5,$6)
               ON CONFLICT (id) DO NOTHING""",
            [
                (r["id"], r["game_id"], r["user_id"], r["username"], r["word"], r["timestamp"])
                for r in rows
            ],
        )
        max_id = max(r["id"] for r in rows)
        await pg.execute(f"SELECT setval('chain_moves_id_seq', {max_id})")
    print(f"  → {len(rows)} chain_moves rows")

    # ── 4. Migrate user_stats ──────────────────────────────────────────────────
    print("Migrating user_stats...")
    async with sqlite.execute("SELECT * FROM user_stats") as cur:
        rows = await cur.fetchall()
    if rows:
        await pg.executemany(
            """INSERT INTO user_stats (user_id, guild_id, username, chain_points, chain_words, longest_chain)
               VALUES ($1,$2,$3,$4,$5,$6)
               ON CONFLICT (user_id, guild_id) DO NOTHING""",
            [
                (
                    r["user_id"], r["guild_id"], r["username"],
                    r["chain_points"] or 0, r["chain_words"] or 0,
                    r["longest_chain"] if "longest_chain" in r.keys() else 0,
                )
                for r in rows
            ],
        )
    print(f"  → {len(rows)} user_stats rows")

    # ── 5. Migrate word_log ────────────────────────────────────────────────────
    print("Migrating word_log...")
    async with sqlite.execute("SELECT * FROM word_log ORDER BY id") as cur:
        rows = await cur.fetchall()
    if rows:
        await pg.executemany(
            """INSERT INTO word_log (id, guild_id, user_id, word, timestamp)
               VALUES ($1,$2,$3,$4,$5)
               ON CONFLICT (id) DO NOTHING""",
            [
                (r["id"], r["guild_id"], r["user_id"], r["word"], r["timestamp"])
                for r in rows
            ],
        )
        max_id = max(r["id"] for r in rows)
        await pg.execute(f"SELECT setval('word_log_id_seq', {max_id})")
    print(f"  → {len(rows)} word_log rows")

    # ── 6. Migrate guild_settings ──────────────────────────────────────────────
    print("Migrating guild_settings...")
    async with sqlite.execute("SELECT * FROM guild_settings") as cur:
        rows = await cur.fetchall()
    if rows:
        await pg.executemany(
            """INSERT INTO guild_settings (guild_id, reminder_channel_id, timezone, last_reminder_date)
               VALUES ($1,$2,$3,$4)
               ON CONFLICT (guild_id) DO NOTHING""",
            [
                (r["guild_id"], r["reminder_channel_id"], r["timezone"] or "UTC", r["last_reminder_date"])
                for r in rows
            ],
        )
    print(f"  → {len(rows)} guild_settings rows")

    await sqlite.close()
    await pg.close()
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

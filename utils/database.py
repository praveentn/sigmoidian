"""
Database helpers — chain game only.
Uses asyncpg connection pool for PostgreSQL.
"""
import asyncpg
import json
import os

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.environ["DATABASE_URL"],
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
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

            CREATE TABLE IF NOT EXISTS word_definitions (
                word     TEXT PRIMARY KEY,
                pos      TEXT NOT NULL DEFAULT '',
                meaning  TEXT NOT NULL DEFAULT '',
                example  TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS daily_spotlight (
                guild_id        TEXT PRIMARY KEY,
                spotlight_date  TEXT,
                user_id         TEXT,
                channel_id      TEXT,
                claimed         BOOLEAN DEFAULT FALSE
            );
        """)

        # Create indexes (IF NOT EXISTS supported in PG 9.5+)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chain_games_lookup
                ON chain_games(guild_id, channel_id, status);
            CREATE INDEX IF NOT EXISTS idx_chain_moves_game
                ON chain_moves(game_id);
            CREATE INDEX IF NOT EXISTS idx_word_log_guild
                ON word_log(guild_id);
            CREATE INDEX IF NOT EXISTS idx_user_stats_lb
                ON user_stats(guild_id, chain_points DESC);
        """)


def _row_to_dict(row: asyncpg.Record) -> dict:
    return dict(row)


# ── Chain games ────────────────────────────────────────────────────────────────

async def get_active_chain(guild_id: str, channel_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM chain_games WHERE guild_id=$1 AND channel_id=$2 AND status='active' "
            "ORDER BY id DESC LIMIT 1",
            guild_id, channel_id,
        )
        return _row_to_dict(row) if row else None


async def create_chain_game(
    guild_id: str, channel_id: str, game_mode: str = "last", started_by: str = ""
) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        game_id = await conn.fetchval(
            "INSERT INTO chain_games (guild_id, channel_id, game_mode, started_by) "
            "VALUES ($1,$2,$3,$4) RETURNING id",
            guild_id, channel_id, game_mode, started_by,
        )
        return game_id


async def update_chain_game(
    game_id: int, words_used: list, next_letter: str, status: str = "active"
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE chain_games SET words_used=$1, next_letter=$2, status=$3 WHERE id=$4",
            json.dumps(words_used), next_letter, status, game_id,
        )


async def add_chain_move(game_id: int, user_id: str, username: str, word: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO chain_moves (game_id, user_id, username, word) VALUES ($1,$2,$3,$4)",
            game_id, user_id, username, word,
        )


async def get_chain_moves(game_id: int) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM chain_moves WHERE game_id=$1 ORDER BY timestamp",
            game_id,
        )
        return [_row_to_dict(r) for r in rows]


# ── Stats ──────────────────────────────────────────────────────────────────────

async def upsert_user(user_id: str, guild_id: str, username: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO user_stats (user_id, guild_id, username)
               VALUES ($1,$2,$3)
               ON CONFLICT(user_id, guild_id) DO UPDATE SET username=EXCLUDED.username""",
            user_id, guild_id, username,
        )


async def increment_stat(user_id: str, guild_id: str, col: str, amount: int = 1) -> None:
    safe = {"chain_points", "chain_words"}
    if col not in safe:
        raise ValueError(f"Unknown stat column: {col}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE user_stats SET {col}={col}+$1 WHERE user_id=$2 AND guild_id=$3",
            amount, user_id, guild_id,
        )


async def get_user_stats(user_id: str, guild_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_stats WHERE user_id=$1 AND guild_id=$2",
            user_id, guild_id,
        )
        return _row_to_dict(row) if row else None


async def get_leaderboard(guild_id: str, limit: int = 10) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_stats WHERE guild_id=$1 ORDER BY chain_points DESC LIMIT $2",
            guild_id, limit,
        )
        return [_row_to_dict(r) for r in rows]


async def log_word(guild_id: str, user_id: str, word: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO word_log (guild_id, user_id, word) VALUES ($1,$2,$3)",
            guild_id, user_id, word,
        )


async def update_longest_chain(user_id: str, guild_id: str, chain_length: int) -> None:
    """Update a player's personal best chain length if this game was longer."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE user_stats SET longest_chain = GREATEST(longest_chain, $1) "
            "WHERE user_id=$2 AND guild_id=$3",
            chain_length, user_id, guild_id,
        )


async def get_top_chains(guild_id: str, limit: int = 10) -> list[dict]:
    """Return top N completed games by chain length for a guild."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                g.id,
                g.game_mode,
                jsonb_array_length(g.words_used::jsonb) AS length,
                g.created_at::date                      AS date,
                (SELECT m.username FROM chain_moves m
                 WHERE m.game_id = g.id
                 GROUP BY m.user_id, m.username
                 ORDER BY COUNT(*) DESC LIMIT 1) AS top_player
            FROM chain_games g
            WHERE g.guild_id = $1 AND g.status = 'ended'
              AND jsonb_array_length(g.words_used::jsonb) > 0
            ORDER BY length DESC
            LIMIT $2
            """,
            guild_id, limit,
        )
        return [_row_to_dict(r) for r in rows]


async def get_top_words(guild_id: str, limit: int = 15) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT word, COUNT(*) as count FROM word_log WHERE guild_id=$1 "
            "GROUP BY word ORDER BY count DESC LIMIT $2",
            guild_id, limit,
        )
        return [_row_to_dict(r) for r in rows]


# ── Guild settings / reminders ─────────────────────────────────────────────────

async def get_guild_settings(guild_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM guild_settings WHERE guild_id=$1", guild_id,
        )
        return _row_to_dict(row) if row else None


async def set_guild_reminder(guild_id: str, channel_id: str, tz: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO guild_settings (guild_id, reminder_channel_id, timezone)
               VALUES ($1,$2,$3)
               ON CONFLICT(guild_id) DO UPDATE SET
                   reminder_channel_id=EXCLUDED.reminder_channel_id,
                   timezone=EXCLUDED.timezone""",
            guild_id, channel_id, tz,
        )


async def set_reminder_channel(guild_id: str, channel_id: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO guild_settings (guild_id, reminder_channel_id)
               VALUES ($1,$2)
               ON CONFLICT(guild_id) DO UPDATE SET
                   reminder_channel_id=EXCLUDED.reminder_channel_id""",
            guild_id, channel_id,
        )


async def set_reminder_timezone(guild_id: str, tz: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO guild_settings (guild_id, timezone)
               VALUES ($1,$2)
               ON CONFLICT(guild_id) DO UPDATE SET
                   timezone=EXCLUDED.timezone""",
            guild_id, tz,
        )


async def disable_guild_reminder(guild_id: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE guild_settings SET reminder_channel_id=NULL WHERE guild_id=$1",
            guild_id,
        )


async def update_last_reminder_date(guild_id: str, date_str: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO guild_settings (guild_id, last_reminder_date)
               VALUES ($1,$2)
               ON CONFLICT(guild_id) DO UPDATE SET last_reminder_date=EXCLUDED.last_reminder_date""",
            guild_id, date_str,
        )


async def get_all_reminder_guilds() -> list[dict]:
    """Return all guilds that have an active reminder channel configured."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM guild_settings WHERE reminder_channel_id IS NOT NULL"
        )
        return [_row_to_dict(r) for r in rows]


async def get_active_players(guild_id: str) -> list[dict]:
    """Return all users who have played at least one word in this guild, ranked by points."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, username, chain_words, chain_points FROM user_stats "
            "WHERE guild_id=$1 AND chain_words > 0 ORDER BY chain_points DESC",
            guild_id,
        )
        return [_row_to_dict(r) for r in rows]


async def get_all_time_players(guild_id: str) -> list[dict]:
    """
    Return every user who has ever played at least one word in this guild.

    Uses a UNION of user_stats (primary source) and word_log (fallback) so that
    players are never missed due to a stats-update race or partial write. The
    result is deduplicated by user_id and ordered by points descending.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                u.user_id,
                u.username,
                u.chain_words,
                u.chain_points
            FROM user_stats u
            WHERE u.guild_id = $1 AND u.chain_words > 0

            UNION

            SELECT
                wl.user_id,
                wl.user_id  AS username,   -- fallback: no display name in word_log
                0           AS chain_words,
                0           AS chain_points
            FROM word_log wl
            WHERE wl.guild_id = $1
              AND NOT EXISTS (
                  SELECT 1 FROM user_stats us
                  WHERE us.user_id = wl.user_id
                    AND us.guild_id = $1
                    AND us.chain_words > 0
              )

            ORDER BY chain_points DESC
            """,
            guild_id,
        )
        return [_row_to_dict(r) for r in rows]


async def get_active_chains_for_guild(guild_id: str) -> list[dict]:
    """Return all currently active chain games in a guild."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM chain_games WHERE guild_id=$1 AND status='active' ORDER BY id DESC",
            guild_id,
        )
        return [_row_to_dict(r) for r in rows]


async def get_all_active_game_channels() -> set[tuple[str, str]]:
    """Return set of (guild_id, channel_id) for all currently active games."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT guild_id, channel_id FROM chain_games WHERE status='active'"
        )
        return {(r["guild_id"], r["channel_id"]) for r in rows}


async def get_word_definition(word: str) -> dict | None:
    """Return cached definition for a word, or None if not yet cached."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM word_definitions WHERE word=$1", word.upper()
        )
        return _row_to_dict(row) if row else None


async def save_word_definition(word: str, pos: str, meaning: str, example: str) -> None:
    """Cache a word's definition; no-op if already cached."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO word_definitions (word, pos, meaning, example)
               VALUES ($1,$2,$3,$4)
               ON CONFLICT(word) DO NOTHING""",
            word.upper(), pos, meaning, example,
        )


async def get_spotlight(guild_id: str) -> dict | None:
    """Return today's spotlight record for the guild, or None."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM daily_spotlight WHERE guild_id=$1", guild_id
        )
        return _row_to_dict(row) if row else None


async def set_spotlight(guild_id: str, date_str: str, user_id: str, channel_id: str) -> None:
    """Record today's spotlight player for a guild."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO daily_spotlight (guild_id, spotlight_date, user_id, channel_id, claimed)
               VALUES ($1,$2,$3,$4,FALSE)
               ON CONFLICT(guild_id) DO UPDATE SET
                   spotlight_date=EXCLUDED.spotlight_date,
                   user_id=EXCLUDED.user_id,
                   channel_id=EXCLUDED.channel_id,
                   claimed=FALSE""",
            guild_id, date_str, user_id, channel_id,
        )


async def claim_spotlight(guild_id: str) -> None:
    """Mark the spotlight as claimed (bonus points awarded)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE daily_spotlight SET claimed=TRUE WHERE guild_id=$1", guild_id
        )


async def get_chain_game_by_id(game_id: int) -> dict | None:
    """Fetch any chain game by its ID regardless of status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM chain_games WHERE id=$1", game_id)
        return _row_to_dict(row) if row else None


async def delete_chain_game(game_id: int) -> None:
    """Hard-delete a game and all its moves from the database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM chain_moves WHERE game_id=$1", game_id)
            await conn.execute("DELETE FROM chain_games WHERE id=$1", game_id)

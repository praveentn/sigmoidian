"""
Database helpers — chain game only.
Each function opens/closes its own connection (SQLite WAL mode is safe for concurrent async use).
"""
import aiosqlite
import json
from config import DB_PATH


async def _migrate(db) -> None:
    """One-time migrations for schema changes between versions."""
    # chain_games: add game_mode column if missing
    async with db.execute("PRAGMA table_info(chain_games)") as cur:
        gcols = {row[1] for row in await cur.fetchall()}
    if gcols and "game_mode" not in gcols:
        await db.execute(
            "ALTER TABLE chain_games ADD COLUMN game_mode TEXT NOT NULL DEFAULT 'last'"
        )
        await db.commit()
        print("    DB migration : added game_mode column to chain_games")

    # word_log previously had `game_mode TEXT NOT NULL`; rebuild without it.
    async with db.execute("PRAGMA table_info(word_log)") as cur:
        cols = {row[1] for row in await cur.fetchall()}
    if "game_mode" in cols:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS _word_log_new (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id  TEXT NOT NULL,
                user_id   TEXT NOT NULL,
                word      TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO _word_log_new (id, guild_id, user_id, word, timestamp)
                SELECT id, guild_id, user_id, word, timestamp FROM word_log;
            DROP TABLE word_log;
            ALTER TABLE _word_log_new RENAME TO word_log;
        """)
        await db.commit()
        print("    DB migration : removed game_mode column from word_log")

    # chain_games: add started_by column if missing
    if gcols and "started_by" not in gcols:
        await db.execute(
            "ALTER TABLE chain_games ADD COLUMN started_by TEXT NOT NULL DEFAULT ''"
        )
        await db.commit()
        print("    DB migration : added started_by column to chain_games")

    # user_stats: add longest_chain column if missing
    async with db.execute("PRAGMA table_info(user_stats)") as cur:
        ucols_lc = {row[1] for row in await cur.fetchall()}
    if ucols_lc and "longest_chain" not in ucols_lc:
        await db.execute(
            "ALTER TABLE user_stats ADD COLUMN longest_chain INTEGER DEFAULT 0"
        )
        await db.commit()
        print("    DB migration : added longest_chain column to user_stats")

    # user_stats previously had wordle_wins / wordle_losses columns; drop them if present.
    async with db.execute("PRAGMA table_info(user_stats)") as cur:
        ucols = {row[1] for row in await cur.fetchall()}
    if "wordle_wins" in ucols:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS _user_stats_new (
                user_id      TEXT NOT NULL,
                guild_id     TEXT NOT NULL,
                username     TEXT,
                chain_points INTEGER DEFAULT 0,
                chain_words  INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            );
            INSERT INTO _user_stats_new (user_id, guild_id, username, chain_points, chain_words)
                SELECT user_id, guild_id, username,
                       COALESCE(chain_points, 0), COALESCE(chain_words, 0)
                FROM user_stats;
            DROP TABLE user_stats;
            ALTER TABLE _user_stats_new RENAME TO user_stats;
        """)
        await db.commit()
        print("    DB migration : removed wordle columns from user_stats")


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await _migrate(db)
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS chain_games (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    TEXT NOT NULL,
                channel_id  TEXT NOT NULL,
                words_used  TEXT NOT NULL DEFAULT '[]',
                next_letter TEXT,
                game_mode   TEXT NOT NULL DEFAULT 'last',
                started_by  TEXT NOT NULL DEFAULT '',
                status      TEXT NOT NULL DEFAULT 'active',
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chain_moves (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id   INTEGER NOT NULL,
                user_id   TEXT NOT NULL,
                username  TEXT,
                word      TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
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
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id  TEXT NOT NULL,
                user_id   TEXT NOT NULL,
                word      TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
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
        await db.commit()


# ── Chain games ────────────────────────────────────────────────────────────────

async def get_active_chain(guild_id: str, channel_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM chain_games WHERE guild_id=? AND channel_id=? AND status='active' "
            "ORDER BY id DESC LIMIT 1",
            (guild_id, channel_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def create_chain_game(
    guild_id: str, channel_id: str, game_mode: str = "last", started_by: str = ""
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "INSERT INTO chain_games (guild_id, channel_id, game_mode, started_by) VALUES (?,?,?,?)",
            (guild_id, channel_id, game_mode, started_by),
        ) as cur:
            game_id = cur.lastrowid
        await db.commit()
        return game_id


async def update_chain_game(
    game_id: int, words_used: list, next_letter: str, status: str = "active"
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE chain_games SET words_used=?, next_letter=?, status=? WHERE id=?",
            (json.dumps(words_used), next_letter, status, game_id),
        )
        await db.commit()


async def add_chain_move(game_id: int, user_id: str, username: str, word: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chain_moves (game_id, user_id, username, word) VALUES (?,?,?,?)",
            (game_id, user_id, username, word),
        )
        await db.commit()


async def get_chain_moves(game_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM chain_moves WHERE game_id=? ORDER BY timestamp",
            (game_id,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ── Stats ──────────────────────────────────────────────────────────────────────

async def upsert_user(user_id: str, guild_id: str, username: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO user_stats (user_id, guild_id, username)
               VALUES (?,?,?)
               ON CONFLICT(user_id, guild_id) DO UPDATE SET username=excluded.username""",
            (user_id, guild_id, username),
        )
        await db.commit()


async def increment_stat(user_id: str, guild_id: str, col: str, amount: int = 1) -> None:
    safe = {"chain_points", "chain_words"}
    if col not in safe:
        raise ValueError(f"Unknown stat column: {col}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE user_stats SET {col}={col}+? WHERE user_id=? AND guild_id=?",
            (amount, user_id, guild_id),
        )
        await db.commit()


async def get_user_stats(user_id: str, guild_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_stats WHERE user_id=? AND guild_id=?",
            (user_id, guild_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_leaderboard(guild_id: str, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_stats WHERE guild_id=? ORDER BY chain_points DESC LIMIT ?",
            (guild_id, limit),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def log_word(guild_id: str, user_id: str, word: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO word_log (guild_id, user_id, word) VALUES (?,?,?)",
            (guild_id, user_id, word),
        )
        await db.commit()


async def update_longest_chain(user_id: str, guild_id: str, chain_length: int) -> None:
    """Update a player's personal best chain length if this game was longer."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE user_stats SET longest_chain = MAX(longest_chain, ?) "
            "WHERE user_id=? AND guild_id=?",
            (chain_length, user_id, guild_id),
        )
        await db.commit()


async def get_top_chains(guild_id: str, limit: int = 10) -> list[dict]:
    """Return top N completed games by chain length for a guild."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                g.id,
                g.game_mode,
                json_array_length(g.words_used) AS length,
                date(g.created_at)              AS date,
                (SELECT m.username FROM chain_moves m
                 WHERE m.game_id = g.id
                 GROUP BY m.user_id
                 ORDER BY COUNT(*) DESC LIMIT 1) AS top_player
            FROM chain_games g
            WHERE g.guild_id = ? AND g.status = 'ended'
              AND json_array_length(g.words_used) > 0
            ORDER BY length DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_top_words(guild_id: str, limit: int = 15) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT word, COUNT(*) as count FROM word_log WHERE guild_id=? "
            "GROUP BY word ORDER BY count DESC LIMIT ?",
            (guild_id, limit),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


# ── Guild settings / reminders ─────────────────────────────────────────────────

async def get_guild_settings(guild_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM guild_settings WHERE guild_id=?", (guild_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_guild_reminder(guild_id: str, channel_id: str, tz: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO guild_settings (guild_id, reminder_channel_id, timezone)
               VALUES (?,?,?)
               ON CONFLICT(guild_id) DO UPDATE SET
                   reminder_channel_id=excluded.reminder_channel_id,
                   timezone=excluded.timezone""",
            (guild_id, channel_id, tz),
        )
        await db.commit()


async def disable_guild_reminder(guild_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE guild_settings SET reminder_channel_id=NULL WHERE guild_id=?",
            (guild_id,),
        )
        await db.commit()


async def update_last_reminder_date(guild_id: str, date_str: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO guild_settings (guild_id, last_reminder_date)
               VALUES (?,?)
               ON CONFLICT(guild_id) DO UPDATE SET last_reminder_date=excluded.last_reminder_date""",
            (guild_id, date_str),
        )
        await db.commit()


async def get_all_reminder_guilds() -> list[dict]:
    """Return all guilds that have an active reminder channel configured."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM guild_settings WHERE reminder_channel_id IS NOT NULL"
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_active_players(guild_id: str) -> list[dict]:
    """Return all users who have played at least one word in this guild, ranked by points."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT user_id, username, chain_words, chain_points FROM user_stats "
            "WHERE guild_id=? AND chain_words > 0 ORDER BY chain_points DESC",
            (guild_id,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_active_chains_for_guild(guild_id: str) -> list[dict]:
    """Return all currently active chain games in a guild."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM chain_games WHERE guild_id=? AND status='active' ORDER BY id DESC",
            (guild_id,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

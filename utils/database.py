"""
Database helpers — chain game only.
Each function opens/closes its own connection (SQLite WAL mode is safe for concurrent async use).
"""
import aiosqlite
import json
from config import DB_PATH


async def _migrate(db) -> None:
    """One-time migrations for schema changes between versions."""
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
                user_id      TEXT NOT NULL,
                guild_id     TEXT NOT NULL,
                username     TEXT,
                chain_points INTEGER DEFAULT 0,
                chain_words  INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            );

            CREATE TABLE IF NOT EXISTS word_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id  TEXT NOT NULL,
                user_id   TEXT NOT NULL,
                word      TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
            );
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


async def create_chain_game(guild_id: str, channel_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "INSERT INTO chain_games (guild_id, channel_id) VALUES (?,?)",
            (guild_id, channel_id),
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


async def get_top_words(guild_id: str, limit: int = 15) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT word, COUNT(*) as count FROM word_log WHERE guild_id=? "
            "GROUP BY word ORDER BY count DESC LIMIT ?",
            (guild_id, limit),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

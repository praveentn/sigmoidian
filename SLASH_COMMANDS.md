# Slash Command Registration — How It Works & Fixes Applied

## Background

Discord slash commands come in two scopes:

| Scope | Registration | Propagation |
|-------|-------------|-------------|
| **Guild** (via `DISCORD_GUILD_ID`) | Instant | Only in that server |
| **Global** (no guild ID) | Up to 1 hour | All servers the bot is in |

This bot uses **global commands** in production (Railway). Guild-scoped commands are only used locally for fast dev/test iteration.

---

## Problems Encountered & Root Causes

### 1. Commands wiped after deploy
`sync_commands()` fired with zero commands registered, which tells Discord to delete them all. Caused by a cog failing to load (silently) before the sync ran.

### 2. Commands going stale / not updating after redeploy
py-cord calls `sync_commands()` automatically during `on_connect`, before `on_ready`. This auto-sync can silently fail on a Railway cold start (rate limit, transient network error), leaving Discord with the old or no commands.

### 3. Ghost / duplicate commands after switching from guild → global mode
When `DISCORD_GUILD_ID` is removed, old guild-scoped command registrations remain on Discord indefinitely. They show up alongside or instead of the new global commands in the `/` menu.

### 4. Repeated heavy init on reconnection
`on_ready` fires on every Discord reconnection, not just cold start. Running DB migrations and full cleanup on every reconnect is wasteful and can cause race conditions.

---

## All Fixes Applied

### Fix 1 — `sys.exit(1)` on cog load failure

**This is the most critical fix.** Previously, a failed cog load was caught, logged, and ignored — then `sync_commands()` ran with zero commands, wiping all slash commands from Discord. Now the process aborts immediately. Railway auto-restarts it and keeps retrying until the cog loads cleanly. `sync_commands()` never fires with an empty set.

```python
for cog in COGS:
    try:
        bot.load_extension(cog)
        log.info("Loaded cog: %s", cog)
    except Exception as exc:
        # Abort immediately — if a cog fails to load, sync_commands() would push
        # an empty or partial command list and wipe all slash commands from Discord.
        log.critical("FAILED to load cog %s: %s — aborting startup.", cog, exc, exc_info=True)
        sys.exit(1)
```

### Fix 2 — `_ready_fired` guard in `on_ready`

`on_ready` fires on every Discord reconnection. Without this guard, DB migrations and full cleanup ran on every overnight reconnect. Now the full init path runs **once per process lifetime**; reconnections only do a lightweight re-sync.

```python
_ready_fired = False  # guard: only run full init once per process lifetime

@bot.event
async def on_ready():
    global _ready_fired

    log.info("Discord connected: %s (ID: %s) | guilds: %d",
             bot.user, bot.user.id, len(bot.guilds))

    if _ready_fired:
        # Reconnection — skip heavy init but re-sync commands as a safety net.
        log.info("Reconnected — re-syncing commands.")
        try:
            await bot.sync_commands()
        except Exception as exc:
            log.error("sync_commands() failed on reconnect: %s", exc)
        return

    _ready_fired = True
    ...
```

### Fix 3 — Explicit `sync_commands()` in `on_ready` with error logging

A guaranteed second sync attempt after the bot is fully connected, with full logging of which commands were pushed. If the list is empty, the log warns immediately.

```python
try:
    await bot.sync_commands()
    synced = [c.name for c in bot.pending_application_commands]
    log.info(
        "Commands synced (%s): %s",
        f"guild {DEBUG_GUILDS[0]}" if DEBUG_GUILDS else "global",
        synced if synced else "⚠ EMPTY — cog load may have failed silently",
    )
except Exception as exc:
    log.error("sync_commands() FAILED: %s", exc, exc_info=True)
```

### Fix 4 — Stale guild-command cleanup (check before wipe)

Runs after the sync. Checks each guild for existing guild-scoped registrations using `get_guild_commands` before wiping — only guilds with stale entries are touched. Logs exact counts so you can confirm in Railway what was cleared. Becomes a no-op on all subsequent restarts once the stale entries are gone.

```python
if not DEBUG_GUILDS:
    cleaned = 0
    for guild in bot.guilds:
        try:
            existing = await bot.http.get_guild_commands(bot.user.id, guild.id)
            if existing:
                await bot.http.bulk_upsert_guild_commands(bot.user.id, guild.id, [])
                log.info("Cleared %d stale guild command(s) from %s (%d).",
                         len(existing), guild.name, guild.id)
                cleaned += 1
        except Exception as exc:
            log.warning("Could not clear guild commands for %s: %s", guild.name, exc)
    if cleaned:
        log.info("Stale guild-command cleanup done — %d guild(s) cleared.", cleaned)
    else:
        log.info("No stale guild commands found.")
```

### Fix 5 — Structured logging (`logging` module)

Replaced all `print()` calls with the standard `logging` module. Timestamped log lines with severity levels (`INFO`, `ERROR`, `CRITICAL`) make Railway logs much easier to scan and filter.

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)-8s]  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("sigmoidian")
```

---

## Expected Startup Log (healthy)

After deploying all fixes, Railway logs should look like this:

```
2026-04-14 10:00:01  [INFO    ]  sigmoidian: Loaded cog: cogs.chain_cog
2026-04-14 10:00:01  [INFO    ]  sigmoidian: Loaded cog: cogs.stats_cog
2026-04-14 10:00:01  [INFO    ]  sigmoidian: Status page  →  http://localhost:8080/
2026-04-14 10:00:01  [INFO    ]  sigmoidian: Health JSON  →  http://localhost:8080/health
2026-04-14 10:00:02  [INFO    ]  sigmoidian: Discord connected: sigmoidian#3241 (ID: ...) | guilds: 3
2026-04-14 10:00:02  [INFO    ]  sigmoidian: DB initialised.
2026-04-14 10:00:02  [INFO    ]  sigmoidian: Commands synced (global): ['chain', 'addword', 'removeword', 'checkword', 'stats', 'leaderboard', 'topwords', 'dictionary']
2026-04-14 10:00:02  [INFO    ]  sigmoidian: No stale guild commands found.
```

On reconnection (no full re-init):
```
2026-04-14 10:05:00  [INFO    ]  sigmoidian: Discord connected: sigmoidian#3241 (ID: ...) | guilds: 3
2026-04-14 10:05:00  [INFO    ]  sigmoidian: Reconnected — re-syncing commands.
```

If a cog fails (process will abort and Railway will restart):
```
2026-04-14 10:00:01  [CRITICAL ]  sigmoidian: FAILED to load cog cogs.chain_cog: ... — aborting startup.
```

---

## Checklist When Commands Stop Showing Up

1. **Check Railway logs** — confirm `Commands synced` printed with the full command list. If the list is empty or the line is missing, a cog failed to load.
2. **Restart Discord fully** — global commands are cached per client; `Ctrl+R` is not enough, fully quit and reopen.
3. **Try Discord in a browser** (discord.com) — bypasses the desktop client cache entirely.
4. **Verify bot invite URL** includes both scopes:
   ```
   scope=bot+applications.commands
   ```
5. **Wait up to 1 hour** — global command propagation is Discord's SLA, not the bot's.

---

## Local Development

Set `DISCORD_GUILD_ID` in `.env` for instant command registration in your test server:

```env
DISCORD_GUILD_ID=976816967161892976
```

Remove it (or leave it commented out) for global registration. Do not set this in Railway — guild commands are for dev speed only.

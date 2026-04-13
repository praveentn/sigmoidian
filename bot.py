import os
import certifi

# Must be set before any SSL/network import (discord, aiohttp, etc.)
# Fixes "certificate verify failed" on macOS with python.org Python builds.
os.environ.setdefault("SSL_CERT_FILE",      certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import discord
from discord.ext import commands
import asyncio
import time
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

TOKEN      = os.getenv("DISCORD_TOKEN", "")
PORT       = int(os.getenv("PORT", "8080"))
START_TIME = time.time()

# Optional: register commands instantly to a specific guild instead of waiting
# up to 1 hour for global propagation. Set DISCORD_GUILD_ID in .env while testing.
_raw_guild  = os.getenv("DISCORD_GUILD_ID", "").strip()
DEBUG_GUILDS = [int(_raw_guild)] if _raw_guild.isdigit() else None

# Python 3.10+ no longer auto-creates an event loop at module scope.
# discord.Bot.__init__ calls asyncio.get_event_loop(), so we must set one
# before instantiating the bot.
asyncio.set_event_loop(asyncio.new_event_loop())

intents = discord.Intents.default()
bot     = discord.Bot(intents=intents, debug_guilds=DEBUG_GUILDS)

COGS = [
    "cogs.chain_cog",
    "cogs.stats_cog",
]

# ── Status dashboard ───────────────────────────────────────────────────────────

_STATUS_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="10">
  <title>Sigmoidian — Bot Status</title>
  <style>
    *    {{ box-sizing:border-box; margin:0; padding:0 }}
    body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            background:#1a1a2e; color:#e0e0e0; padding:32px 16px }}
    .wrap{{ max-width:680px; margin:0 auto }}
    h1   {{ color:#7289da; font-size:1.8rem; margin-bottom:24px }}
    h2   {{ color:#99aab5; font-size:1rem; text-transform:uppercase;
            letter-spacing:.08em; margin-bottom:10px }}
    .card{{ background:#16213e; border-radius:10px; padding:18px 22px;
            margin-bottom:16px }}
    ul   {{ list-style:none; line-height:2 }}
    .ok  {{ color:#43b581 }}
    .warn{{ color:#faa61a }}
    .err {{ color:#f04747 }}
    code {{ background:#0f3460; padding:2px 6px; border-radius:4px;
            font-size:.88em }}
    a    {{ color:#7289da; text-decoration:none }}
    a:hover {{ text-decoration:underline }}
    .badge{{ display:inline-block; padding:2px 10px; border-radius:12px;
             font-size:.8rem; font-weight:700 }}
    .badge-ok  {{ background:#43b581; color:#fff }}
    .badge-warn{{ background:#faa61a; color:#000 }}
    footer{{ margin-top:24px; color:#555; font-size:.8rem; text-align:center }}
  </style>
</head>
<body><div class="wrap">
  <h1>🎮 Sigmoidian Discord Bot</h1>
  {content}
  <footer>Auto-refreshes every 10 s &nbsp;·&nbsp;
    <a href="/health">/health JSON</a></footer>
</div></body></html>"""


async def _status_page(request):
    up   = int(time.time() - START_TIME)
    uptime = f"{up//3600}h {(up%3600)//60}m {up%60}s"

    token_set  = bool(TOKEN) and TOKEN != "your_bot_token_here"
    discord_ok = bool(bot.user)

    rows = []
    rows.append(f'<li>{"✅" if token_set  else "❌"} Token  : '
                f'{"<span class=ok>configured</span>" if token_set else "<span class=err>not set — edit <code>.env</code></span>"}</li>')
    rows.append(f'<li>{"✅" if discord_ok else "⏳"} Discord: '
                f'{"<span class=ok>connected as <b>" + str(bot.user) + "</b></span>" if discord_ok else "<span class=warn>not connected yet</span>"}</li>')
    rows.append(f'<li>✅ HTTP server: <span class=ok>port {PORT}</span></li>')
    rows.append(f'<li>⏱ Uptime: {uptime}</li>')

    content = f'<div class=card><h2>Status</h2><ul>{"".join(rows)}</ul></div>'

    if discord_ok:
        content += (f'<div class=card><h2>Bot Info</h2><ul>'
                    f'<li>🤖 {bot.user}</li>'
                    f'<li>🏠 Guilds: {len(bot.guilds)}</li>'
                    f'<li>📡 Latency: {round(bot.latency*1000)} ms</li>'
                    f'</ul></div>')
    elif not token_set:
        content += """<div class=card><h2>Setup Checklist</h2><ol style="padding-left:18px;line-height:2.2">
  <li>Go to <a href="https://discord.com/developers/applications">discord.com/developers</a> → New Application</li>
  <li>Bot tab → Add Bot → copy token</li>
  <li>Paste into <code>.env</code> as <code>DISCORD_TOKEN=&lt;token&gt;</code></li>
  <li>Restart the bot — this page refreshes automatically</li>
</ol><p style="margin-top:10px">Full guide: <code>SETUP.md</code></p></div>"""

    return web.Response(text=_STATUS_TMPL.format(content=content),
                        content_type="text/html")


async def _health_json(request):
    return web.json_response({
        "status":     "online",
        "discord":    str(bot.user) if bot.user else None,
        "guilds":     len(bot.guilds),
        "latency_ms": round(bot.latency * 1000, 2) if bot.user else None,
        "uptime_s":   int(time.time() - START_TIME),
        "port":       PORT,
    })


async def _run_web_server():
    app = web.Application()
    app.router.add_get("/",       _status_page)
    app.router.add_get("/health", _health_json)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"    Status page  →  http://localhost:{PORT}/")
    print(f"    Health JSON  →  http://localhost:{PORT}/health")


# ── Bot events ─────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    from utils.database import init_db
    await init_db()
    print(f"✅  Discord  : {bot.user} (ID: {bot.user.id})")
    print(f"    Guilds  : {len(bot.guilds)}")
    print("    DB      : initialised")

    # Explicitly re-sync slash commands on every startup so redeploys never
    # leave stale or missing commands. py-cord's auto-sync on on_connect can
    # silently fail; this call in on_ready is the guaranteed safety net.
    try:
        await bot.sync_commands()
        cmds = [c.name for c in bot.pending_application_commands]
        print(f"    Commands synced ({'guild' if DEBUG_GUILDS else 'global'} mode): {cmds}")
    except Exception as e:
        print(f"    ❌ sync_commands() FAILED: {e}")


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    msg = f"An error occurred: {error}"
    try:
        if ctx.response.is_done():
            await ctx.followup.send(msg, ephemeral=True)
        else:
            await ctx.respond(msg, ephemeral=True)
    except Exception:
        pass
    raise error


# ── Cogs ───────────────────────────────────────────────────────────────────────

for cog in COGS:
    bot.load_extension(cog)


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    await _run_web_server()

    token_set = bool(TOKEN) and TOKEN != "your_bot_token_here"

    if not token_set:
        print("⚠️  DISCORD_TOKEN not set  →  running in local-only mode")
        print(f"    Open http://localhost:{PORT}/ for setup instructions.")
        await asyncio.Event().wait()   # block until Ctrl-C
    else:
        await bot.start(TOKEN)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋  Stopped.")
    finally:
        loop.close()

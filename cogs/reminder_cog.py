"""
Daily 6 AM reminder cog — pings all players in each configured guild with a
word-history fact and a leaderboard snapshot to drive daily engagement.

Admins configure per-guild with /remind channel and /remind timezone; the task
fires every minute, checks whether it is 6:00–6:04 AM in the guild's timezone,
and sends at most once per calendar day (guarded by last_reminder_date).

Reminders are NEVER sent unless a channel has been explicitly configured.

ReminderView uses persistent custom_ids and is registered with bot.add_view() so
buttons remain functional across bot restarts — no in-memory state is required.
"""
import asyncio
import json
import logging
import random
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import commands, tasks
from discord import SlashCommandGroup

from utils import database as db
from utils.wordhistory import get_word_fact
from utils.display import STATS_COLOR, CHAIN_COLOR

log = logging.getLogger("sigmoidian.reminder")

_REMINDER_HOUR   = 6   # fire at 6 AM local time
_REMINDER_WINDOW = 5   # accept minutes 0–4 to survive brief restarts

_SUNRISE_COLOR = discord.Colour.from_rgb(255, 179, 0)
_MENTION_CHUNK_LIMIT = 1800  # safety margin below 2000-char Discord limit

_HOOKS = [
    "The chain won't build itself — time to link up.",
    "Your vocabulary is your weapon. Use it today.",
    "Yesterday's winner is today's target. Go get them.",
    "Every word you know was once someone else's advantage.",
    "The leaderboard doesn't update itself.",
    "Fortune favors the wordy. Prove it.",
    "Today's chain record is wide open — claim it.",
    "One rare word can flip the leaderboard. You know that word.",
    "The dictionary has more moves than you've made.",
    "Your streak is either building or broken — your call.",
    "Words are points. Points are rank. Rank is everything.",
    "Someone in this server is already thinking. Catch up.",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _chunk_mentions(user_ids: list[str]) -> list[str]:
    """Split user IDs into message-sized chunks of Discord mention strings."""
    chunks: list[str] = []
    current = ""
    for uid in user_ids:
        mention = f"<@{uid}> "
        if len(current) + len(mention) > _MENTION_CHUNK_LIMIT:
            if current:
                chunks.append(current.strip())
            current = mention
        else:
            current += mention
    if current:
        chunks.append(current.strip())
    return chunks


def _build_reminder_embed(
    guild_name: str,
    word_fact: str,
    today_display: str,
    top_players: list[dict],
    active_games: list[dict],
    hook: str,
    player_count: int,
) -> discord.Embed:
    embed = discord.Embed(
        title=f"🌅 Good Morning, {guild_name}!",
        description=f"*{hook}*",
        colour=_SUNRISE_COLOR,
    )

    embed.add_field(
        name=f"📖 Today in Word History — {today_display}",
        value=word_fact,
        inline=False,
    )

    if top_players:
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, row in enumerate(top_players[:3]):
            prefix = medals[i] if i < 3 else f"**{i + 1}.**"
            name   = row.get("username") or f"<@{row['user_id']}>"
            pts    = row.get("chain_points", 0)
            words  = row.get("chain_words", 0)
            lines.append(f"{prefix} **{name}** — {pts} pts · {words} words")
        embed.add_field(
            name="🏆 Server Leaderboard",
            value="\n".join(lines),
            inline=False,
        )

    if active_games:
        g           = active_games[0]
        channel_ref = f"<#{g['channel_id']}>"
        words_used  = json.loads(g.get("words_used") or "[]")
        chain_len   = len(words_used)
        next_letter = (g.get("next_letter") or "?").upper()
        if len(active_games) == 1:
            status_val = (
                f"🔗 **Game #{g['id']}** is live in {channel_ref}!\n"
                f"Chain length: **{chain_len}** · next letter: **{next_letter}**\n"
                f"Use `/chain play <word>` to jump in."
            )
        else:
            status_val = (
                f"🔗 **{len(active_games)} games** are running right now!\n"
                f"Use `/chain play <word>` in any game channel to join."
            )
    else:
        status_val = (
            "No game running yet — be the one to start it!\n"
            "Use the **Start a Game** button below or `/chain start`."
        )

    embed.add_field(name="🎮 Chain Status", value=status_val, inline=False)

    player_note = (
        f"{player_count} word warrior{'s' if player_count != 1 else ''} in this server"
        if player_count > 0 else "No players yet"
    )
    embed.set_footer(text=f"Sigmoidian Daily Reminder · {player_note}")
    return embed


# ── Persistent interactive view ────────────────────────────────────────────────

class ReminderView(discord.ui.View):
    """
    Buttons attached to every daily reminder message.

    Uses stable custom_ids + bot.add_view() registration so interactions are
    handled correctly even after a bot restart — no in-memory state required.
    All callbacks run on the bot's asyncio event loop; no threading concerns.
    """

    def __init__(self):
        super().__init__(timeout=None)  # persistent — never expires

    @discord.ui.button(
        label="🔗 Start a Game",
        style=discord.ButtonStyle.success,
        custom_id="reminder:start_game",
    )
    async def start_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return

        gid = str(interaction.guild_id)
        cid = str(interaction.channel_id)

        existing = await db.get_active_chain(gid, cid)
        if existing:
            await interaction.followup.send(
                f"A game is already running here (Game #{existing['id']})!\n"
                "Use `/chain play <word>` to jump in.",
                ephemeral=True,
            )
            return

        game_id = await db.create_chain_game(
            gid, cid, "last", started_by=str(interaction.user.id)
        )
        await db.upsert_user(str(interaction.user.id), gid, interaction.user.display_name)

        embed = discord.Embed(
            title=f"🔗 Word Chain Started — Game #{game_id}",
            colour=CHAIN_COLOR,
            description=(
                f"**{interaction.user.display_name}** kicked off today's game!\n\n"
                "**How to play**\n"
                "• `/chain play <word>` — add a 5-letter word to the chain\n"
                "• Each word must start with the **last letter** of the previous word\n"
                "  e.g. `SENSE` → `ENTER` → `ROVER` → `RANGE` → …\n"
                "• Words must be in the dictionary · no repeats · anyone can join!\n\n"
                "**Scoring**: ★☆☆ Common = +1pt · ★★☆ Moderate = +2pts · ★★★ Rare = +3pts\n"
                "• **+2 milestone bonus** every 5 words in the chain"
            ),
        )
        embed.set_footer(text=f"Game #{game_id} | Mode: last letter | /chain end to stop")

        try:
            await interaction.channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException) as exc:
            log.warning("ReminderView: cannot announce game in channel %s: %s", cid, exc)

        await interaction.followup.send(
            f"✅ Game #{game_id} started! Use `/chain play <word>` to jump in.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="🏆 Leaderboard",
        style=discord.ButtonStyle.primary,
        custom_id="reminder:leaderboard",
    )
    async def leaderboard(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return

        rows = await db.get_leaderboard(str(interaction.guild_id), limit=10)
        if not rows:
            await interaction.followup.send(
                "No players on the leaderboard yet — start a game and be the first!",
                ephemeral=True,
            )
            return

        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, row in enumerate(rows):
            prefix  = medals[i] if i < 3 else f"**{i + 1}.**"
            name    = row.get("username") or f"<@{row['user_id']}>"
            pts     = row.get("chain_points", 0)
            words   = row.get("chain_words", 0)
            longest = row.get("longest_chain", 0)
            lines.append(
                f"{prefix} **{name}** — {pts} pts · {words} words · best chain: {longest}"
            )

        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} Leaderboard",
            description="\n".join(lines),
            colour=STATS_COLOR,
        )
        embed.set_footer(text="Use /stats for your full personal stats")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="📊 My Stats",
        style=discord.ButtonStyle.secondary,
        custom_id="reminder:my_stats",
    )
    async def my_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return

        stats = await db.get_user_stats(
            str(interaction.user.id), str(interaction.guild_id)
        )
        if not stats or stats.get("chain_words", 0) == 0:
            await interaction.followup.send(
                "You haven't played yet!\nClick **Start a Game** or use `/chain start` to begin.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Stats",
            colour=STATS_COLOR,
        )
        embed.add_field(name="Points",       value=str(stats.get("chain_points", 0)),  inline=True)
        embed.add_field(name="Words Played", value=str(stats.get("chain_words", 0)),   inline=True)
        embed.add_field(name="Best Chain",   value=str(stats.get("longest_chain", 0)), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)


# ── Cog ────────────────────────────────────────────────────────────────────────

class ReminderCog(commands.Cog):
    remind = SlashCommandGroup(
        "remind",
        "Daily reminder configuration — server admins only",
        default_member_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        # Register the persistent view once so Discord routes button interactions
        # to this handler even after a bot restart (no in-memory state needed).
        bot.add_view(ReminderView())
        self._daily_task.start()

    def cog_unload(self):
        self._daily_task.cancel()

    # ── Background task ────────────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def _daily_task(self):
        try:
            await self._check_and_send()
        except Exception as exc:
            log.error("Daily reminder task crashed: %s", exc, exc_info=True)

    @_daily_task.before_loop
    async def _before_daily_task(self):
        await self.bot.wait_until_ready()

    async def _check_and_send(self):
        guilds_cfg = await db.get_all_reminder_guilds()
        if not guilds_cfg:
            return

        now_utc = datetime.now(tz=ZoneInfo("UTC"))

        for cfg in guilds_cfg:
            guild_id   = cfg["guild_id"]
            channel_id = cfg["reminder_channel_id"]
            tz_name    = cfg.get("timezone") or "UTC"
            last_date  = cfg.get("last_reminder_date")

            try:
                tz = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                log.warning(
                    "Unknown timezone %r for guild %s — falling back to UTC",
                    tz_name, guild_id,
                )
                tz = ZoneInfo("UTC")

            now_local = now_utc.astimezone(tz)
            today_str = now_local.strftime("%Y-%m-%d")

            # Only fire within the 6:00–6:04 window, once per calendar day
            if now_local.hour != _REMINDER_HOUR or now_local.minute >= _REMINDER_WINDOW:
                continue
            if last_date == today_str:
                continue

            # Mark sent before async work to prevent double-send on reconnect
            await db.update_last_reminder_date(guild_id, today_str)

            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(int(channel_id))
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    log.warning(
                        "Reminder: cannot access channel %s for guild %s",
                        channel_id, guild_id,
                    )
                    continue

            await self._send_reminder(channel.guild, channel, now_local)

    # ── Core send logic ────────────────────────────────────────────────────────

    async def _send_reminder(
        self,
        guild: discord.Guild,
        channel: discord.abc.Messageable,
        now_local: datetime,
    ) -> None:
        gid = str(guild.id)

        # Fetch all data concurrently — safe: each coroutine is independent
        top_players, active_games, players = await asyncio.gather(
            db.get_leaderboard(gid, limit=3),
            db.get_active_chains_for_guild(gid),
            db.get_all_time_players(gid),   # all users who ever played ≥ 1 word
        )

        today_display = f"{now_local.strftime('%B')} {now_local.day}"
        word_fact     = get_word_fact(now_local.month, now_local.day)
        hook          = random.choice(_HOOKS)

        embed = _build_reminder_embed(
            guild_name    = guild.name,
            word_fact     = word_fact,
            today_display = today_display,
            top_players   = top_players,
            active_games  = active_games,
            hook          = hook,
            player_count  = len(players),
        )

        # Deduplicate user_ids across both user_stats and word_log sources
        user_ids       = list(dict.fromkeys(p["user_id"] for p in players))
        mention_chunks = _chunk_mentions(user_ids)

        view = ReminderView()

        try:
            if mention_chunks:
                # First chunk carries the embed and action buttons
                await channel.send(content=mention_chunks[0], embed=embed, view=view)
                # Overflow pages — rare, only when the server has many players
                for i, chunk in enumerate(mention_chunks[1:], start=2):
                    await channel.send(
                        content=f"*(continued — page {i})* {chunk} — today's word chain awaits! 🔤"
                    )
            else:
                # No players yet — send embed + buttons without any mentions
                await channel.send(
                    content="📣 Daily word challenge is live!",
                    embed=embed,
                    view=view,
                )
        except (discord.Forbidden, discord.HTTPException) as exc:
            log.warning(
                "Cannot send reminder to %s (#%s): %s",
                guild.name, getattr(channel, "id", "?"), exc,
            )
            return

        log.info("Daily reminder sent → %s (#%s)", guild.name, getattr(channel, "id", "?"))

    # ── /remind channel ────────────────────────────────────────────────────────

    @remind.command(name="channel", description="Set the channel where daily reminders are posted")
    async def set_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.Option(
            discord.TextChannel,
            "Channel where reminders will be posted",
            required=True,
        ),  # type: ignore[valid-type]
    ):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this inside a server.", ephemeral=True)
            return

        await db.set_reminder_channel(str(ctx.guild.id), str(channel.id))

        cfg     = await db.get_guild_settings(str(ctx.guild.id))
        tz_name = (cfg.get("timezone") if cfg else None) or "UTC"

        embed = discord.Embed(
            title="✅ Reminder Channel Set",
            colour=discord.Colour.green(),
            description=(
                f"Daily reminders will be posted in {channel.mention}.\n\n"
                f"Current timezone: **{tz_name}** — reminders fire at **6:00 AM** in that zone.\n"
                "Use `/remind timezone` to change the timezone.\n"
                "Use `/remind test` to preview a reminder right now."
            ),
        )
        await ctx.followup.send(embed=embed, ephemeral=True)

    # ── /remind timezone ───────────────────────────────────────────────────────

    @remind.command(name="timezone", description="Set the timezone for 6 AM daily reminders")
    async def set_timezone(
        self,
        ctx: discord.ApplicationContext,
        timezone: discord.Option(
            str,
            "IANA timezone name (e.g. America/New_York, Europe/London, Asia/Kolkata)",
            required=True,
        ),  # type: ignore[valid-type]
    ):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this inside a server.", ephemeral=True)
            return

        try:
            tz        = ZoneInfo(timezone)
            now_local = datetime.now(tz=tz)
        except ZoneInfoNotFoundError:
            await ctx.followup.send(
                f"❌ Unknown timezone: `{timezone}`\n"
                "Use a valid IANA timezone name, e.g.:\n"
                "• `America/New_York`\n"
                "• `Europe/London`\n"
                "• `Asia/Kolkata`\n"
                "• `Australia/Sydney`\n"
                "• `UTC`",
                ephemeral=True,
            )
            return

        await db.set_reminder_timezone(str(ctx.guild.id), timezone)

        time_str = now_local.strftime("%I:%M %p")
        date_str = now_local.strftime("%A, %B %d")

        embed = discord.Embed(
            title="✅ Timezone Set",
            colour=discord.Colour.green(),
            description=(
                f"Timezone set to **{timezone}**.\n\n"
                f"Current local time there: **{time_str}** ({date_str})\n\n"
                "Daily reminders will fire at **6:00 AM** in this timezone.\n"
                "Use `/remind channel` to set or change the reminder channel."
            ),
        )
        await ctx.followup.send(embed=embed, ephemeral=True)

    # ── /remind off ────────────────────────────────────────────────────────────

    @remind.command(name="off", description="Disable daily reminders for this server")
    async def off(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this inside a server.", ephemeral=True)
            return

        await db.disable_guild_reminder(str(ctx.guild.id))
        await ctx.followup.send(
            "🔕 Daily reminders disabled. Use `/remind channel` to re-enable.",
            ephemeral=True,
        )

    # ── /remind test ───────────────────────────────────────────────────────────

    @remind.command(name="test", description="Send a test reminder to the configured channel right now")
    async def test(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this inside a server.", ephemeral=True)
            return

        cfg = await db.get_guild_settings(str(ctx.guild.id))
        if not cfg or not cfg.get("reminder_channel_id"):
            await ctx.followup.send(
                "❌ No reminder channel configured.\n"
                "Use `/remind channel #channel` to set one first.",
                ephemeral=True,
            )
            return

        raw_id  = cfg["reminder_channel_id"]
        channel = ctx.guild.get_channel(int(raw_id))
        if channel is None:
            try:
                channel = await ctx.guild.fetch_channel(int(raw_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
                await ctx.followup.send(
                    f"❌ Could not access reminder channel (ID `{raw_id}`).\n"
                    f"Error: `{exc}`\n\n"
                    "Make sure the bot has **View Channel** permission there, or "
                    "use `/remind channel #channel` to set a new one.",
                    ephemeral=True,
                )
                return

        tz_name = cfg.get("timezone") or "UTC"
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")

        now_local = datetime.now(tz=tz)
        await self._send_reminder(ctx.guild, channel, now_local)
        await ctx.followup.send(
            f"✅ Test reminder sent to {channel.mention}.", ephemeral=True
        )

    # ── /remind status ─────────────────────────────────────────────────────────

    @remind.command(name="status", description="Show current reminder configuration")
    async def status_cmd(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this inside a server.", ephemeral=True)
            return

        cfg   = await db.get_guild_settings(str(ctx.guild.id))
        embed = discord.Embed(title="⏰ Reminder Configuration", colour=STATS_COLOR)

        if cfg and cfg.get("reminder_channel_id"):
            tz_name = cfg.get("timezone") or "UTC"
            last    = cfg.get("last_reminder_date") or "never"
            try:
                tz        = ZoneInfo(tz_name)
                now_local = datetime.now(tz=tz)
                local_str = now_local.strftime("%I:%M %p")
            except ZoneInfoNotFoundError:
                local_str = "unknown"

            embed.description = (
                f"**Status:** ✅ Active\n"
                f"**Channel:** <#{cfg['reminder_channel_id']}>\n"
                f"**Timezone:** {tz_name} (currently {local_str})\n"
                f"**Fires at:** 6:00 AM {tz_name}\n"
                f"**Last sent:** {last}"
            )
        else:
            embed.description = (
                "**Status:** 🔕 Not configured\n\n"
                "Set up with:\n"
                "• `/remind channel #channel` — choose where reminders go\n"
                "• `/remind timezone America/New_York` — set your local timezone\n\n"
                "Reminders will not be sent until a channel is configured."
            )

        await ctx.followup.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(ReminderCog(bot))

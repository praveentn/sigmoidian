import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands
from discord import SlashCommandGroup

from utils import database as db
from utils import definitions as worddef
from utils.display import (
    chain_status_embed, hint_embed, chain_end_embed,
    chain_recap_embed, top_chains_embed, _remaining_indicator,
    ERROR_COLOR, CHAIN_COLOR, OK_COLOR, STATS_COLOR,
)
from utils.words import is_valid, add_word, remove_word, word_count, remaining_for_letter, get_hints, closest_word
from game.chain import ChainGame, VALID_MODES

log = logging.getLogger("sigmoidian.chain")

_channel_locks: dict[tuple[str, str], asyncio.Lock] = defaultdict(asyncio.Lock)
_user_last_play: dict[str, float] = {}
_PLAY_COOLDOWN = 1.5

# Channels with an active game — populated on ready, updated when games start/end.
_active_game_channels: set[tuple[str, str]] = set()


async def _try_channel_send(
    channel: discord.abc.Messageable,
    content: str,
    embed: discord.Embed,
    view: discord.ui.View | None = None,
) -> bool:
    try:
        await channel.send(content, embed=embed, view=view)
        return True
    except (discord.Forbidden, discord.HTTPException) as exc:
        log.warning("Cannot send to channel %s: %s", getattr(channel, "id", "?"), exc)
        return False


# ── Paginated views ────────────────────────────────────────────────────────────

class ChainRecapView(discord.ui.View):
    WORDS_PER_PAGE = 50

    def __init__(self, words: list[str], game_id: int):
        super().__init__(timeout=300)
        self.words       = words
        self.game_id     = game_id
        self.page        = 0
        self.total_pages = max(1, (len(words) + self.WORDS_PER_PAGE - 1) // self.WORDS_PER_PAGE)
        self._sync()

    def _sync(self):
        self.prev_btn.disabled = (self.page == 0)
        self.next_btn.disabled = (self.page >= self.total_pages - 1)

    def build_embed(self) -> discord.Embed:
        return chain_recap_embed(self.words, self.game_id, self.page, self.WORDS_PER_PAGE)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page -= 1
        self._sync()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        self._sync()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class LetterWordsView(discord.ui.View):
    WORDS_PER_PAGE = 15

    def __init__(self, letter: str, moves: list[dict], remaining: int, game_id: int):
        super().__init__(timeout=300)
        self.letter      = letter.upper()
        self.moves       = moves
        self.remaining   = remaining
        self.game_id     = game_id
        self.page        = 0
        self.total_pages = max(1, (len(moves) + self.WORDS_PER_PAGE - 1) // self.WORDS_PER_PAGE)
        self._sync()

    def _sync(self):
        self.prev_btn.disabled = (self.page == 0)
        self.next_btn.disabled = (self.page >= self.total_pages - 1)

    def build_embed(self) -> discord.Embed:
        start      = self.page * self.WORDS_PER_PAGE
        end        = min(start + self.WORDS_PER_PAGE, len(self.moves))
        page_moves = self.moves[start:end]

        embed = discord.Embed(
            title=f"🔤 Words Starting with {self.letter} — Game #{self.game_id}",
            colour=CHAIN_COLOR,
        )
        if page_moves:
            lines = [f"`{m['word']}` — **{m['username']}**" for m in page_moves]
            embed.add_field(
                name=f"Words {start + 1}–{end} of {len(self.moves)}",
                value="\n".join(lines),
                inline=False,
            )
        else:
            embed.add_field(name="Used (0)", value="None yet.", inline=False)

        embed.add_field(
            name="Still available",
            value=_remaining_indicator(self.remaining, self.letter),
            inline=False,
        )
        page_note = f" | Page {self.page + 1}/{self.total_pages}" if self.total_pages > 1 else ""
        embed.set_footer(
            text=f"Game #{self.game_id} | {len(self.moves)} used · {self.remaining} remaining{page_note}"
        )
        return embed

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page -= 1
        self._sync()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.page += 1
        self._sync()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


# ── Modal ──────────────────────────────────────────────────────────────────────

class AddWordModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Add Word to Dictionary")
        self.add_item(
            discord.ui.InputText(
                label="5-letter word",
                placeholder="e.g. CRANE",
                min_length=5,
                max_length=5,
                style=discord.InputTextStyle.short,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        word = self.children[0].value.strip().upper()
        if len(word) != 5 or not word.isalpha():
            await interaction.response.send_message(
                f"❌ `{word}` is not a valid 5-letter alphabetic word.", ephemeral=True
            )
            return
        added = add_word(word)
        if added:
            await interaction.response.send_message(
                f"✅ `{word}` added to the dictionary. Total: **{word_count()}** words.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"`{word}` is already in the dictionary ({word_count()} words).",
                ephemeral=True,
            )


# ── Persistent game views ──────────────────────────────────────────────────────

class GameView(discord.ui.View):
    """
    Persistent buttons attached to game-start and each play response.
    Registered with bot.add_view() so interactions survive bot restarts.
    All callbacks read live game state from DB — no stored state required.
    """

    def __init__(self):
        super().__init__(timeout=None)

    # ── Row 0: player actions ──────────────────────────────────────────────────

    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.secondary, custom_id="game:status", row=0)
    async def status_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return
        row = await db.get_active_chain(str(interaction.guild_id), str(interaction.channel_id))
        if not row:
            await interaction.followup.send("No active chain game here.", ephemeral=True)
            return
        game  = ChainGame.from_db(row)
        moves = await db.get_chain_moves(game.game_id)
        rem   = (remaining_for_letter(game.next_letter, set(game.words_used)) if game.next_letter else None)
        embed = chain_status_embed(game.words_used, game.next_letter or "any letter", moves, game.game_id, rem, game.game_mode)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="💡 Hint", style=discord.ButtonStyle.secondary, custom_id="game:hint", row=0)
    async def hint_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return
        row = await db.get_active_chain(str(interaction.guild_id), str(interaction.channel_id))
        if not row:
            await interaction.followup.send("No active game here.", ephemeral=True)
            return
        game = ChainGame.from_db(row)
        if not game.next_letter:
            await interaction.followup.send("Game just started — any valid 5-letter word works!", ephemeral=True)
            return
        used  = set(game.words_used)
        hints = get_hints(game.next_letter, used)
        rem   = remaining_for_letter(game.next_letter, used)
        embed = hint_embed(game.next_letter, hints, rem, game.game_id, interaction.user.display_name)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏆 Leaderboard", style=discord.ButtonStyle.primary, custom_id="game:leaderboard", row=0)
    async def leaderboard_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return
        rows = await db.get_leaderboard(str(interaction.guild_id), limit=10)
        if not rows:
            await interaction.followup.send("No players yet — start playing!", ephemeral=True)
            return
        medals = ["🥇", "🥈", "🥉"]
        lines  = [
            f"{medals[i] if i < 3 else f'**{i+1}.**'} **{r.get('username') or f'<@{r[\"user_id\"]}>'}**"
            f" — {r.get('chain_points', 0)} pts · {r.get('chain_words', 0)} words"
            for i, r in enumerate(rows)
        ]
        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} Leaderboard",
            description="\n".join(lines),
            colour=STATS_COLOR,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 My Stats", style=discord.ButtonStyle.secondary, custom_id="game:my_stats", row=0)
    async def my_stats_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return
        stats = await db.get_user_stats(str(interaction.user.id), str(interaction.guild_id))
        if not stats or stats.get("chain_words", 0) == 0:
            await interaction.followup.send(
                "You haven't played yet! Type a 5-letter word in the game channel to start.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(title=f"📊 {interaction.user.display_name}'s Stats", colour=STATS_COLOR)
        embed.add_field(name="Points",       value=str(stats.get("chain_points", 0)),  inline=True)
        embed.add_field(name="Words Played", value=str(stats.get("chain_words", 0)),   inline=True)
        embed.add_field(name="Best Chain",   value=str(stats.get("longest_chain") or "—"), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── Row 1: admin actions ───────────────────────────────────────────────────

    @discord.ui.button(label="🔚 End Game", style=discord.ButtonStyle.danger, custom_id="game:end", row=1)
    async def end_game_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return

        gid = str(interaction.guild_id)
        cid = str(interaction.channel_id)
        row = await db.get_active_chain(gid, cid)
        if not row:
            await interaction.followup.send("No active game to end.", ephemeral=True)
            return

        started_by = row.get("started_by") or ""
        is_starter = bool(started_by) and str(interaction.user.id) == started_by
        is_mod     = interaction.user.guild_permissions.manage_messages
        if not is_starter and not is_mod:
            await interaction.followup.send(
                "⚠️ Only the player who started this game or a moderator (Manage Messages) can end it.",
                ephemeral=True,
            )
            return

        game  = ChainGame.from_db(row)
        moves = await db.get_chain_moves(game.game_id)
        await db.update_chain_game(game.game_id, game.words_used, game.next_letter or "", "ended")

        seen: set[str] = set()
        for m in moves:
            if m["user_id"] not in seen:
                seen.add(m["user_id"])
                await db.update_longest_chain(m["user_id"], gid, game.chain_length)

        tally: dict[str, list[str]] = {}
        for m in moves:
            tally.setdefault(m["username"], []).append(m["word"])

        embed = chain_end_embed(game.game_id, game.chain_length, tally)
        _active_game_channels.discard((gid, cid))

        try:
            await interaction.channel.send(embed=embed, view=PostGameView())
        except (discord.Forbidden, discord.HTTPException):
            pass

        if game.chain_length > 0:
            recap_view = ChainRecapView(game.words_used, game.game_id)
            try:
                await interaction.channel.send(
                    "📜 **Final Chain Recap:**",
                    embed=recap_view.build_embed(),
                    view=recap_view if recap_view.total_pages > 1 else None,
                )
            except (discord.Forbidden, discord.HTTPException):
                pass

        await interaction.followup.send(f"✅ Game #{game.game_id} ended.", ephemeral=True)

    @discord.ui.button(label="➕ Add Word", style=discord.ButtonStyle.secondary, custom_id="game:add_word", row=1)
    async def add_word_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Only works inside a server.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "⚠️ Adding words requires **Manage Server** permission.", ephemeral=True
            )
            return
        await interaction.response.send_modal(AddWordModal())


class PostGameView(discord.ui.View):
    """Shown when a game ends — lets admins start a new one without a command."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔗 Start New Game", style=discord.ButtonStyle.success, custom_id="game:start_new")
    async def start_new_btn(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.guild:
            await interaction.followup.send("Only works inside a server.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.followup.send(
                "⚠️ Only server admins can start a new game. Ask an admin!", ephemeral=True
            )
            return

        gid = str(interaction.guild_id)
        cid = str(interaction.channel_id)
        existing = await db.get_active_chain(gid, cid)
        if existing:
            await interaction.followup.send(
                f"A game is already running here (Game #{existing['id']})!\n"
                "Just type a 5-letter word in the channel to play.",
                ephemeral=True,
            )
            return

        game_id = await db.create_chain_game(gid, cid, "last", started_by=str(interaction.user.id))
        _active_game_channels.add((gid, cid))
        await db.upsert_user(str(interaction.user.id), gid, interaction.user.display_name)

        embed = discord.Embed(
            title=f"🔗 Word Chain Started — Game #{game_id}",
            colour=CHAIN_COLOR,
            description=(
                f"**{interaction.user.display_name}** started a new game!\n\n"
                "**How to play**\n"
                "• Just **type a 5-letter word** in this channel!\n"
                "• Each word must start with the **last letter** of the previous word\n"
                "  e.g. `SENSE` → `ENTER` → `ROVER` → `RANGE` → …\n"
                "• Words must be in the dictionary · no repeats · anyone can join!\n\n"
                "**Scoring**: ★☆☆ Common = +1pt · ★★☆ Moderate = +2pts · ★★★ Rare = +3pts\n"
                "• **+2 milestone bonus** every 5 words"
            ),
        )
        embed.set_footer(text=f"Game #{game_id} | Mode: last letter | tap 🔚 End Game to stop")
        try:
            await interaction.channel.send(embed=embed, view=GameView())
        except (discord.Forbidden, discord.HTTPException) as exc:
            log.warning("PostGameView: cannot announce game in %s: %s", cid, exc)
        await interaction.followup.send(f"✅ Game #{game_id} started!", ephemeral=True)


# ───────────────────────────────────────────────────────────────────────────────

_MODE_LABELS = {
    "last":   "last letter",
    "random": "random letter (chosen from each word)",
    "2nd":    "2nd letter",
    "3rd":    "3rd letter (middle)",
    "4th":    "4th letter",
}


class ChainCog(commands.Cog):
    chain = SlashCommandGroup("chain", "Word-chain multiplayer game commands")

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    # ── Startup ────────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        channels = await db.get_all_active_game_channels()
        _active_game_channels.clear()
        _active_game_channels.update(channels)
        log.info("Active game channel cache populated: %d channel(s)", len(channels))
        self.bot.add_view(GameView())
        self.bot.add_view(PostGameView())
        log.info("Persistent game views registered")

    # ── Core play logic ────────────────────────────────────────────────────────

    async def _process_play(
        self,
        gid: str,
        cid: str,
        uid: str,
        username: str,
        word: str,
        ctx_or_msg,
    ) -> None:
        is_slash = isinstance(ctx_or_msg, discord.ApplicationContext)
        channel  = ctx_or_msg.channel

        async def send(embed=None, content=None, ephemeral=False, view=None):
            if is_slash:
                await ctx_or_msg.followup.send(
                    content=content, embed=embed, ephemeral=ephemeral,
                    view=(view if not ephemeral else None),
                )
            else:
                if ephemeral:
                    try:
                        await ctx_or_msg.add_reaction("⏳")
                    except discord.HTTPException:
                        pass
                else:
                    await ctx_or_msg.reply(content=content, embed=embed, view=view)

        # ── Rate limit ─────────────────────────────────────────────────────────
        rk   = f"{uid}:{gid}"
        now  = time.monotonic()
        wait = _PLAY_COOLDOWN - (now - _user_last_play.get(rk, 0))
        if wait > 0:
            await send(content=f"⏳ Wait **{wait:.1f}s** before playing again.", ephemeral=True)
            return
        _user_last_play[rk] = now

        # ── Serialise concurrent plays per channel ─────────────────────────────
        async with _channel_locks[(gid, cid)]:
            row = await db.get_active_chain(gid, cid)
            if not row:
                _active_game_channels.discard((gid, cid))
                if is_slash:
                    await send(content="No active chain game here. Use `/chain start` to begin.")
                return

            game  = ChainGame.from_db(row)
            error = game.validate(word)
            if error:
                embed = discord.Embed(title="Invalid Word", colour=ERROR_COLOR)
                suggestion = None
                if (
                    "not in the word list" in error
                    and game.next_letter
                    and word[0] == game.next_letter
                ):
                    suggestion = closest_word(word, game.next_letter, set(game.words_used))
                desc = f"{ctx_or_msg.author.mention} — {error}"
                if suggestion:
                    desc += f"\n💡 Did you mean **{suggestion}**?"
                embed.description = desc
                if game.next_letter:
                    embed.set_footer(text=f"Next word must start with: {game.next_letter}")
                await send(embed=embed)
                return

            total, base_pts, tier_label, stars = game.play(word)

            await db.update_chain_game(game.game_id, game.words_used, game.next_letter or "")
            await db.add_chain_move(game.game_id, uid, username, word)
            await db.upsert_user(uid, gid, username)

            moves = await db.get_chain_moves(game.game_id)

            # ── Streak bonus ───────────────────────────────────────────────────
            streak_count = 0
            for m in reversed(moves[:-1]):
                if m["user_id"] == uid:
                    streak_count += 1
                else:
                    break
            streak_bonus = 1 if streak_count >= 1 else 0
            total_final  = total + streak_bonus

            # ── Spotlight bonus ────────────────────────────────────────────────
            spotlight_bonus = 0
            try:
                spotlight = await db.get_spotlight(gid)
                today_str = datetime.now(tz=ZoneInfo("UTC")).strftime("%Y-%m-%d")
                if (spotlight
                        and spotlight.get("spotlight_date") == today_str
                        and spotlight.get("user_id") == uid
                        and not spotlight.get("claimed")):
                    spotlight_bonus = 5
                    await db.claim_spotlight(gid)
            except Exception:
                pass

            total_awarded = total_final + spotlight_bonus
            await db.increment_stat(uid, gid, "chain_points", total_awarded)
            await db.increment_stat(uid, gid, "chain_words")
            await db.log_word(gid, uid, word)

            user_stats = await db.get_user_stats(uid, gid)
            if user_stats is not None and game.chain_length > (user_stats.get("longest_chain") or 0):
                await db.update_longest_chain(uid, gid, game.chain_length)

            remaining = (
                remaining_for_letter(game.next_letter, set(game.words_used))
                if game.next_letter else None
            )

            # ── Auto-end: no words remain ──────────────────────────────────────
            if remaining == 0:
                _active_game_channels.discard((gid, cid))
                await db.update_chain_game(
                    game.game_id, game.words_used, game.next_letter or "", "ended"
                )
                seen: set[str] = set()
                for m in moves:
                    if m["user_id"] not in seen:
                        seen.add(m["user_id"])
                        await db.update_longest_chain(m["user_id"], gid, game.chain_length)

                milestone_note  = " *(+2 milestone bonus!)*" if total > base_pts else ""
                streak_note     = f" 🔥 *+1 streak ({streak_count + 1} in a row!)*" if streak_bonus else ""
                spotlight_note  = f" 🌟 *+{spotlight_bonus} spotlight bonus!*" if spotlight_bonus else ""
                embed = discord.Embed(
                    title=f"🏁 Chain Complete — Game #{game.game_id}",
                    colour=discord.Colour.orange(),
                    description=(
                        f"✅ **{username}** played `{word}` "
                        f"({stars} **+{total_awarded} pt{'s' if total_awarded != 1 else ''}**)"
                        f"{milestone_note}{streak_note}{spotlight_note}\n\n"
                        f"💀 **No more words start with `{game.next_letter}`** — dictionary exhausted!\n"
                        f"Chain ends at **{game.chain_length}** word(s). Well played!\n\n"
                        "Tap **🔗 Start New Game** below to play again!"
                    ),
                )
                await send(embed=embed, view=PostGameView())
                if game.chain_length > 0:
                    recap_view = ChainRecapView(game.words_used, game.game_id)
                    await _try_channel_send(
                        channel, "📜 **Final Chain Recap:**",
                        recap_view.build_embed(),
                        recap_view if recap_view.total_pages > 1 else None,
                    )
                asyncio.create_task(self._post_definition(channel, word))
                return

            # ── Normal play response ───────────────────────────────────────────
            embed = chain_status_embed(
                game.words_used, game.next_letter or "?", moves, game.game_id, remaining, game.game_mode
            )
            milestone_note = " *(+2 milestone bonus!)*" if total > base_pts else ""
            streak_note    = f" 🔥 *+1 streak ({streak_count + 1} in a row!)*" if streak_bonus else ""
            spotlight_note = f" 🌟 *+{spotlight_bonus} spotlight bonus!*" if spotlight_bonus else ""
            desc = (
                f"✅ **{username}** played `{word}` "
                f"— {stars} **+{total_awarded} pt{'s' if total_awarded != 1 else ''}**"
                f"{milestone_note}{streak_note}{spotlight_note}"
            )
            if stars == "★★★":
                desc += f"\n✨ **Rare word spotlight!** `{word}` — {tier_label}, {base_pts} base pts."
            embed.description = desc
            await send(embed=embed, view=GameView())

        # ── Milestone recap (outside lock) ─────────────────────────────────────
        if game.chain_length % 100 == 0:
            recap_view = ChainRecapView(game.words_used, game.game_id)
            await _try_channel_send(
                channel,
                f"🎉 **{game.chain_length}-word milestone!** Here's the chain so far:",
                recap_view.build_embed(),
                recap_view if recap_view.total_pages > 1 else None,
            )

        asyncio.create_task(self._post_definition(channel, word))

    async def _post_definition(self, channel: discord.abc.Messageable, word: str) -> None:
        try:
            defn = await db.get_word_definition(word)
            if defn and defn.get("meaning"):
                text = worddef.format_definition(word, defn)
                await channel.send(text)
        except Exception as exc:
            log.warning("Definition post failed for %s: %s", word, exc)

    # ── Direct message listener ────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        content = message.content.strip()
        if not (len(content) == 5 and content.isalpha()):
            return
        gid = str(message.guild.id)
        cid = str(message.channel.id)
        if (gid, cid) not in _active_game_channels:
            return
        await self._process_play(
            gid, cid,
            str(message.author.id),
            message.author.display_name,
            content.upper(),
            message,
        )

    # ── /chain start ───────────────────────────────────────────────────────────

    @chain.command(name="start", description="Start a word-chain game in this channel")
    async def start(
        self,
        ctx: discord.ApplicationContext,
        mode: discord.Option(
            str,
            "How the next letter is chosen (default: last letter of each word)",
            required=False,
            default="last",
            choices=["last", "random", "2nd", "3rd", "4th"],
        ),  # type: ignore[valid-type]
    ):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        gid, cid = str(ctx.guild.id), str(ctx.channel.id)
        existing = await db.get_active_chain(gid, cid)
        if existing:
            game  = ChainGame.from_db(existing)
            moves = await db.get_chain_moves(game.game_id)
            rem   = remaining_for_letter(game.next_letter, set(game.words_used)) if game.next_letter else None
            embed = chain_status_embed(game.words_used, game.next_letter or "?", moves, game.game_id, rem, game.game_mode)
            embed.description = "⚠️ A chain game is already running in this channel!"
            await ctx.followup.send(embed=embed, view=GameView())
            return

        game_id = await db.create_chain_game(gid, cid, mode, started_by=str(ctx.author.id))
        await db.upsert_user(str(ctx.author.id), gid, ctx.author.display_name)

        mode_desc = _MODE_LABELS.get(mode, mode)
        embed = discord.Embed(
            title=f"🔗 Word Chain Started — Game #{game_id}",
            colour=CHAIN_COLOR,
            description=(
                "**How to play**\n"
                "• Just **type a 5-letter word** in this channel to play!\n"
                f"• Each word must start with the **{mode_desc}** of the previous word\n"
                "  e.g. `SENSE` → `ENTER` → `ROVER` → `RANGE` → …\n"
                "• Words must exist in the dictionary · no repeats · any player can join!\n\n"
                "**Scoring**\n"
                "• ★☆☆ **Common** word = **+1 pt**  ·  ★★☆ **Moderate** = **+2 pts**  ·  ★★★ **Rare** = **+3 pts**\n"
                "• **+2 milestone bonus** every 5 words in the chain\n\n"
                "The first player can start with **any** valid 5-letter word.\n"
                "Use the buttons below for status, hints, leaderboard, and more."
            ),
        )
        embed.set_footer(text=f"Game #{game_id} | Mode: {mode_desc} | tap 🔚 End Game to stop")
        await ctx.followup.send(embed=embed, view=GameView())
        _active_game_channels.add((gid, cid))

    # ── /chain play ────────────────────────────────────────────────────────────

    @chain.command(name="play", description="Play a word in the active chain game (or just type it in the channel!)")
    async def play(
        self,
        ctx: discord.ApplicationContext,
        word: discord.Option(str, "Your 5-letter word", required=True),  # type: ignore[valid-type]
    ):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return
        await self._process_play(
            str(ctx.guild.id),
            str(ctx.channel.id),
            str(ctx.author.id),
            ctx.author.display_name,
            word.strip().upper(),
            ctx,
        )

    # ── /chain status ──────────────────────────────────────────────────────────

    @chain.command(name="status", description="Show the current word chain")
    async def status(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        row = await db.get_active_chain(str(ctx.guild.id), str(ctx.channel.id))
        if not row:
            await ctx.followup.send("No active chain game here. Use `/chain start` to begin.")
            return

        game  = ChainGame.from_db(row)
        moves = await db.get_chain_moves(game.game_id)
        rem   = (
            remaining_for_letter(game.next_letter, set(game.words_used))
            if game.next_letter else None
        )
        embed = chain_status_embed(
            game.words_used, game.next_letter or "any letter", moves, game.game_id, rem, game.game_mode
        )
        await ctx.followup.send(embed=embed, view=GameView())

    # ── /chain words ───────────────────────────────────────────────────────────

    @chain.command(
        name="words",
        description="List words used starting with a specific letter, plus how many remain",
    )
    async def words_cmd(
        self,
        ctx: discord.ApplicationContext,
        letter: discord.Option(
            str, "Single letter (A–Z)", required=True, min_length=1, max_length=1
        ),  # type: ignore[valid-type]
    ):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        letter = letter.strip().upper()
        if not letter.isalpha():
            await ctx.followup.send("Please provide a single letter (A–Z).", ephemeral=True)
            return

        row = await db.get_active_chain(str(ctx.guild.id), str(ctx.channel.id))
        if not row:
            await ctx.followup.send("No active chain game here. Use `/chain start` to begin.")
            return

        game  = ChainGame.from_db(row)
        moves = await db.get_chain_moves(game.game_id)

        letter_moves = [m for m in moves if m["word"].upper().startswith(letter)]
        remaining    = remaining_for_letter(letter, set(game.words_used))

        view  = LetterWordsView(letter, letter_moves, remaining, game.game_id)
        await ctx.followup.send(
            embed=view.build_embed(),
            view=view if view.total_pages > 1 else None,
        )

    # ── /chain hint ────────────────────────────────────────────────────────────

    @chain.command(
        name="hint",
        description="Ask for a hint — reveals one letter of a valid word (visible to all)",
    )
    async def hint(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        row = await db.get_active_chain(str(ctx.guild.id), str(ctx.channel.id))
        if not row:
            await ctx.followup.send("No active chain game here. Use `/chain start` to begin.")
            return

        game = ChainGame.from_db(row)
        if not game.next_letter:
            await ctx.followup.send("The game just started — any valid 5-letter word works!")
            return

        used   = set(game.words_used)
        hints  = get_hints(game.next_letter, used)
        rem    = remaining_for_letter(game.next_letter, used)
        embed  = hint_embed(game.next_letter, hints, rem, game.game_id, ctx.author.display_name)
        await ctx.followup.send(embed=embed)

    # ── /chain top ─────────────────────────────────────────────────────────────

    @chain.command(name="top", description="Show the longest chain games ever played in this server")
    async def top(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        rows  = await db.get_top_chains(str(ctx.guild.id))
        embed = top_chains_embed(rows, ctx.guild.name)
        await ctx.followup.send(embed=embed)

    # ── /chain end ─────────────────────────────────────────────────────────────

    @chain.command(name="end", description="End the active chain game in this channel")
    async def end(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        gid = str(ctx.guild.id)
        row = await db.get_active_chain(gid, str(ctx.channel.id))
        if not row:
            await ctx.followup.send("No active chain game to end.")
            return

        started_by = row.get("started_by") or ""
        is_starter = bool(started_by) and str(ctx.author.id) == started_by
        is_mod     = ctx.author.guild_permissions.manage_messages
        if not is_starter and not is_mod:
            await ctx.followup.send(
                "⚠️ Only the player who started this game or a moderator "
                "(Manage Messages) can end it.",
                ephemeral=True,
            )
            return

        game  = ChainGame.from_db(row)
        moves = await db.get_chain_moves(game.game_id)
        await db.update_chain_game(game.game_id, game.words_used, game.next_letter or "", "ended")

        seen: set[str] = set()
        for m in moves:
            if m["user_id"] not in seen:
                seen.add(m["user_id"])
                await db.update_longest_chain(m["user_id"], gid, game.chain_length)

        tally: dict[str, list[str]] = {}
        for m in moves:
            tally.setdefault(m["username"], []).append(m["word"])

        embed = chain_end_embed(game.game_id, game.chain_length, tally)
        _active_game_channels.discard((gid, str(ctx.channel.id)))
        await ctx.followup.send(embed=embed, view=PostGameView())

        if game.chain_length > 0:
            recap_view = ChainRecapView(game.words_used, game.game_id)
            await _try_channel_send(
                ctx.channel,
                "📜 **Final Chain Recap:**",
                recap_view.build_embed(),
                recap_view if recap_view.total_pages > 1 else None,
            )

    # ── /chain remove ──────────────────────────────────────────────────────────

    @chain.command(
        name="remove",
        description="Admin: force-end an active game or delete an ended game",
        default_member_permissions=discord.Permissions(manage_guild=True),
    )
    async def remove(
        self,
        ctx: discord.ApplicationContext,
        game_id: discord.Option(  # type: ignore[valid-type]
            int,
            "Game ID to target (leave blank to target the active game in this channel)",
            required=False,
        ) = None,
    ):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.", ephemeral=True)
            return

        gid = str(ctx.guild.id)

        if game_id is not None:
            row = await db.get_chain_game_by_id(game_id)
            if not row or row.get("guild_id") != gid:
                await ctx.followup.send(
                    f"❌ No game with ID **#{game_id}** found in this server.", ephemeral=True
                )
                return
        else:
            row = await db.get_active_chain(gid, str(ctx.channel.id))
            if not row:
                await ctx.followup.send(
                    "No active game in this channel.\n"
                    "Use the `game_id` option to target a specific game by ID.",
                    ephemeral=True,
                )
                return

        g_id     = row["id"]
        g_status = row.get("status", "active")
        g_cid    = row.get("channel_id")

        if g_status == "active":
            game  = ChainGame.from_db(row)
            moves = await db.get_chain_moves(g_id)
            await db.update_chain_game(g_id, game.words_used, game.next_letter or "", "ended")
            _active_game_channels.discard((gid, g_cid))

            seen: set[str] = set()
            for m in moves:
                if m["user_id"] not in seen:
                    seen.add(m["user_id"])
                    await db.update_longest_chain(m["user_id"], gid, game.chain_length)

            notice = discord.Embed(
                title=f"🛑 Game #{g_id} Force-Ended",
                colour=ERROR_COLOR,
                description=(
                    f"This game was stopped by admin **{ctx.author.display_name}**.\n"
                    f"Final chain length: **{game.chain_length}** word{'s' if game.chain_length != 1 else ''}."
                ),
            )
            target = ctx.guild.get_channel(int(g_cid)) if g_cid else None
            if target and target.id != ctx.channel.id:
                try:
                    await target.send(embed=notice, view=PostGameView())
                except (discord.Forbidden, discord.HTTPException):
                    pass
            elif not target or target.id == ctx.channel.id:
                try:
                    await ctx.channel.send(embed=notice, view=PostGameView())
                except (discord.Forbidden, discord.HTTPException):
                    pass

            await ctx.followup.send(
                f"✅ Game **#{g_id}** force-ended. "
                f"Chain was **{game.chain_length}** word{'s' if game.chain_length != 1 else ''} long.",
                ephemeral=True,
            )
        else:
            await db.delete_chain_game(g_id)
            await ctx.followup.send(
                f"🗑️ Game **#{g_id}** (was: `{g_status}`) has been permanently deleted.",
                ephemeral=True,
            )

    # ── /chain help ────────────────────────────────────────────────────────────

    @chain.command(name="help", description="How to play Word Chain")
    async def help(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="How to Play Word Chain",
            colour=CHAIN_COLOR,
            description=(
                "A multiplayer word-linking game using 5-letter words.\n\n"
                "**Rules**\n"
                "• Each word must start with the letter determined by the **game mode**\n"
                "  `SENSE` → `ENTER` → `ROVER` → `RANGE` → `EMBER` → …\n"
                "• Words must be valid 5-letter English words (in the dictionary)\n"
                "• No repeating words in the same game\n"
                "• Any player can join — just type a 5-letter word!\n\n"
                "**Scoring** *(Scrabble-style letter rarity)*\n"
                "• ★☆☆ **Common** word (Scrabble sum ≤ 7) = **+1 pt**\n"
                "• ★★☆ **Moderate** word (sum 8–12) = **+2 pts**\n"
                "• ★★★ **Rare** word (sum ≥ 13) = **+3 pts**\n"
                "• **+2 milestone bonus** every 5 words added to the chain\n\n"
                "**Game Modes** (choose at `/chain start`)\n"
                "`last` *(default)* — next word starts with the **last** letter\n"
                "`random` — a **random** letter from the word is chosen next\n"
                "`2nd` / `3rd` / `4th` — specific position's letter is used\n\n"
                "**Streak & Spotlight**\n"
                "• 🔥 **Streak bonus** — play back-to-back words for **+1 extra pt** each time\n"
                "• ✨ **Rare word spotlight** — ★★★ rare words get a special callout\n"
                "• 🎉 **Milestone recap** — full chain shown every 100 words\n\n"
                "**Buttons** *(shown below game messages)*\n"
                "📊 **Status** · 💡 **Hint** · 🏆 **Leaderboard** · 📊 **My Stats**\n"
                "🔚 **End Game** *(starter/mod)* · ➕ **Add Word** *(admin)*\n\n"
                "**Commands**\n"
                "`/chain start [mode]` — start a game\n"
                "`/chain status` · `/chain hint` · `/chain top` · `/chain end`\n"
                "`/chain words <letter>` — words used for a letter (paginated)\n"
                "`/chain remove [game_id]` — *(admin)* force-end or delete a game\n"
                "`/checkword <word>` — check if a word is in the dictionary\n"
            ),
        )
        await ctx.respond(embed=embed, ephemeral=True)


# ── Word dictionary management ─────────────────────────────────────────────────

class WordAdminCog(commands.Cog):

    @commands.slash_command(name="addword", description="Add a word to the dictionary (admin only)")
    @discord.default_permissions(manage_guild=True)
    async def addword(
        self,
        ctx: discord.ApplicationContext,
        word: discord.Option(str, "5-letter word to add", required=True),  # type: ignore[valid-type]
    ):
        await ctx.defer(ephemeral=True)
        word = word.strip().upper()

        if len(word) != 5 or not word.isalpha():
            await ctx.followup.send(
                f"❌ `{word}` is not a valid 5-letter alphabetic word.", ephemeral=True
            )
            return

        added = add_word(word)
        if added:
            embed = discord.Embed(
                title="Word Added",
                description=f"✅ `{word}` has been added to the dictionary.\nDictionary now has **{word_count()}** words.",
                colour=OK_COLOR,
            )
        else:
            embed = discord.Embed(
                title="Already Exists",
                description=f"`{word}` is already in the dictionary ({word_count()} words total).",
                colour=discord.Colour.greyple(),
            )
        await ctx.followup.send(embed=embed, ephemeral=True)

    @commands.slash_command(name="removeword", description="Remove a word from the dictionary (bot developer only)")
    @discord.default_permissions(administrator=True)
    async def removeword(
        self,
        ctx: discord.ApplicationContext,
        word: discord.Option(str, "5-letter word to remove", required=True),  # type: ignore[valid-type]
    ):
        await ctx.defer(ephemeral=True)

        # Restricted to bot owner(s) only
        owner_ids: set[int] = set()
        if ctx.bot.owner_id:
            owner_ids.add(ctx.bot.owner_id)
        if ctx.bot.owner_ids:
            owner_ids |= ctx.bot.owner_ids
        if not owner_ids or ctx.author.id not in owner_ids:
            await ctx.followup.send(
                "❌ Removing words from the dictionary is restricted to the bot developer.",
                ephemeral=True,
            )
            return

        word = word.strip().upper()
        removed = remove_word(word)
        if removed:
            embed = discord.Embed(
                title="Word Removed",
                description=f"🗑️ `{word}` has been removed. Dictionary now has **{word_count()}** words.",
                colour=OK_COLOR,
            )
        else:
            embed = discord.Embed(
                title="Not Found",
                description=f"`{word}` was not in the dictionary.",
                colour=ERROR_COLOR,
            )
        await ctx.followup.send(embed=embed, ephemeral=True)

    @commands.slash_command(name="checkword", description="Check if a word is in the dictionary")
    async def checkword(
        self,
        ctx: discord.ApplicationContext,
        word: discord.Option(str, "Word to check", required=True),  # type: ignore[valid-type]
    ):
        word = word.strip().upper()
        if len(word) != 5 or not word.isalpha():
            await ctx.respond(f"❌ `{word}` is not a 5-letter word.", ephemeral=True)
            return

        if is_valid(word):
            await ctx.respond(
                f"✅ `{word}` is in the dictionary ({word_count()} words total).",
                ephemeral=True,
            )
        else:
            await ctx.respond(
                f"❌ `{word}` is **not** in the dictionary. "
                f"An admin can add it via `/addword {word}` or the ➕ **Add Word** button.",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(ChainCog(bot))
    bot.add_cog(WordAdminCog())

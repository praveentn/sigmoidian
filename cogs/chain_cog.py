import asyncio
import logging
import time
from collections import defaultdict

import discord
from discord.ext import commands
from discord import SlashCommandGroup

from utils import database as db
from utils.display import (
    chain_status_embed, hint_embed, chain_end_embed,
    chain_recap_embed, top_chains_embed, _remaining_indicator,
    ERROR_COLOR, CHAIN_COLOR, OK_COLOR,
)
from utils.words import is_valid, add_word, remove_word, word_count, remaining_for_letter, get_hints
from game.chain import ChainGame, VALID_MODES

log = logging.getLogger("sigmoidian.chain")

# Per-(guild, channel) lock — serialises concurrent /chain play calls to prevent
# TOCTOU races where two simultaneous plays would both pass validation against the
# same stale game state and corrupt the chain.
_channel_locks: dict[tuple[str, str], asyncio.Lock] = defaultdict(asyncio.Lock)

# Per-user cooldown: prevents rapid-fire spam of /chain play
_user_last_play: dict[str, float] = {}
_PLAY_COOLDOWN = 1.5  # seconds


async def _try_channel_send(
    channel: discord.abc.Messageable,
    content: str,
    embed: discord.Embed,
    view: discord.ui.View | None = None,
) -> bool:
    """Send a message to a channel, gracefully handling permission errors."""
    try:
        await channel.send(content, embed=embed, view=view)
        return True
    except (discord.Forbidden, discord.HTTPException) as exc:
        log.warning("Cannot send to channel %s: %s", getattr(channel, "id", "?"), exc)
        return False


# ── Paginated views ────────────────────────────────────────────────────────────

class ChainRecapView(discord.ui.View):
    """Paginated view of all words in a chain — 50 words per page."""
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
    """Paginated view of all words used for a specific starting letter — 15 per page."""
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
            # 15 lines × ~30 chars ≈ 450 chars — safe within 1024 field limit
            lines = [f"`{m['word']}` — **{m['username']}**" for m in page_moves]
            embed.add_field(
                name=f"Words {start + 1}–{end} of {len(self.moves)}",
                value="\n".join(lines),
                inline=False,
            )
        else:
            embed.add_field(name=f"Used (0)", value="None yet.", inline=False)

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

    # ── /chain start ──────────────────────────────────────────────────────────
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
            await ctx.followup.send(embed=embed)
            return

        game_id = await db.create_chain_game(gid, cid, mode, started_by=str(ctx.author.id))
        await db.upsert_user(str(ctx.author.id), gid, ctx.author.display_name)

        mode_desc = _MODE_LABELS.get(mode, mode)
        embed = discord.Embed(
            title=f"🔗 Word Chain Started — Game #{game_id}",
            colour=CHAIN_COLOR,
            description=(
                "**How to play**\n"
                "• `/chain play <word>` — add a 5-letter word to the chain\n"
                f"• Each word must start with the **{mode_desc}** of the previous word\n"
                "  e.g. `SENSE` → `ENTER` → `ROVER` → `RANGE` → …\n"
                "• Words must exist in the dictionary · no repeats · any player can join!\n\n"
                "**Scoring**\n"
                "• ★☆☆ **Common** word = **+1 pt**  ·  ★★☆ **Moderate** = **+2 pts**  ·  ★★★ **Rare** = **+3 pts**\n"
                "• **+2 milestone bonus** every 5 words in the chain\n\n"
                "The first player can start with **any** valid 5-letter word."
            ),
        )
        embed.set_footer(text=f"Game #{game_id} | Mode: {mode_desc} | /chain end to stop")
        await ctx.followup.send(embed=embed)

    # ── /chain play ───────────────────────────────────────────────────────────
    @chain.command(name="play", description="Play a word in the active chain game")
    async def play(
        self,
        ctx: discord.ApplicationContext,
        word: discord.Option(str, "Your 5-letter word", required=True),  # type: ignore[valid-type]
    ):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        uid  = str(ctx.author.id)
        gid  = str(ctx.guild.id)
        cid  = str(ctx.channel.id)
        word = word.strip().upper()

        # ── Per-user rate limit ───────────────────────────────────────────────
        rk   = f"{uid}:{gid}"
        now  = time.monotonic()
        wait = _PLAY_COOLDOWN - (now - _user_last_play.get(rk, 0))
        if wait > 0:
            await ctx.followup.send(
                f"⏳ Wait **{wait:.1f}s** before playing again.", ephemeral=True
            )
            return
        _user_last_play[rk] = now

        # ── Serialise concurrent plays per channel to prevent TOCTOU races ───
        async with _channel_locks[(gid, cid)]:
            row = await db.get_active_chain(gid, cid)
            if not row:
                await ctx.followup.send(
                    "No active chain game here. Use `/chain start` to begin."
                )
                return

            game  = ChainGame.from_db(row)
            error = game.validate(word)
            if error:
                embed = discord.Embed(
                    title="Invalid Word",
                    description=f"{ctx.author.mention} — {error}",
                    colour=ERROR_COLOR,
                )
                if game.next_letter:
                    embed.set_footer(text=f"Next word must start with: {game.next_letter}")
                await ctx.followup.send(embed=embed)
                return

            total, base_pts, tier_label, stars = game.play(word)

            await db.update_chain_game(game.game_id, game.words_used, game.next_letter or "")
            await db.add_chain_move(game.game_id, uid, ctx.author.display_name, word)
            await db.upsert_user(uid, gid, ctx.author.display_name)

            # Fetch moves (includes the just-added move at the end)
            moves = await db.get_chain_moves(game.game_id)

            # ── Streak bonus: +1 if player played the previous word too ──────
            streak_count = 0
            for m in reversed(moves[:-1]):
                if m["user_id"] == uid:
                    streak_count += 1
                else:
                    break
            streak_bonus = 1 if streak_count >= 1 else 0
            total_final  = total + streak_bonus

            await db.increment_stat(uid, gid, "chain_points", total_final)
            await db.increment_stat(uid, gid, "chain_words")
            await db.log_word(gid, uid, word)

            remaining = (
                remaining_for_letter(game.next_letter, set(game.words_used))
                if game.next_letter else None
            )

            # ── Auto-end: no words remain for the required next letter ───────
            if remaining == 0:
                await db.update_chain_game(
                    game.game_id, game.words_used, game.next_letter or "", "ended"
                )
                seen: set[str] = set()
                for m in moves:
                    if m["user_id"] not in seen:
                        seen.add(m["user_id"])
                        await db.update_longest_chain(m["user_id"], gid, game.chain_length)

                milestone_note = " *(+2 milestone bonus!)*" if total > base_pts else ""
                streak_note    = f" 🔥 *+1 streak ({streak_count + 1} in a row!)*" if streak_bonus else ""
                embed = discord.Embed(
                    title=f"🏁 Chain Complete — Game #{game.game_id}",
                    colour=discord.Colour.orange(),
                    description=(
                        f"✅ **{ctx.author.display_name}** played `{word}` "
                        f"({stars} **+{total_final} pt{'s' if total_final != 1 else ''}**)"
                        f"{milestone_note}{streak_note}\n\n"
                        f"💀 **No more words start with `{game.next_letter}`** — the dictionary is exhausted!\n"
                        f"The chain ends here at **{game.chain_length}** word(s). Well played!\n\n"
                        "Use `/chain start` to begin a new game."
                    ),
                )
                await ctx.followup.send(embed=embed)
                if game.chain_length > 0:
                    recap_view = ChainRecapView(game.words_used, game.game_id)
                    await _try_channel_send(
                        ctx.channel,
                        "📜 **Final Chain Recap:**",
                        recap_view.build_embed(),
                        recap_view if recap_view.total_pages > 1 else None,
                    )
                return

            # ── Normal play response ──────────────────────────────────────────
            embed = chain_status_embed(
                game.words_used, game.next_letter or "?", moves, game.game_id, remaining, game.game_mode
            )
            milestone_note = " *(+2 milestone bonus!)*" if total > base_pts else ""
            streak_note    = f" 🔥 *+1 streak ({streak_count + 1} in a row!)*" if streak_bonus else ""
            desc = (
                f"✅ **{ctx.author.display_name}** played `{word}` "
                f"— {stars} **+{total_final} pt{'s' if total_final != 1 else ''}**{milestone_note}{streak_note}"
            )
            if stars == "★★★":
                desc += f"\n✨ **Rare word spotlight!** `{word}` — {tier_label}, {base_pts} base pts."
            embed.description = desc
            await ctx.followup.send(embed=embed)

        # ── Milestone recap every 100 words (outside lock — state already saved) ──
        if game.chain_length % 100 == 0:
            recap_view = ChainRecapView(game.words_used, game.game_id)
            await _try_channel_send(
                ctx.channel,
                f"🎉 **{game.chain_length}-word milestone!** Here's the chain so far:",
                recap_view.build_embed(),
                recap_view if recap_view.total_pages > 1 else None,
            )

    # ── /chain status ─────────────────────────────────────────────────────────
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
        await ctx.followup.send(embed=embed)

    # ── /chain words ──────────────────────────────────────────────────────────
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

    # ── /chain hint ───────────────────────────────────────────────────────────
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
            await ctx.followup.send(
                "No active chain game here. Use `/chain start` to begin."
            )
            return

        game = ChainGame.from_db(row)
        if not game.next_letter:
            await ctx.followup.send(
                "The game just started — any valid 5-letter word works!"
            )
            return

        used   = set(game.words_used)
        hints  = get_hints(game.next_letter, used)
        rem    = remaining_for_letter(game.next_letter, used)
        embed  = hint_embed(game.next_letter, hints, rem, game.game_id, ctx.author.display_name)
        await ctx.followup.send(embed=embed)

    # ── /chain top ────────────────────────────────────────────────────────────
    @chain.command(name="top", description="Show the longest chain games ever played in this server")
    async def top(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        rows  = await db.get_top_chains(str(ctx.guild.id))
        embed = top_chains_embed(rows, ctx.guild.name)
        await ctx.followup.send(embed=embed)

    # ── /chain end ────────────────────────────────────────────────────────────
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

        # Only the game starter or a moderator (Manage Messages) can end the game.
        # If started_by is empty (game predates this field), allow any moderator.
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
        await ctx.followup.send(embed=embed)

        if game.chain_length > 0:
            recap_view = ChainRecapView(game.words_used, game.game_id)
            await _try_channel_send(
                ctx.channel,
                "📜 **Final Chain Recap:**",
                recap_view.build_embed(),
                recap_view if recap_view.total_pages > 1 else None,
            )

    # ── /chain help ───────────────────────────────────────────────────────────
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
                "• Any player can join — just use `/chain play`\n\n"
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
                "**Commands**\n"
                "`/chain start [mode]` — start a game\n"
                "`/chain play <word>` — add a word\n"
                "`/chain status` — view the current chain and remaining words\n"
                "`/chain words <letter>` — see all words used for a letter (paginated)\n"
                "`/chain hint` — ask for a hint (visible to all — use wisely!)\n"
                "`/chain top` — server's longest chains ever\n"
                "`/chain end` — end and show results\n"
                "`/checkword <word>` — check if a word is in the dictionary\n"
            ),
        )
        await ctx.respond(embed=embed, ephemeral=True)


# ── Word dictionary management (top-level commands) ───────────────────────────

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

    @commands.slash_command(name="removeword", description="Remove a word from the dictionary (admin only)")
    @discord.default_permissions(manage_guild=True)
    async def removeword(
        self,
        ctx: discord.ApplicationContext,
        word: discord.Option(str, "5-letter word to remove", required=True),  # type: ignore[valid-type]
    ):
        await ctx.defer(ephemeral=True)
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
                f"An admin can add it with `/addword {word}`.",
                ephemeral=True,
            )


def setup(bot):
    bot.add_cog(ChainCog())
    bot.add_cog(WordAdminCog())

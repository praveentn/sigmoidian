import discord
from discord.ext import commands
from discord import SlashCommandGroup

from utils import database as db
from utils.display import (
    chain_status_embed, words_by_letter_embed,
    ERROR_COLOR, CHAIN_COLOR, OK_COLOR,
)
from utils.words import is_valid, add_word, remove_word, word_count, remaining_for_letter
from game.chain import ChainGame, VALID_MODES

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

        game_id = await db.create_chain_game(gid, cid, mode)
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
        await db.increment_stat(uid, gid, "chain_points", total)
        await db.increment_stat(uid, gid, "chain_words")
        await db.log_word(gid, uid, word)

        remaining = (
            remaining_for_letter(game.next_letter, set(game.words_used))
            if game.next_letter else None
        )

        # Auto-end if no words remain for the required next letter
        if remaining == 0:
            await db.update_chain_game(
                game.game_id, game.words_used, game.next_letter or "", "ended"
            )
            embed = discord.Embed(
                title=f"🏁 Chain Complete — Game #{game.game_id}",
                colour=discord.Colour.orange(),
                description=(
                    f"✅ **{ctx.author.display_name}** played `{word}` "
                    f"({stars} **+{total} pt{'s' if total != 1 else ''}**)\n\n"
                    f"💀 **No more words start with `{game.next_letter}`** — the dictionary is exhausted!\n"
                    f"The chain ends here at **{game.chain_length}** word(s). Well played!\n\n"
                    "Use `/chain start` to begin a new game."
                ),
            )
            await ctx.followup.send(embed=embed)
            return

        moves = await db.get_chain_moves(game.game_id)
        embed = chain_status_embed(
            game.words_used, game.next_letter or "?", moves, game.game_id, remaining, game.game_mode
        )
        milestone_note = " *(+2 milestone bonus!)*" if total > base_pts else ""
        embed.description = (
            f"✅ **{ctx.author.display_name}** played `{word}` "
            f"— {stars} **+{total} pt{'s' if total != 1 else ''}**{milestone_note}"
        )
        await ctx.followup.send(embed=embed)

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

        embed = words_by_letter_embed(letter, letter_moves, remaining, game.game_id)
        await ctx.followup.send(embed=embed)

    # ── /chain end ────────────────────────────────────────────────────────────
    @chain.command(name="end", description="End the active chain game in this channel")
    async def end(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        row = await db.get_active_chain(str(ctx.guild.id), str(ctx.channel.id))
        if not row:
            await ctx.followup.send("No active chain game to end.")
            return

        game  = ChainGame.from_db(row)
        moves = await db.get_chain_moves(game.game_id)
        await db.update_chain_game(game.game_id, game.words_used, game.next_letter or "", "ended")

        # Per-player summary for this game
        tally: dict[str, list[str]] = {}
        for m in moves:
            tally.setdefault(m["username"], []).append(m["word"])

        lines = [
            f"**{name}** — {len(words)} word(s): {', '.join(f'`{w}`' for w in words)}"
            for name, words in sorted(tally.items(), key=lambda x: -len(x[1]))
        ]

        embed = discord.Embed(
            title=f"🔗 Chain Ended — Game #{game.game_id}",
            colour=CHAIN_COLOR,
            description=(
                f"Chain length: **{game.chain_length}** word(s)\n\n"
                + ("\n".join(lines) if lines else "No moves were made.")
            ),
        )
        await ctx.followup.send(embed=embed)

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
                "**Commands**\n"
                "`/chain start [mode]` — start a game\n"
                "`/chain play <word>` — add a word\n"
                "`/chain status` — view the current chain and remaining words\n"
                "`/chain words <letter>` — see words used for a letter + how many are left\n"
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

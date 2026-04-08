import discord
from discord.ext import commands
from discord import SlashCommandGroup

from utils import database as db
from utils.display import chain_status_embed, ERROR_COLOR, CHAIN_COLOR, OK_COLOR
from utils.words import is_valid, add_word, remove_word, word_count
from game.chain import ChainGame


class ChainCog(commands.Cog):
    chain = SlashCommandGroup("chain", "Word-chain multiplayer game commands")

    # ── /chain start ──────────────────────────────────────────────────────────
    @chain.command(name="start", description="Start a word-chain game in this channel")
    async def start(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        gid, cid = str(ctx.guild.id), str(ctx.channel.id)
        existing = await db.get_active_chain(gid, cid)
        if existing:
            game  = ChainGame.from_db(existing)
            moves = await db.get_chain_moves(game.game_id)
            embed = chain_status_embed(game.words_used, game.next_letter or "?", moves, game.game_id)
            embed.description = "⚠️ A chain game is already running in this channel!"
            await ctx.followup.send(embed=embed)
            return

        game_id = await db.create_chain_game(gid, cid)
        await db.upsert_user(str(ctx.author.id), gid, ctx.author.display_name)

        embed = discord.Embed(
            title=f"🔗 Word Chain Started — Game #{game_id}",
            colour=CHAIN_COLOR,
            description=(
                "**How to play**\n"
                "• `/chain play <word>` — add a 5-letter word to the chain\n"
                "• Each word must **start with the last letter** of the previous word\n"
                "  e.g. `SENSE` → `ENTER` → `ROVER` → `RANGE` → …\n"
                "• Words must exist in the dictionary · no repeats · any player can join!\n\n"
                "**Scoring** · +1 pt per valid word · +2 bonus every 5 words in the chain\n\n"
                "The first player can start with **any** valid 5-letter word."
            ),
        )
        embed.set_footer(text=f"Game #{game_id} | /chain end to stop")
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

        points = game.play(word)

        await db.update_chain_game(game.game_id, game.words_used, game.next_letter or "")
        await db.add_chain_move(game.game_id, uid, ctx.author.display_name, word)
        await db.upsert_user(uid, gid, ctx.author.display_name)
        await db.increment_stat(uid, gid, "chain_points", points)
        await db.increment_stat(uid, gid, "chain_words")
        await db.log_word(gid, uid, word)

        moves = await db.get_chain_moves(game.game_id)
        embed = chain_status_embed(game.words_used, game.next_letter or "?", moves, game.game_id)
        bonus_note = " *(+2 chain bonus!)*" if points > 1 else ""
        embed.description = (
            f"✅ **{ctx.author.display_name}** played `{word}` "
            f"— **+{points} pt{'s' if points != 1 else ''}**{bonus_note}"
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
        embed = chain_status_embed(
            game.words_used, game.next_letter or "any letter", moves, game.game_id
        )
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
                "• Each word must start with the **last letter** of the previous word\n"
                "  `SENSE` → `ENTER` → `ROVER` → `RANGE` → `EMBER` → …\n"
                "• Words must be valid 5-letter English words (in the dictionary)\n"
                "• No repeating words in the same game\n"
                "• Any player can join — just use `/chain play`\n\n"
                "**Scoring**\n"
                "• **+1 pt** per valid word\n"
                "• **+2 bonus pts** every time the chain hits a multiple of 5\n\n"
                "**Commands**\n"
                "`/chain start` — start a game in this channel\n"
                "`/chain play <word>` — add a word\n"
                "`/chain status` — view the current chain\n"
                "`/chain end` — end and show results\n"
                "`/addword <word>` — add a missing word *(admin only)*\n"
                "`/removeword <word>` — remove a word *(admin only)*\n"
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

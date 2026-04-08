import discord
from discord.ext import commands

from utils import database as db
from utils.display import stats_embed, leaderboard_embed, top_words_embed
from utils.words import word_count


class StatsCog(commands.Cog):

    @commands.slash_command(name="stats", description="Show your chain game stats in this server")
    async def stats(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.", ephemeral=True)
            return

        uid, gid = str(ctx.author.id), str(ctx.guild.id)
        await db.upsert_user(uid, gid, ctx.author.display_name)
        row = await db.get_user_stats(uid, gid)

        if not row or (row.get("chain_points", 0) == 0 and row.get("chain_words", 0) == 0):
            await ctx.followup.send(
                "No stats yet — join a chain game with `/chain play`!", ephemeral=True
            )
            return

        embed = stats_embed(row, ctx.author.display_name)
        await ctx.followup.send(embed=embed, ephemeral=True)

    @commands.slash_command(name="leaderboard", description="Show the server leaderboard")
    async def leaderboard(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        rows  = await db.get_leaderboard(str(ctx.guild.id))
        embed = leaderboard_embed(rows, ctx.guild.name)
        await ctx.followup.send(embed=embed)

    @commands.slash_command(name="topwords", description="Most used words in this server")
    async def topwords(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        if ctx.guild is None:
            await ctx.followup.send("Use this command inside a server.")
            return

        rows  = await db.get_top_words(str(ctx.guild.id))
        embed = top_words_embed(rows, ctx.guild.name)
        await ctx.followup.send(embed=embed)

    @commands.slash_command(name="dictionary", description="Show dictionary info")
    async def dictionary(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="📖 Dictionary",
            colour=discord.Colour.blurple(),
            description=(
                f"**{word_count()}** valid 5-letter words loaded.\n\n"
                "Words are stored in `data/words.txt` — one word per line.\n"
                "You can also manage words with:\n"
                "`/addword <word>` — add a missing word *(admin only)*\n"
                "`/removeword <word>` — remove a word *(admin only)*\n"
                "`/checkword <word>` — check if a word is accepted"
            ),
        )
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(StatsCog())

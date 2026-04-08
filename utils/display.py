import discord
from typing import List

CHAIN_COLOR = discord.Colour.blurple()
STATS_COLOR = discord.Colour.gold()
ERROR_COLOR = discord.Colour.red()
OK_COLOR    = discord.Colour.green()

_MODE_LABELS = {
    "last":   "last letter",
    "random": "random letter",
    "2nd":    "2nd letter",
    "3rd":    "3rd letter",
    "4th":    "4th letter",
}


def _remaining_indicator(remaining: int, next_letter: str) -> str:
    """Format the words-remaining line with a colour-coded status indicator."""
    letter = next_letter.upper()
    if remaining >= 15:
        return f"🟢 **{remaining}** words available for **{letter}**"
    elif remaining >= 5:
        return f"🟡 **{remaining}** words available for **{letter}**"
    elif remaining > 0:
        return f"🔴 ⚠️ Only **{remaining}** word(s) left for **{letter}**!"
    else:
        return f"💀 **No words left** for **{letter}** — game over!"


def chain_status_embed(
    words: List[str],
    next_letter: str,
    moves: List[dict],
    game_id: int,
    remaining: int | None = None,
    game_mode: str = "last",
) -> discord.Embed:
    """Current state of an active chain game."""
    chain_str = " → ".join(f"**{w}**" for w in words[-12:])
    if len(words) > 12:
        chain_str = "… → " + chain_str

    move_lines = [
        f"`{m['word']}` — **{m['username']}**"
        for m in moves[-8:]
    ]
    moves_str = "\n".join(move_lines) if move_lines else "No moves yet."

    embed = discord.Embed(title=f"🔗 Word Chain — Game #{game_id}", colour=CHAIN_COLOR)
    embed.add_field(name="Chain", value=chain_str or "Starting…", inline=False)
    embed.add_field(name="Recent Moves", value=moves_str, inline=False)

    # Next required letter + remaining-words indicator
    if next_letter and next_letter not in ("?", "any letter"):
        letter_disp = f"**` {next_letter.upper()} `**"
        if remaining is not None:
            rem_line = _remaining_indicator(remaining, next_letter)
            next_val = f"{letter_disp}\n{rem_line}"
        else:
            next_val = letter_disp
    else:
        next_val = "Any letter"

    embed.add_field(
        name="Next word must start with",
        value=next_val,
        inline=False,
    )

    mode_label = _MODE_LABELS.get(game_mode, game_mode)
    embed.set_footer(
        text=f"Chain length: {len(words)} | Mode: {mode_label} | /chain play <word>"
    )
    return embed


def words_by_letter_embed(
    letter: str,
    moves: List[dict],
    remaining: int,
    game_id: int,
) -> discord.Embed:
    """Words used in the current game that start with a specific letter."""
    letter = letter.upper()
    embed = discord.Embed(
        title=f"🔤 Words Starting with {letter} — Game #{game_id}",
        colour=CHAIN_COLOR,
    )

    if moves:
        lines = [f"`{m['word']}` — **{m['username']}**" for m in moves]
        embed.add_field(
            name=f"Used in this game ({len(moves)})",
            value="\n".join(lines),
            inline=True,
        )
    else:
        embed.add_field(
            name="Used in this game (0)",
            value="None yet.",
            inline=True,
        )

    embed.add_field(
        name="Still available",
        value=_remaining_indicator(remaining, letter),
        inline=True,
    )
    embed.set_footer(text=f"Game #{game_id} | {len(moves)} used · {remaining} remaining")
    return embed


def stats_embed(stats: dict, username: str) -> discord.Embed:
    pts   = stats.get("chain_points", 0)
    words = stats.get("chain_words", 0)

    embed = discord.Embed(title=f"📊 Stats — {username}", colour=STATS_COLOR)
    embed.add_field(name="Chain Points", value=str(pts),   inline=True)
    embed.add_field(name="Words Played", value=str(words), inline=True)
    avg = f"{pts/words:.2f}" if words else "—"
    embed.add_field(name="Avg pts/word", value=avg,        inline=True)
    return embed


def leaderboard_embed(rows: List[dict], guild_name: str) -> discord.Embed:
    embed = discord.Embed(title=f"🏆 Leaderboard — {guild_name}", colour=STATS_COLOR)
    if not rows:
        embed.description = "No stats yet. Start playing with `/chain start`!"
        return embed

    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, row in enumerate(rows):
        prefix = medals[i] if i < 3 else f"**{i+1}.**"
        name   = row.get("username") or f"<@{row['user_id']}>"
        lines.append(
            f"{prefix} **{name}** — "
            f"{row.get('chain_points', 0)} pts · "
            f"{row.get('chain_words', 0)} words"
        )
    embed.description = "\n".join(lines)
    return embed


def top_words_embed(rows: List[dict], guild_name: str) -> discord.Embed:
    embed = discord.Embed(title=f"💬 Most Used Words — {guild_name}", colour=STATS_COLOR)
    if not rows:
        embed.description = "No word history yet."
        return embed
    lines = [
        f"**{i+1}.** `{r['word']}` — {r['count']} time{'s' if r['count'] != 1 else ''}"
        for i, r in enumerate(rows)
    ]
    embed.description = "\n".join(lines)
    return embed

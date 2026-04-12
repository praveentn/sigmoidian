import discord
import random as _random
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

_FIELD_LIMIT = 1024


def _fit_field(lines: list[str], limit: int = _FIELD_LIMIT) -> str:
    """Join lines into a field value, truncating with a count if it would exceed `limit`."""
    result = ""
    for i, line in enumerate(lines):
        chunk = (line + "\n")
        if len(result) + len(chunk) > limit - 20:  # leave room for overflow note
            overflow = len(lines) - i
            result += f"… +{overflow} more"
            break
        result += chunk
    return result.strip() or "—"


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
            value=_fit_field(lines),
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


def _mask_word(word: str) -> str:
    """Reveal 3 letters: position 0 (always) + 2 random from positions 1–4.
    e.g. YEAST → Y _ A _ T  (positions 0, 2, 4 revealed)
    """
    word = word.upper()
    other_indices = list(range(1, len(word)))
    extra = _random.sample(other_indices, min(2, len(other_indices)))
    reveal = {0} | set(extra)
    return " ".join(c if i in reveal else "_" for i, c in enumerate(word))


def hint_embed(
    letter: str,
    hints: list[tuple[str, int, str, str]],
    remaining: int,
    game_id: int,
    requester: str = "",
) -> discord.Embed:
    """Hint suggestions — each word is shown with only the 2nd letter revealed."""
    letter = letter.upper()
    embed = discord.Embed(
        title=f"💡 Hint — Game #{game_id}",
        colour=CHAIN_COLOR,
    )
    if not hints:
        embed.description = f"No unused words starting with **{letter}** remain in the dictionary."
        return embed

    lines = [
        f"{stars} `{_mask_word(word)}` — {label} (+{pts} pt{'s' if pts != 1 else ''})"
        for word, pts, label, stars in hints
    ]
    who = f"**{requester}** asked for a hint" if requester else "Hint requested"
    embed.description = (
        f"{who} — words starting with **{letter}**, 3 letters revealed:\n\n"
        + "\n".join(lines)
    )
    embed.set_footer(text=_remaining_indicator(remaining, letter))
    return embed


def chain_end_embed(
    game_id: int,
    chain_length: int,
    tally: dict[str, list[str]],
) -> discord.Embed:
    """Summary embed for /chain end — safe against Discord's 4096-char description limit."""
    embed = discord.Embed(
        title=f"🔗 Chain Ended — Game #{game_id}",
        colour=CHAIN_COLOR,
        description=f"Chain length: **{chain_length}** word(s)",
    )

    if not tally:
        embed.add_field(name="Player Summary", value="No moves were made.", inline=False)
        return embed

    lines = [
        f"**{name}** — {len(words)} word(s): {', '.join(f'`{w}`' for w in words)}"
        for name, words in sorted(tally.items(), key=lambda x: -len(x[1]))
    ]
    embed.add_field(name="Player Summary", value=_fit_field(lines), inline=False)
    return embed


def chain_recap_embed(words: list[str], game_id: int, page: int, words_per_page: int = 50) -> discord.Embed:
    """One page of the full chain word list, safe against all Discord limits."""
    total = len(words)
    total_pages = max(1, (total + words_per_page - 1) // words_per_page)
    page = max(0, min(page, total_pages - 1))

    start = page * words_per_page
    end   = min(start + words_per_page, total)
    chunk = words[start:end]

    # Each word: bold 5 chars + " → " = ~9 chars; 50 words ≈ 450 chars — well within 4096
    chain_str = " → ".join(f"**{w}**" for w in chunk)
    if start > 0:
        chain_str = "… → " + chain_str

    embed = discord.Embed(
        title=f"📜 Chain Recap — Game #{game_id}",
        description=chain_str or "No words yet.",
        colour=CHAIN_COLOR,
    )
    embed.set_footer(text=f"Words {start + 1}–{end} of {total} | Page {page + 1}/{total_pages}")
    return embed


def stats_embed(stats: dict, username: str) -> discord.Embed:
    pts   = stats.get("chain_points", 0)
    words = stats.get("chain_words", 0)
    best  = stats.get("longest_chain", 0)

    embed = discord.Embed(title=f"📊 Stats — {username}", colour=STATS_COLOR)
    embed.add_field(name="Chain Points", value=str(pts),   inline=True)
    embed.add_field(name="Words Played", value=str(words), inline=True)
    avg = f"{pts/words:.2f}" if words else "—"
    embed.add_field(name="Avg pts/word", value=avg,        inline=True)
    embed.add_field(name="Longest Chain", value=str(best) if best else "—", inline=True)
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


def top_chains_embed(rows: List[dict], guild_name: str) -> discord.Embed:
    """Top completed chain games by length for a guild."""
    embed = discord.Embed(title=f"🏆 Longest Chains — {guild_name}", colour=STATS_COLOR)
    if not rows:
        embed.description = "No completed chains yet. Use `/chain start` to play!"
        return embed

    medals = ["🥇", "🥈", "🥉"]
    lines  = []
    for i, row in enumerate(rows):
        prefix    = medals[i] if i < 3 else f"**{i + 1}.**"
        mode      = _MODE_LABELS.get(row.get("game_mode", "last"), row.get("game_mode", ""))
        top_note  = f" — led by **{row['top_player']}**" if row.get("top_player") else ""
        date_note = f" · {row['date']}" if row.get("date") else ""
        lines.append(
            f"{prefix} Game **#{row['id']}** — **{row['length']}** words{top_note}\n"
            f"   {mode}{date_note}"
        )

    # Each entry ~80 chars, 10 entries ≈ 800 chars — safe within 4096
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

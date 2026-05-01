"""
Word definition display helpers.

Definitions are pre-populated into the word_definitions DB table by
scripts/populate_definitions.py — no runtime API calls are made by the bot.
"""

_POS_LABEL: dict[str, str] = {
    "noun":         "n.",
    "verb":         "v.",
    "adjective":    "adj.",
    "adverb":       "adv.",
    "pronoun":      "pron.",
    "preposition":  "prep.",
    "conjunction":  "conj.",
    "interjection": "interj.",
}


def format_definition(word: str, defn: dict) -> str:
    """Format a DB definition row into a compact Discord string."""
    pos     = defn.get("pos", "")
    meaning = defn.get("meaning", "")
    example = defn.get("example", "")
    pos_str = f"*({_POS_LABEL.get(pos, pos)})*" if pos else ""
    parts   = [f"📖 **{word.upper()}** {pos_str} — {meaning}".strip()]
    if example:
        parts.append(f'> *"{example}"*')
    return "\n".join(parts)

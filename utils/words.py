"""
Word list management.
Source of truth is data/words.txt — one uppercase word per line.
All runtime lookups use the in-memory set VALID_WORDS.
"""
import pathlib
import random as _random

_WORDS_FILE = pathlib.Path(__file__).parent.parent / "data" / "words.txt"

VALID_WORDS: set[str] = set()

# First-letter index: letter → set of all valid words starting with that letter
LETTER_INDEX: dict[str, set[str]] = {}

# Scrabble tile values — proxy for letter rarity / word difficulty
_SCRABBLE: dict[str, int] = {
    'A': 1, 'E': 1, 'I': 1, 'O': 1, 'U': 1,
    'L': 1, 'N': 1, 'S': 1, 'T': 1, 'R': 1,
    'D': 2, 'G': 2,
    'B': 3, 'C': 3, 'M': 3, 'P': 3,
    'F': 4, 'H': 4, 'V': 4, 'W': 4, 'Y': 4,
    'K': 5,
    'J': 8, 'X': 8,
    'Q': 10, 'Z': 10,
}


def _build_letter_index() -> None:
    LETTER_INDEX.clear()
    for w in VALID_WORDS:
        LETTER_INDEX.setdefault(w[0], set()).add(w)


def _load() -> None:
    """Load (or reload) words from data/words.txt into VALID_WORDS."""
    VALID_WORDS.clear()
    if not _WORDS_FILE.exists():
        print(f"[words] WARNING: word list not found at {_WORDS_FILE}")
        return
    with _WORDS_FILE.open() as f:
        for line in f:
            w = line.strip().upper()
            if len(w) == 5 and w.isalpha():
                VALID_WORDS.add(w)
    _build_letter_index()
    print(f"    Word list   : {len(VALID_WORDS)} words loaded from {_WORDS_FILE.name}")


def is_valid(word: str) -> bool:
    return word.upper() in VALID_WORDS


def word_score(word: str) -> tuple[int, str, str]:
    """
    Score a word using Scrabble letter values as a proxy for rarity.
    Returns (base_points, tier_label, star_display).
      ★☆☆ Common   — Scrabble sum ≤ 7  → 1 pt
      ★★☆ Moderate — Scrabble sum 8–12 → 2 pts
      ★★★ Rare     — Scrabble sum ≥ 13 → 3 pts
    """
    total = sum(_SCRABBLE.get(c, 1) for c in word.upper())
    if total <= 7:
        return 1, "Common", "★☆☆"
    elif total <= 12:
        return 2, "Moderate", "★★☆"
    else:
        return 3, "Rare", "★★★"


def remaining_for_letter(letter: str, used_words: set[str]) -> int:
    """Count valid words starting with `letter` that haven't been used yet."""
    available = LETTER_INDEX.get(letter.upper(), set())
    return len(available - used_words)


def add_word(word: str) -> bool:
    """
    Add a new word to the in-memory set AND persist it to data/words.txt.
    Returns True if added, False if already present.
    """
    word = word.strip().upper()
    if word in VALID_WORDS:
        return False
    VALID_WORDS.add(word)
    LETTER_INDEX.setdefault(word[0], set()).add(word)
    all_words = sorted(VALID_WORDS)
    with _WORDS_FILE.open("w") as f:
        for w in all_words:
            f.write(w + "\n")
    return True


def remove_word(word: str) -> bool:
    """
    Remove a word from the in-memory set AND from data/words.txt.
    Returns True if removed, False if not present.
    """
    word = word.strip().upper()
    if word not in VALID_WORDS:
        return False
    VALID_WORDS.discard(word)
    if word[0] in LETTER_INDEX:
        LETTER_INDEX[word[0]].discard(word)
    all_words = sorted(VALID_WORDS)
    with _WORDS_FILE.open("w") as f:
        for w in all_words:
            f.write(w + "\n")
    return True


def word_count() -> int:
    return len(VALID_WORDS)


# Load on import
_load()

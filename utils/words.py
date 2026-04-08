"""
Word list management.
Source of truth is data/words.txt — one uppercase word per line.
All runtime lookups use the in-memory set VALID_WORDS.
"""
import os
import pathlib

# Resolve path relative to this file so it works from any cwd
_WORDS_FILE = pathlib.Path(__file__).parent.parent / "data" / "words.txt"

VALID_WORDS: set[str] = set()


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
    print(f"    Word list   : {len(VALID_WORDS)} words loaded from {_WORDS_FILE.name}")


def is_valid(word: str) -> bool:
    return word.upper() in VALID_WORDS


def add_word(word: str) -> bool:
    """
    Add a new word to the in-memory set AND persist it to data/words.txt.
    Returns True if the word was added (False if it was already present).
    """
    word = word.strip().upper()
    if word in VALID_WORDS:
        return False
    VALID_WORDS.add(word)
    # Append + re-sort the file so it stays clean
    all_words = sorted(VALID_WORDS)
    with _WORDS_FILE.open("w") as f:
        for w in all_words:
            f.write(w + "\n")
    return True


def remove_word(word: str) -> bool:
    """
    Remove a word from the in-memory set AND from data/words.txt.
    Returns True if the word was removed (False if it wasn't present).
    """
    word = word.strip().upper()
    if word not in VALID_WORDS:
        return False
    VALID_WORDS.discard(word)
    all_words = sorted(VALID_WORDS)
    with _WORDS_FILE.open("w") as f:
        for w in all_words:
            f.write(w + "\n")
    return True


def word_count() -> int:
    return len(VALID_WORDS)


# Load on import
_load()

"""
Word-chain game logic — no Discord dependencies.

Rules:
  • Each word must be a valid 5-letter word.
  • Each word must start with `next_letter` (determined by game mode).
  • No word may be repeated within the same game.
  • Points: word_score base pts + milestone bonus +2 every 5 words in the chain.

Game modes (how next_letter is chosen after each word):
  last   — last letter of word (default)
  random — a random letter from the word (prefers letters with remaining unused words)
  2nd    — second letter (index 1)
  3rd    — third letter (index 2)
  4th    — fourth letter (index 3)
"""
import json
import random as _random
from typing import List

from utils.words import is_valid, word_score, remaining_for_letter

VALID_MODES = {"last", "random", "2nd", "3rd", "4th"}
_POSITION_INDEX = {"2nd": 1, "3rd": 2, "4th": 3}


class ChainGame:
    def __init__(
        self,
        game_id: int,
        words_json: str = "[]",
        next_letter: str | None = None,
        status: str = "active",
        game_mode: str = "last",
    ):
        self.game_id     = game_id
        self.status      = status
        self.game_mode   = game_mode if game_mode in VALID_MODES else "last"
        self.words_used: List[str] = json.loads(words_json)
        self.next_letter = (next_letter or "").upper() if next_letter else None

    @property
    def chain_length(self) -> int:
        return len(self.words_used)

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def _pick_next_letter(self, word: str) -> str:
        """Determine the next required starting letter from the just-played word."""
        mode = self.game_mode
        if mode == "last":
            return word[-1]
        if mode in _POSITION_INDEX:
            return word[_POSITION_INDEX[mode]]
        # random: prefer a letter that still has available unused words
        used_set = set(self.words_used)
        letters = list(word)
        _random.shuffle(letters)
        for letter in letters:
            if remaining_for_letter(letter, used_set) > 0:
                return letter
        # fallback: any random letter (game will end after this word)
        return _random.choice(list(word))

    def validate(self, word: str) -> str | None:
        """Return None if the word is valid for the chain, or an error message string."""
        word = word.upper()
        if len(word) != 5:
            return "Word must be exactly 5 letters."
        if not word.isalpha():
            return "Word must contain only letters."
        if not is_valid(word):
            return f"**{word}** is not in the word list."
        if self.next_letter and word[0] != self.next_letter:
            return f"Word must start with **{self.next_letter}**."
        if word in self.words_used:
            return f"**{word}** has already been used in this chain."
        return None

    def play(self, word: str) -> tuple[int, int, str, str]:
        """
        Add a valid word to the chain. Call validate() first.
        Returns (total_points, base_pts, tier_label, stars).
          total_points = base_pts + milestone_bonus
          milestone_bonus = +2 every time chain_length hits a multiple of 5
        """
        word = word.upper()
        self.words_used.append(word)
        self.next_letter = self._pick_next_letter(word)

        base_pts, tier_label, stars = word_score(word)
        milestone_bonus = 2 if self.chain_length % 5 == 0 else 0
        total = base_pts + milestone_bonus
        return total, base_pts, tier_label, stars

    def end(self) -> None:
        self.status = "ended"

    def words_json(self) -> str:
        return json.dumps(self.words_used)

    @classmethod
    def from_db(cls, row: dict) -> "ChainGame":
        return cls(
            game_id=row["id"],
            words_json=row.get("words_used", "[]"),
            next_letter=row.get("next_letter"),
            status=row.get("status", "active"),
            game_mode=row.get("game_mode", "last"),
        )

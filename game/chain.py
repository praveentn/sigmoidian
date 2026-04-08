"""
Word-chain game logic — no Discord dependencies.

Rules:
  • Each word must be a valid 5-letter word.
  • Each word must start with the last letter of the previous word.
  • No word may be repeated within the same game.
  • Points: 1 per valid word. Bonus +2 every 5 words contributed by the same player.
"""
import json
from typing import List
from utils.words import is_valid


class ChainGame:
    def __init__(
        self,
        game_id: int,
        words_json: str = "[]",
        next_letter: str | None = None,
        status: str = "active",
    ):
        self.game_id     = game_id
        self.status      = status
        self.words_used: List[str] = json.loads(words_json)
        self.next_letter = (next_letter or "").upper() if next_letter else None

    @property
    def chain_length(self) -> int:
        return len(self.words_used)

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def validate(self, word: str) -> str | None:
        """
        Return None if the word is valid for the chain, or an error message string.
        """
        word = word.upper()
        if len(word) != 5:
            return "Word must be exactly 5 letters."
        if not word.isalpha():
            return "Word must contain only letters."
        if not is_valid(word):
            return f"**{word}** is not in the word list."
        if self.next_letter and word[0] != self.next_letter:
            return f"Word must start with **{self.next_letter}** (last letter of previous word)."
        if word in self.words_used:
            return f"**{word}** has already been used in this chain."
        return None

    def play(self, word: str) -> int:
        """
        Add a valid word to the chain. Returns points earned this move.
        Call validate() first.
        """
        word = word.upper()
        self.words_used.append(word)
        self.next_letter = word[-1]

        # Bonus every 5 words in the chain
        bonus = 2 if self.chain_length % 5 == 0 else 0
        return 1 + bonus

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
        )

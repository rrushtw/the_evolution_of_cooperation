import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class Random(BaseStrategy):
    """隨機"""

    def __init__(self):
        super().__init__("Random")

    def play(self, opponent_id: str, opponent_history: list[dict]) -> Move:
        return Move.COOPERATE if random.random() < 0.5 else Move.CHEAT

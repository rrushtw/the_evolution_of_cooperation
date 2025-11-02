import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class Random(BaseStrategy):
    """隨機"""

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:
        return Move.COOPERATE if random.random() < 0.5 else Move.CHEAT

from strategies.base_strategy import BaseStrategy
from definitions import Move


class AlwaysCooperate(BaseStrategy):
    """永遠合作"""

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:
        return Move.COOPERATE

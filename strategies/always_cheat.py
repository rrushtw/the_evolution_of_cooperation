from strategies.base_strategy import BaseStrategy
from definitions import Move


class AlwaysCheat(BaseStrategy):
    """永遠欺騙"""

    def play(self, opponent_unique_id: str, opponent_history: list[dict]) -> Move:
        return Move.CHEAT

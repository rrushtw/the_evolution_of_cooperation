from strategies.base_strategy import BaseStrategy
from definitions import Move


class AlwaysCooperate(BaseStrategy):
    """永遠合作"""

    def __init__(self):
        super().__init__("Always Cooperate")

    def play(self, opponent_id: str, opponent_history: list[dict]) -> Move:
        return Move.CHEAT

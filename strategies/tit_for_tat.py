from strategies.base_strategy import BaseStrategy
from definitions import Move


class TitForTat(BaseStrategy):
    """以牙還牙 (TFT)"""

    def __init__(self):
        super().__init__("Tit-for-Tat")

    def play(self, opponent_unique_id: str, opponent_history: list[dict]) -> Move:
        # 1. 取得 "私怨" 列表
        #    使用 .get(key, default) 更安全，避免 KeyError
        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        if not private_history_list:
            # 2. 沒有 "私怨" 歷史 (第一回合)，則合作
            return Move.COOPERATE

        # 3. 取得上一回合的 "私怨" 紀錄 (這是一個 dict)
        last_private_record = private_history_list[-1]

        # 4. 【修正點】從紀錄中取出對手的 "實際" 出招
        opponent_last_actual_move = last_private_record["opponent_actual_move"]

        # 5. 複製該出招
        return opponent_last_actual_move

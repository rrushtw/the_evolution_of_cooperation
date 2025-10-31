from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class Pavlov(BaseStrategy):
    """
    巴甫洛夫 (Pavlov) 策略，又稱 "Win-Stay, Lose-Shift" (贏定輸變)。

    規則：
    1. 第一回合合作。
    2. 如果上一回合的結果是 "贏" (REWARD 或 TEMPTATION)，
       則 "保持 (Stay)" 上一回合的出招。
    3. 如果上一回合的結果是 "輸" (SUCKER 或 PUNISHMENT)，
       則 "改變 (Shift)" 上一回合的出招。

    (此策略只看 "私怨"，忽略傳入的 opponent_history)
    """

    def __init__(self):
        super().__init__("Pavlov (WSLS)")

    def play(self, opponent_id: str, opponent_history: list[dict]) -> Move:

        # 1. 取得 "私怨" 列表
        private_history_list = self.opponent_history.get(opponent_id, [])

        if not private_history_list:
            # 2. 第一回合，總是合作
            return Move.COOPERATE

        # 3. 取得上一回合的紀錄
        last_record = private_history_list[-1]
        my_last_move = last_record["my_actual_move"]
        last_result = last_record["match_result"]

        # 4. 檢查 "贏" (REWARD 或 TEMPTATION)
        if last_result == MatchResult.REWARD or last_result == MatchResult.TEMPTATION:
            # Win-Stay: 保持上一次的出招
            return my_last_move
        else:
            # Lose-Shift: 改變上一次的出招
            # (last_result 是 SUCKER 或 PUNISHMENT)
            return Move.CHEAT if my_last_move == Move.COOPERATE else Move.COOPERATE

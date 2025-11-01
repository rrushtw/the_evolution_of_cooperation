from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class GlobalPavlov(BaseStrategy):
    """
    全局巴甫洛夫 (Global Pavlov) 策略

    這是一個 "不看對手" 的策略。
    它只看 "自己" 在 "整個錦標賽" 的 "上一回合" (self.my_history[-1]) 
    的結果，來決定這一回合的出招。

    規則 (Win-Stay, Lose-Shift):
    1. 錦標賽的第一回合，合作。
    2. 如果上一回合的結果是 "贏" (REWARD 或 TEMPTATION)，
       則 "保持 (Stay)" 上一回合的出招。
    3. 如果上一回合的結果是 "輸" (SUCKER 或 PUNISHMENT)，
       則 "改變 (Shift)" 上一回合的出招。

    (此策略 "忽略" 傳入的 opponent_unique_id 和 opponent_history)
    """

    def __init__(self):
        super().__init__("Global Pavlov")

    def play(self, opponent_unique_id: str, opponent_history: list[dict]) -> Move:

        # 1. 檢查 "全局歷史"
        if not self.my_history:
            # 2. 這是整個錦標賽的第一回合，總是合作
            return Move.COOPERATE

        # 3. 取得 "上一回合" (對戰任何人) 的紀錄
        last_global_record = self.my_history[-1]
        my_last_move = last_global_record["my_actual_move"]
        last_result = last_global_record["match_result"]

        # 4. 檢查 "贏" (REWARD 或 TEMPTATION)
        if last_result == MatchResult.REWARD or last_result == MatchResult.TEMPTATION:
            # Win-Stay: 保持上一次的出招
            return my_last_move
        else:
            # Lose-Shift: 改變上一次的出招
            # (last_result 是 SUCKER 或 PUNISHMENT)
            return Move.CHEAT if my_last_move == Move.COOPERATE else Move.COOPERATE

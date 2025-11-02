from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class LimitedPunisher(BaseStrategy):
    """
    有限懲罰者 (您的 "記點/救贖/有限報復" 變體)

    規則：
    1. 預設保持合作 (善良)。
    2. 內部有一個 "記點" 系統 (strike_counts)，記錄對手 "總共" 背叛了幾次。
    3. 如果對手 "實際" 背叛 (CHEAT)，記點 +1。
    4. 【救贖】如果雙方 "相互合作" (REWARD)，則記點 -1。
    5. 【觸發】一旦 "總記點" 達到 3 次 (STRIKE_LIMIT)：
       a. 將記點重置為 0。
       b. 設定 "懲罰回合數" 為 2 (PUNISHMENT_ROUNDS)。
    6. 【懲罰】在 "懲罰回合數" > 0 時，一律出 CHEAT，並在 update 時 -1。
    """

    STRIKE_LIMIT = 3
    PUNISHMENT_ROUNDS = 2  # <-- 設為 2, 避免觸發其他策略的 3 次上限

    def __init__(self):
        super().__init__()
        # "記點" 系統
        self.strike_counts = {}
        # "懲罰" 計時器
        self.punishment_timers = {}

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 檢查是否處於 "懲罰" 階段
        rounds_left = self.punishment_timers.get(opponent_unique_id, 0)

        if rounds_left > 0:
            return Move.CHEAT  # 正在懲罰

        # 2. 如果不在懲罰階段，則合作
        return Move.COOPERATE

    def update(self,
               opponent_unique_id: str,
               my_intended_move: Move,
               my_actual_move: Move,
               opponent_intended_move: Move,
               opponent_actual_move: Move,
               match_result: MatchResult):

        super().update(
            opponent_unique_id,
            my_intended_move,
            my_actual_move,
            opponent_intended_move,
            opponent_actual_move,
            match_result
        )

        # 1. 檢查是否正在懲罰
        rounds_left = self.punishment_timers.get(opponent_unique_id, 0)

        if rounds_left > 0:
            # 正在懲罰，計時器 -1
            self.punishment_timers[opponent_unique_id] = rounds_left - 1
            # 在懲罰期間，不計點也不救贖
            return

        # 2. 如果不在懲罰階段，則執行 "記點/救贖" 邏輯
        current_strikes = self.strike_counts.get(opponent_unique_id, 0)

        # 3. 【救贖機制】
        if match_result == MatchResult.REWARD:
            current_strikes = max(0, current_strikes - 1)

        # 4. 【記點機制】
        if opponent_actual_move == Move.CHEAT:
            current_strikes += 1

        # 5. 【觸發懲罰】
        if current_strikes >= self.STRIKE_LIMIT:
            # 開始懲罰
            self.punishment_timers[opponent_unique_id] = self.PUNISHMENT_ROUNDS
            # 重置記點
            self.strike_counts[opponent_unique_id] = 0
        else:
            # 儲存更新後的記點
            self.strike_counts[opponent_unique_id] = current_strikes

    def reset(self):
        super().reset()
        self.strike_counts = {}
        self.punishment_timers = {}

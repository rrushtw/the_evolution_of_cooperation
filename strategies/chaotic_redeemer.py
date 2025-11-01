import random
from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class ChaoticRedeemer(BaseStrategy):
    """
    渾沌救贖者 (Chaotic Redeemer) - 您的 "25% 誤判意圖" 版本

    這是一個 "看意圖" 的 Redeemer，但它有 25% 的機率會 "看錯" 意圖。

    規則：
    1. 它會先 "感知" 對手的意圖。
    2. 有 25% (P_MISJUDGE) 的機率，它會把 C 看成 D，或 D 看成 C。
    3. 它 100% 相信自己 "感知" 到的意圖。
    4. 然後，它會根據這個 (可能錯誤的) "感知意圖" 來執行 Redeemer 的記點/救贖邏輯。
    """

    STRIKE_LIMIT = 3

    # 25% 的機率 "誤判" 意圖
    P_MISJUDGE = 0.25

    def __init__(self):
        super().__init__()
        self.grudge_list = set()
        self.strike_counts = {}

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict]
             ) -> Move:

        if opponent_unique_id in self.grudge_list:
            return Move.CHEAT

        return Move.COOPERATE

    def update(self,
               opponent_unique_id: str,
               my_intended_move: Move,
               my_actual_move: Move,
               opponent_intended_move: Move,  # <-- 這是 "真實" 意圖
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

        if opponent_unique_id in self.grudge_list:
            return

        # --- 【渾沌機制】---
        # 1. 判斷 "感知" 到的意圖

        perceived_intent = opponent_intended_move  # 預設 = 真實意圖

        if random.random() < self.P_MISJUDGE:
            # 誤判發生！翻轉感知
            if opponent_intended_move == Move.COOPERATE:
                perceived_intent = Move.CHEAT
            else:
                perceived_intent = Move.COOPERATE

        # --- Redeemer 邏輯 (現在完全基於 "perceived_intent") ---

        current_strikes = self.strike_counts.get(opponent_unique_id, 0)

        # 2. 【救贖機制】(基於感知)
        #    (我們假設自己的意圖是可信的)
        if my_intended_move == Move.COOPERATE and \
           perceived_intent == Move.COOPERATE:  # <-- 使用 "感知"
            current_strikes = max(0, current_strikes - 1)

        # 3. 【記點機制】(基於感知)
        if perceived_intent == Move.CHEAT:  # <-- 使用 "感知"
            current_strikes += 1

        # 4. 【黑名單】 (邏輯不變)
        if current_strikes >= self.STRIKE_LIMIT:
            self.grudge_list.add(opponent_unique_id)
            if opponent_unique_id in self.strike_counts:
                del self.strike_counts[opponent_unique_id]
        else:
            self.strike_counts[opponent_unique_id] = current_strikes

    def reset(self):
        super().reset()
        self.grudge_list = set()
        self.strike_counts = {}

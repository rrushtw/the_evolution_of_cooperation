import random
from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class SkepticalRedeemer(BaseStrategy):
    """
    多疑的救贖者 (Skeptical Redeemer)

    【您修改後的版本：雙重誤判】
    這個策略在兩個方向上都會誤判：
    1. (False Negative) 有 75% 機率 "錯放" 真正的惡意。
    2. (False Positive) 有 25% 機率 "誤判" 無辜的意外。
    """

    STRIKE_LIMIT = 3

    # 誤判率 (同時也是錯放率 1.0 - 0.25 = 0.75)
    P_MISTRUST = 0.25

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

        if opponent_unique_id in self.grudge_list:
            return

        current_strikes = self.strike_counts.get(opponent_unique_id, 0)

        # 1. 【救贖機制】(看意圖)
        if my_intended_move == Move.COOPERATE and \
           opponent_intended_move == Move.COOPERATE:
            current_strikes = max(0, current_strikes - 1)

        # 2. 【記點機制 - 錯放有罪】
        #    如果對手 "打算" 背叛 (懷有惡意)
        if opponent_intended_move == Move.CHEAT:
            # 只有 25% 的機率 "正確" 記點
            # (有 75% 的機率 "誤判" 並放過)
            if random.random() < self.P_MISTRUST:
                current_strikes += 1

        # 3. 【懷疑機制 - 誤判無辜】
        #    如果 "意圖" 是合作, 但 "實際" 是背叛 (意外)
        elif opponent_intended_move == Move.COOPERATE and \
                opponent_actual_move == Move.CHEAT:

            # 有 25% 的機率 "誤判" 並懲罰無辜者
            if random.random() < self.P_MISTRUST:
                current_strikes += 1

        # (檢查黑名單的邏輯保持不變)
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

import random
from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class StochasticPavlov(BaseStrategy):
    """
    隨機巴甫洛夫 (Stochastic Pavlov) / 猶豫的巴甫洛夫

    這是 Pavlov 的 "機率性" 變體。

    規則：
    1. "贏-定" (Win-Stay) 邏輯 100% 不變。
    2. "輸-變" (Lose-Shift) 邏輯是機率性的：
       a. (Sucker, C->D): 有 P_RETALIATE (例如 90%) 的機率切換。
       b. (Punishment, D->C): 有 P_RECONCILE (例如 80%) 的機率切換。
    """

    # 90% 的機率 "報復" (C -> D)
    P_RETALIATE = 0.9

    # 80% 的機率 "和解" (D -> C)
    P_RECONCILE = 0.8

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        private_history_list = self.opponent_history.get(
            opponent_unique_id, [])

        if not private_history_list:
            # 第一回合，總是合作
            return Move.COOPERATE

        last_record = private_history_list[-1]
        my_last_move = last_record["my_actual_move"]
        last_result = last_record["match_result"]

        # 1. --- 贏-定 (Win-Stay) ---
        #    (100% 確定性)
        if last_result == MatchResult.REWARD or last_result == MatchResult.TEMPTATION:
            return my_last_move

        # 2. --- 輸-變 (Lose-Shift) ---
        #    (機率性)

        # 情況 A: 上次是 SUCKER (我出了 C)
        if my_last_move == Move.COOPERATE:
            # 檢查是否 "報復"
            if random.random() < self.P_RETALIATE:
                return Move.CHEAT  # (Shift)
            else:
                return Move.COOPERATE  # (Stay - 猶豫了)

        # 情況 B: 上次是 PUNISHMENT (我出了 D)
        else:  # my_last_move == Move.CHEAT
            # 檢查是否 "和解"
            if random.random() < self.P_RECONCILE:
                return Move.COOPERATE  # (Shift)
            else:
                return Move.CHEAT  # (Stay - 猶豫了)

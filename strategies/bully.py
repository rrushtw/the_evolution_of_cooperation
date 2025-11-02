from strategies.base_strategy import BaseStrategy
from definitions import Move


class Bully(BaseStrategy):
    """
    霸凌者 (Bully) / 諂媚者 (Sycophant)

    規則：
    1. 比較 "自己" 和 "對手" 的 "全局平均分"。
    2. 如果對手平均分 "低於" 自己 -> "霸凌" (CHEAT)。
    3. 如果對手平均分 "高於或等於" 自己 -> "諂媚" (COOPERATE)。

    這是一個 "社會階層攀爬者"，它會自動巴結勝利組，
    並攻擊失敗組。
    """

    # 至少需要 N 筆數據才開始判斷
    MIN_DATA_THRESHOLD = 20

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 檢查是否有足夠數據
        my_total_interactions = len(self.my_history)
        opponent_total_interactions = len(opponent_history)

        if my_total_interactions < self.MIN_DATA_THRESHOLD or \
           opponent_total_interactions < self.MIN_DATA_THRESHOLD:
            return Move.COOPERATE  # 數據不足，先合作

        # 2. 計算我自己的平均分 (O(1))
        my_avg_score = self.total_score / my_total_interactions

        # 3. 計算對手的平均分 (O(1))
        opp_avg_score = opponent_total_score / opponent_total_interactions

        # 4. 【霸凌/諂媚 決策】
        if my_avg_score > opp_avg_score:
            # 4a. 對方比我弱 -> "霸凌"
            return Move.CHEAT
        else:
            # 4b. 對方比我強 (或平手) -> "諂媚"
            return Move.COOPERATE

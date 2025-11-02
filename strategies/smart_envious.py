from strategies.base_strategy import BaseStrategy
from definitions import Move


class SmartEnvious(BaseStrategy):
    """
    精明的嫉妒者 (SmartEnvious Strategy) - 統計優化版

    規則：
    1. 預設保持合作 (COOPERATE)。
    2. 比較自己和對手的 "全局平均分"。
    3. 如果對手平均分高於自己 ("嫉妒" 觸發)：
       a. 統計對手的 "手滑意圖作弊率" (slipped cheat rate)。
       b. 如果作弊率 "低於" 3% (CHEAT_RATE_THRESHOLD)，
          則判定對方為 "養分" (AlwaysCooperate)，並 "攻擊" (CHEAT)。
       c. 否則 (作弊率高於 3%)，
          則判定對方為 "危險" (會還手)，並 "壓抑" 嫉妒 (COOPERATE)。
    """

    # 閾值：AlwaysCooperate 固有的 "內部雜訊" 是 2%
    # 任何高於 3% 的都代表 "會報復" 或 "有惡意"
    CHEAT_RATE_THRESHOLD = 0.03

    # 至少需要 N 筆數據才開始統計，避免早期誤判
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

        # 2. 計算我自己的平均分
        my_avg_score = self.total_score / my_total_interactions

        # 3. 計算對手的平均分 (O(1))
        opp_avg_score = opponent_total_score / opponent_total_interactions

        # 4. 檢查 "嫉妒" 觸發條件
        if opp_avg_score > my_avg_score:

            # --- 5. 統計分析對手的 "作弊率" ---

            opponent_cheats = 0
            for record in opponent_history:
                # 檢查對手 "說出口的" 意圖 (即 my_intended_move in their history)
                if record['my_intended_move'] == Move.CHEAT:
                    opponent_cheats += 1

            opponent_slipped_cheat_rate = opponent_cheats / opponent_total_interactions

            # --- 6. 精明決策 ---

            if opponent_slipped_cheat_rate < self.CHEAT_RATE_THRESHOLD:
                # 5a. 對方是 "和平主義者" (AlwaysCooperate)。
                #     釋放嫉妒，開始剝削！
                return Move.CHEAT
            else:
                # 5b. 對方是 "戰士" (Fighter)。壓抑嫉妒。
                return Move.COOPERATE

        # 7. 預設：保持合作
        return Move.COOPERATE

from strategies.base_strategy import BaseStrategy
from definitions import Move


class Statistical(BaseStrategy):
    """
    統計者 (Statistical) / 滑動窗口策略

    規則：
    1. 預設合作 (善良)。
    2. 會持續觀察對手 "最近 N 回合" (例如 10 回合) 的 "實際" 合作率。
    3. 如果對手的合作率 "低於" 一個閾值 (例如 60%)，
       就判定對方為 "壞人" (或 "隨機者")，並開始背叛。
    4. 如果對手合作率回升，則會再次合作。
    """

    # --- 您可以調整這些參數 ---
    LOOKBACK_WINDOW = 10  # 觀察 "最近 10 回合"
    COOPERATION_THRESHOLD = 0.6  # 合作率必須 "大於等於 60%"
    # ---------------------------

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 取得 "私怨" 列表
        private_history_list = self.opponent_history.get(
            opponent_unique_id, [])

        # 2. 檢查歷史是否足夠長
        #    如果不足 (例如剛開局)，則保持合作
        if len(private_history_list) < self.LOOKBACK_WINDOW:
            return Move.COOPERATE

        # 3. 只看 "最近" 的 N 筆紀錄
        recent_records = private_history_list[-self.LOOKBACK_WINDOW:]

        # 4. 統計對手在 "實際" 遊戲中合作了幾次
        #    (您也可以改成 "opponent_intended_move" 來使其免疫雜訊)
        opponent_coop_count = sum(
            1 for record in recent_records
            if record["opponent_actual_move"] == Move.COOPERATE
        )

        # 5. 計算合作率
        opponent_coop_rate = opponent_coop_count / self.LOOKBACK_WINDOW

        # 6. 做出決策
        if opponent_coop_rate >= self.COOPERATION_THRESHOLD:
            # 對手是 "好人"，合作
            return Move.COOPERATE
        else:
            # 對手是 "壞人" (或太隨機)，背叛
            return Move.CHEAT

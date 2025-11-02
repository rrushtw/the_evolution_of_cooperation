import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class SmartProber(BaseStrategy):
    """
    智慧試探者 (SmartProber) - "更精明" 的版本

    規則：
    1. 偽裝 (R1-3): 先合作 3 回合 (偽裝成 "善良")。
    2. 試探 (R4): 在第 4 回合故意背叛 (D)。
    3. 分類 (R5):
       a. 如果對手在 R4 報復 (D) -> 標記為 "Responsive" (好人)。
       b. 如果對手在 R4 容忍 (C) -> 標記為 "Exploitable" (傻瓜)。
    4. 行動 (R5+):
       a. 對 "Responsive": 永久切換到 GenerousTitForTat 邏輯。
       b. 對 "Exploitable": 永久出 CHEAT。
    5. 【關鍵】重新評估:
       在 "Exploitable" 模式下，如果對手 "曾經" (ever) 報復了 (D)，
       立刻將其移至 "Responsive" 名單，並切換到 GTFT 邏輯。
    """

    PROBE_ROUND = 3  # 在第 3 回合後 (即第 4 回合) 進行試探

    # 用於 "Responsive" 狀態的 GTFT 邏輯
    P_GENEROUS = 0.1

    def __init__(self):
        super().__init__()
        # 狀態 1: "可敬的對手" (切換到 GTFT)
        self.responsive_list = set()
        # 狀態 2: "可剝削者" (永遠背叛)
        self.exploitable_list = set()

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 檢查是否已分類
        if opponent_unique_id in self.responsive_list:
            # --- 狀態 1: 可敬的對手 (扮演 GTFT) ---
            return self._play_generous_tft(opponent_history)

        if opponent_unique_id in self.exploitable_list:
            # --- 狀態 2: 可剝削者 (持續背叛) ---
            return self._play_exploiter(opponent_unique_id, opponent_history)

        # --- 狀態 0: 尚未分類 (執行試探) ---
        return self._play_probing_phase(opponent_unique_id, opponent_history)

    def _play_probing_phase(self, opp_id, history):
        """處理 R1-R5 的試探和分類"""
        current_round = len(history)

        # R1-3: 偽裝成好人
        if current_round < self.PROBE_ROUND:
            return Move.COOPERATE

        # R4: 試探
        if current_round == self.PROBE_ROUND:
            return Move.CHEAT

        # R5: 分析 R4 的結果並分類
        # (我們在第 5 回合才分析第 4 回合的結果)
        if current_round == (self.PROBE_ROUND + 1):

            last_record = history[-1]  # R4 的紀錄
            opponent_response = last_record["opponent_actual_move"]

            if opponent_response == Move.CHEAT:
                # 4a. 對方報復了 -> 標記為 "Responsive"
                self.responsive_list.add(opp_id)
                return self._play_generous_tft(history)  # 切換到 GTFT
            else:
                # 4b. 對方容忍了 -> 標記為 "Exploitable"
                self.exploitable_list.add(opp_id)
                return Move.CHEAT  # 開始剝削

        # (R5 之後的罕見情況，如果分類失敗)
        return Move.COOPERATE

    def _play_exploiter(self, opp_id, history):
        """
        扮演剝削者 (永遠 D)，但持續監視
        """
        # 5. 【關鍵】重新評估
        # 檢查 "剝削" 期間，對手是否 "曾經" 反抗過

        # (我們只檢查 R4 之後的歷史, 因為 R4 之前我們是 C)
        relevant_history = history[self.PROBE_ROUND:]

        for record in relevant_history:
            if record["opponent_actual_move"] == Move.CHEAT:
                # 找到了！他醒了！(例如 TolerantGrudger 在 3 次後醒了)
                # print(f"DEBUG: SmartProber 發現 {opp_id} 醒了!")
                self.exploitable_list.remove(opp_id)
                self.responsive_list.add(opp_id)
                return self._play_generous_tft(history)  # 切換到 GTFT

        # 如果還沒醒，繼續剝削
        return Move.CHEAT

    def _play_generous_tft(self, history):
        """扮演 Generous Tit-for-Tat"""
        if not history:
            return Move.COOPERATE

        last_record = history[-1]
        opponent_last_actual_move = last_record["opponent_actual_move"]

        my_intended_move = opponent_last_actual_move  # TFT 邏輯

        if my_intended_move == Move.CHEAT:
            if random.random() < self.P_GENEROUS:
                return Move.COOPERATE  # 慷慨

        return my_intended_move

    def reset(self):
        super().reset()
        self.responsive_list = set()
        self.exploitable_list = set()

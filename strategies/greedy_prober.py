import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class GreedyProber(BaseStrategy):
    """
    貪婪的試探者 (GreedyProber)

    這是 SmartProber 和 Joss 的結合體。
    它會試探並分類對手。

    - 對 "傻瓜" (Exploitable): 永遠背叛。
    - 對 "好人" (Responsive): 扮演 GenerousTitForTat，
      但 "額外" 增加了 10% 的 "Joss 偷襲" 機率。
    """

    PROBE_ROUND = 3

    # 用於 "Responsive" 狀態
    P_GENEROUS = 0.1  # 10% 慷慨 (TFT 邏輯)
    P_SNEAKY = 0.1   # 10% 偷襲 (Joss 邏輯)

    def __init__(self):
        super().__init__()
        self.responsive_list = set()
        self.exploitable_list = set()

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 檢查是否已分類: 可敬的對手
        if opponent_unique_id in self.responsive_list:
            return self._play_joss_tft(opponent_history)

        # 2. 檢查是否已分類: 可剝削者
        if opponent_unique_id in self.exploitable_list:
            return self._play_exploiter(opponent_unique_id, opponent_history)

        # 3. 尚未分類: 執行試探
        return self._play_probing_phase(opponent_unique_id, opponent_history)

    def _play_probing_phase(self, opp_id, history):
        """處理 R1-R5 的試探和分類"""
        current_round = len(history)

        if current_round < self.PROBE_ROUND:
            return Move.COOPERATE

        if current_round == self.PROBE_ROUND:
            return Move.CHEAT

        if current_round == (self.PROBE_ROUND + 1):
            last_record = history[-1]
            opponent_response = last_record["opponent_actual_move"]

            if opponent_response == Move.CHEAT:
                self.responsive_list.add(opp_id)
                return self._play_joss_tft(history)  # 切換到 JOSS+TFT
            else:
                self.exploitable_list.add(opp_id)
                return Move.CHEAT

        return Move.COOPERATE

    def _play_exploiter(self, opp_id, history):
        """
        扮演剝削者 (永遠 D)，但持續監視
        (同 SmartProber)
        """
        relevant_history = history[self.PROBE_ROUND:]

        for record in relevant_history:
            if record["opponent_actual_move"] == Move.CHEAT:
                # 醒了！
                self.exploitable_list.remove(opp_id)
                self.responsive_list.add(opp_id)
                return self._play_joss_tft(history)  # 切換到 JOSS+TFT

        return Move.CHEAT

    def _play_joss_tft(self, history):
        """
        【關鍵】扮演 GTFT + Joss
        """
        if not history:
            return Move.COOPERATE

        last_record = history[-1]
        opponent_last_actual_move = last_record["opponent_actual_move"]

        # 1. TFT 邏輯
        my_intended_move = opponent_last_actual_move

        # 2. GTFT "慷慨" 邏輯
        if my_intended_move == Move.CHEAT:
            if random.random() < self.P_GENEROUS:
                return Move.COOPERATE  # 慷慨

        # 3. Joss "偷襲" 邏輯
        if my_intended_move == Move.COOPERATE:
            if random.random() < self.P_SNEAKY:
                return Move.CHEAT  # 偷襲!

        return my_intended_move

    def reset(self):
        super().reset()
        self.responsive_list = set()
        self.exploitable_list = set()

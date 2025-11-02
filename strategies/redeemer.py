from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class Redeemer(BaseStrategy):
    """
    救贖者 (Redeemer) / 寬容記點策略

    規則：
    1. 預設保持合作 (善良)。
    2. 內部有一個 "記點" 系統 (strike_counts)，記錄對手 "總共" 背叛了幾次。
    3. 如果對手背叛 (CHEAT)，記點 +1。
    4. 【救贖機制】如果雙方 "相互合作" (REWARD)，則記點 -1 (抵銷一筆)。
    5. 【黑名單】一旦 "總記點" 達到 3 次，
       則將此對手加入黑名單，並永遠對其背叛。

    (此策略只看 "私怨"，忽略傳入的 opponent_history)
    """

    STRIKE_LIMIT = 3  # 記點 3 次觸發

    def __init__(self):
        super().__init__()
        # "黑名單" (Grudge list)
        self.grudge_list = set()
        # "記點" 系統 (Strike count)
        # 結構: {'opponent_name': 1, ...}
        self.strike_counts = {}

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 檢查這個對手是否已在我的 "黑名單" 上
        if opponent_unique_id in self.grudge_list:
            return Move.CHEAT

        # 2. 如果不在黑名單上，預設合作 (等待 update 更新記點)
        return Move.COOPERATE

    def update(self,
               opponent_unique_id: str,
               my_intended_move: Move,
               my_actual_move: Move,
               opponent_intended_move: Move,
               opponent_actual_move: Move,
               match_result: MatchResult):
        """
        覆寫 (Override) BaseStrategy 的 update 方法來更新記點。
        """

        # 1. 【重要】必須呼叫 super().update()
        #    這樣 BaseStrategy 才能儲存歷史 (history) 和更新總分 (total_score)
        super().update(
            opponent_unique_id,
            my_intended_move,
            my_actual_move,
            opponent_intended_move,
            opponent_actual_move,
            match_result
        )

        # 2. 如果已在黑名單，則不再更新記點
        if opponent_unique_id in self.grudge_list:
            return

        # 3. 取得當前的記點 (預設 0)
        current_strikes = self.strike_counts.get(opponent_unique_id, 0)

        # 4. 【救贖機制】
        #    如果我們 "相互合作"，則抵銷一次記點
        if match_result == MatchResult.REWARD:
            current_strikes = max(0, current_strikes - 1)  # 減 1, 但不低於 0

        # 5. 【記點機制】
        #    如果對手 "實際" 背叛了
        if opponent_actual_move == Move.CHEAT:
            current_strikes += 1

        # 6. 【黑名單觸發】
        #    檢查記點是否已達上限
        if current_strikes >= self.STRIKE_LIMIT:
            self.grudge_list.add(opponent_unique_id)
            # (可選) 觸發後清除記點，節省記憶體
            if opponent_unique_id in self.strike_counts:
                del self.strike_counts[opponent_unique_id]
        else:
            # 7. 儲存更新後的記點
            self.strike_counts[opponent_unique_id] = current_strikes

    def reset(self):
        """
        重置錦標賽時，也要清空 "黑名單" 和 "記點"
        """
        super().reset()
        self.grudge_list = set()
        self.strike_counts = {}

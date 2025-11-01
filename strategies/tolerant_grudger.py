from strategies.base_strategy import BaseStrategy
from definitions import Move


class TolerantGrudger(BaseStrategy):
    """
    寬容的怨恨者 (Tolerant Grudger) / 三振出局 (Three Strikes)

    規則：
    1. 保持合作 (善良)。
    2. 會持續檢查對手 "最近 3 回合" 的 "實際" 出招。
    3. 如果對手 "連續 3 次" 都選擇背叛 (CHEAT)，
       則將此對手加入黑名單，並永遠對其背叛。

    (此策略只看 "私怨"，忽略傳入的 opponent_history)
    """

    STRIKE_LIMIT = 3  # 連續背叛 3 次觸發

    def __init__(self):
        super().__init__("Tolerant Grudger")
        # 用一個 set 來儲存 "黑名單"
        self.grudge_list = set()

    def play(self, opponent_unique_id: str, opponent_history: list[dict]) -> Move:

        # 1. 檢查這個對手是否已在我的 "黑名單" 上
        if opponent_unique_id in self.grudge_list:
            return Move.CHEAT

        # 2. 取得 "私怨" 列表
        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        # 3. 檢查是否有足夠的歷史來觸發 (必須至少 3 回合)
        if len(private_history_list) < self.STRIKE_LIMIT:
            # 歷史不足，繼續合作
            return Move.COOPERATE

        # 4. 只檢查 "最近的 3 回合"
        recent_records = private_history_list[-self.STRIKE_LIMIT:]

        # 5. 檢查是否 "全部" 都是背叛
        # (我們使用 all() 產生器來快速檢查)
        is_consecutive_cheat = all(
            record["opponent_actual_move"] == Move.CHEAT
            for record in recent_records
        )

        if is_consecutive_cheat:
            # 6. 觸發！三振出局
            # print(f"DEBUG: {self.name} 將 {opponent_unique_id} 加入黑名單!")
            self.grudge_list.add(opponent_unique_id)
            return Move.CHEAT

        # 7. 如果未觸發，則繼續合作
        return Move.COOPERATE

    def reset(self):
        """
        重置錦標賽時，也要清空 "黑名單"
        """
        super().reset()
        self.grudge_list = set()

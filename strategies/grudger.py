from strategies.base_strategy import BaseStrategy
from definitions import Move


class Grudger(BaseStrategy):
    """
    怨恨者 (Grudger) / 恐怖策略 (Grim Trigger)

    規則：
    1. 永遠先合作。
    2. 只要對手 (在 "私怨" 歷史中) 曾經背叛過 "一次"，
       就永遠對這個對手背叛。

    (此策略只看 "私怨"，忽略傳入的 opponent_history)
    """

    def __init__(self):
        super().__init__()
        # 用一個 set 來儲存 "我恨誰" (我對誰懷恨在心)
        self.grudge_list = set()

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 檢查這個對手是否已在我的 "黑名單" 上
        if opponent_unique_id in self.grudge_list:
            return Move.CHEAT

        # 2. 如果不在黑名單上，檢查 "私怨" 歷史
        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        # 3. 掃描 "所有" 過去的回合
        for record in private_history_list:
            if record["opponent_actual_move"] == Move.CHEAT:
                # 4. 找到了！對手曾經背叛過
                #    將他加入黑名單，並從這回合開始永遠背叛
                self.grudge_list.add(opponent_unique_id)
                return Move.CHEAT

        # 5. 如果歷史清白，且不在黑名單上，則合作
        return Move.COOPERATE

    def reset(self):
        """
        重置錦標賽時，也要清空 "黑名單"
        """
        super().reset()
        self.grudge_list = set()

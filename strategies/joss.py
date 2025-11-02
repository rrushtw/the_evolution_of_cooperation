import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class Joss(BaseStrategy):
    """
    Joss (狡猾的策略 / 偷襲者)

    規則：
    1. 基本上是 TitForTat (複製對手上一回合的 "實際" 出招)。
    2. 【關鍵】當它 "決定要合作" 時 (因為對手上一回合也合作),
       它會有 P_SNEAKY (例如 10%) 的機率 "狡猾地" 偷襲，改為背叛。
    3. 這是一個 "Nasty" (不善良) 策略，旨在剝削過度善良的對手。
    """

    # 10% 的偷襲機率
    P_SNEAKY = 0.1

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        if not private_history_list:
            # 第一回合，合作 (它偽裝成 "善良" 策略)
            return Move.COOPERATE

        # 1. 取得對手上一回合的 "實際" 出招
        last_private_record = private_history_list[-1]
        opponent_last_actual_move = last_private_record["opponent_actual_move"]

        # 2. 執行 TFT 邏輯 (決定 "意圖")
        my_intended_move = opponent_last_actual_move

        # 3. 【偷襲機制】
        # 如果我的意圖是 "合作"
        if my_intended_move == Move.COOPERATE:
            # 檢查是否要 "偷襲"
            if random.random() < self.P_SNEAKY:
                # 偷襲觸發，改為背叛
                return Move.CHEAT

        # 4. 如果意圖是背叛，或偷襲未觸發，則執行原意圖
        return my_intended_move

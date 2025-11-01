import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class GenerousTitForTat(BaseStrategy):
    """
    慷慨的牙還牙 (Generous Tit-for-Tat, GTFT)

    規則：
    1. 基本上是 TitForTat (複製對手上一回合的 "實際" 出招)。
    2. 【關鍵】當它 "決定要背叛" (報復) 時，
       它會有 P_GENEROUS (例如 10%) 的機率 "慷慨地" 選擇合作。
    3. 這使它能 "主動" 打破因雜訊引起的死亡螺旋。
    """

    # 10% 的慷慨機率
    P_GENEROUS = 0.1

    def play(self, opponent_unique_id: str, opponent_history: list[dict]) -> Move:

        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        if not private_history_list:
            # 第一回合，合作
            return Move.COOPERATE

        # 1. 取得對手上一回合的 "實際" 出招
        last_private_record = private_history_list[-1]
        opponent_last_actual_move = last_private_record["opponent_actual_move"]

        # 2. 執行 TFT 邏輯 (決定 "意圖")
        my_intended_move = opponent_last_actual_move  # 複製

        # 3. 【慷慨機制】
        # 如果我的意圖是 "背叛" (報復)
        if my_intended_move == Move.CHEAT:
            # 檢查是否要 "慷慨"
            if random.random() < self.P_GENEROUS:
                # 慷慨觸發，改為合作
                return Move.COOPERATE

        # 4. 如果意圖是合作，或慷慨未觸發，則執行原意圖
        return my_intended_move

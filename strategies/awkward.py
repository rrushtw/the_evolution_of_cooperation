import random
from strategies.base_strategy import BaseStrategy
from definitions import Move


class Awkward(BaseStrategy):
    """
    尷尬的策略 (Awkward Strategy) / 笨拙的合作者

    這是一個 "內心善良" 但 "表達笨拙" 的策略。

    規則：
    1. 它的 "真實意圖" (play()) 永遠是 COOPERATE。
    2. 但是，它的 "內部雜訊" (apply_internal_noise())
       有機率會 "手滑"，將意圖翻轉為 CHEAT。
    """

    # "手滑" 的機率
    P_SLIP = 0.10

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict]
             ) -> Move:

        # 1. 我的 "真實意圖" 永遠是合作
        return Move.COOPERATE

    def apply_internal_noise(self, intended_move: Move) -> Move:
        """
        覆寫 "內部失誤" 方法。
        """

        # 2. 檢查是否 "手滑"
        if random.random() < self.P_SLIP:
            # 糟糕！我想合作，但 "說出口" 的卻是背叛
            return Move.CHEAT

        # 3. (30% 的機率) 成功表達了合作
        #    (intended_move 在這裡永遠是 COOPERATE)
        return intended_move

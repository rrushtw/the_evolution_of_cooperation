from strategies.base_strategy import BaseStrategy
from definitions import Move


class OmegaTitForTat(BaseStrategy):
    """
    Omega 以牙還牙 (Omega Tit-for-Tat, OmegaTFT)

    在普通 TFT 之上加兩個 per-opponent 計數器，專治 TFT 的兩個雜訊弱點：

    1. 死鎖 (deadlock)：雜訊讓雙方錯開步調 → C-D-D-C 互相報復的 echo
       死鎖。OmegaTFT 偵測對手最近兩手是否一直 "交替"，連續達
       DEADLOCK_THRESHOLD 次就 "主動合作一手" 打破死鎖（類似 GTFT
       的破螺旋，但只在偵測到死鎖時才出手，而非隨機）。

    2. 隨機 / 不可溝通對手：對手行為若長期 "飄忽不定"（兩手老是交替、
       對我的合作毫無回應），TFT 會被持續佔便宜。OmegaTFT 用
       randomness_counter 累積 "亂度"，超過 RANDOMNESS_THRESHOLD 就
       認定對手不可溝通，永久背叛（對純隨機對手 AllD 是最佳解）。

    其餘情況退回標準 TFT。計數器只看 per-opponent 私有歷史，
    在 play() 內依歷史確定性更新（每回合對每位對手呼叫一次）。
    採 Axelrod 函式庫的經典參數與邏輯。
    """

    DEADLOCK_THRESHOLD = 3
    RANDOMNESS_THRESHOLD = 8

    def __init__(self):
        super().__init__()
        self.deadlock_counter: dict[str, int] = {}
        self.randomness_counter: dict[str, int] = {}

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        private = self.opponent_history.get(opponent_unique_id, [])

        # R1：合作
        if not private:
            return Move.COOPERATE

        # 對手最近一手（實際出招）
        opp_last = private[-1]["opponent_actual_move"]

        # R2：純 TFT（資訊還不夠判斷死鎖/隨機）
        if len(private) == 1:
            return opp_last

        opp_prev = private[-2]["opponent_actual_move"]
        deadlock = self.deadlock_counter.get(opponent_unique_id, 0)
        randomness = self.randomness_counter.get(opponent_unique_id, 0)

        # --- 死鎖狀態：主動合作打破，並把計數推過門檻後歸零 ---
        if deadlock >= self.DEADLOCK_THRESHOLD:
            move = Move.COOPERATE
            if deadlock == self.DEADLOCK_THRESHOLD:
                # 再撐一手，下回合才歸零，確保確實送出一次合作訊號
                self.deadlock_counter[opponent_unique_id] = self.DEADLOCK_THRESHOLD + 1
            else:
                self.deadlock_counter[opponent_unique_id] = 0
            return move

        # --- 更新隨機度：對手持平→趨穩(-1，但不低於 0)，交替→偏亂(+1) ---
        if opp_last == opp_prev:
            if randomness > 0:
                randomness -= 1
        else:
            randomness += 1
        self.randomness_counter[opponent_unique_id] = randomness

        # 對手太隨機 → 永久背叛
        if randomness >= self.RANDOMNESS_THRESHOLD:
            return Move.CHEAT

        # --- 否則標準 TFT，同時更新死鎖計數 ---
        if opp_last != opp_prev:
            # 對手在 "交替"，可能正陷入 echo 死鎖
            self.deadlock_counter[opponent_unique_id] = deadlock + 1
        else:
            self.deadlock_counter[opponent_unique_id] = 0

        return opp_last

    def reset(self):
        super().reset()
        self.deadlock_counter = {}
        self.randomness_counter = {}

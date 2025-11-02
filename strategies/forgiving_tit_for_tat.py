from strategies.base_strategy import BaseStrategy
from definitions import Move


class ForgivingTitForTat(BaseStrategy):
    """
    寬容的牙還牙 (Forgiving Tit-for-Tat)

    與 TitForTat 幾乎相同，但有一個關鍵區別：
    它 "只看" 對手 "打算" (intended) 出什麼招，
    並 "忽略" 雜訊 (noise) 造成的 "實際" (actual) 結果。

    這使它在有雜訊的環境中極具彈性，不會陷入死亡螺旋。

    (此策略只看 "私怨"，忽略傳入的 opponent_history)
    """

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 1. 取得 "私怨" 列表
        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        if not private_history_list:
            # 2. 第一回合，總是合作 (保持 "善良")
            return Move.COOPERATE

        # 3. 取得上一回合的 "私怨" 紀錄 (dict)
        last_private_record = private_history_list[-1]

        # 4. 【關鍵點】
        #    - 標準 TFT 看的是:
        #      last_private_record["opponent_actual_move"]
        #
        #    - 本策略 (ForgivingTFT) 看的是:
        opponent_last_intended_move = last_private_record["opponent_intended_move"]

        # 5. 複製對手 "上回合的意圖"
        return opponent_last_intended_move

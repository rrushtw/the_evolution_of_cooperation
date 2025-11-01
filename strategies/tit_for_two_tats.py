from strategies.base_strategy import BaseStrategy
from definitions import Move


class TitForTwoTats(BaseStrategy):
    """
    兩報還一牙 (Tit-for-Two-Tats, TFTT)

    規則：
    1. 保持合作 (善良)。
    2. 只有當對手 "連續兩次" (在 "實際" 出招中) 都背叛時，
       才在下一回合背叛 "一次" 作為懲罰。
    3. 這使它能原諒 "單次" 的雜訊或背叛。
    """

    def __init__(self):
        super().__init__("Tit-for-Two-Tats")

    def play(self, opponent_unique_id: str, opponent_history: list[dict]) -> Move:

        private_history_list = self.opponent_history.get(opponent_unique_id, [])

        # 1. 檢查歷史是否足夠 (至少 2 回合)
        if len(private_history_list) < 2:
            return Move.COOPERATE

        # 2. 取得最近兩回合的紀錄
        last_record = private_history_list[-1]
        second_last_record = private_history_list[-2]

        # 3. 檢查對手是否 "連續兩次" 背叛
        if last_record["opponent_actual_move"] == Move.CHEAT and \
           second_last_record["opponent_actual_move"] == Move.CHEAT:

            # 觸發！報復一次
            return Move.CHEAT

        # 4. 如果沒有連續兩次背叛，則合作
        return Move.COOPERATE

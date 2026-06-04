from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult


class ContriteTitForTat(BaseStrategy):
    """
    懺悔的以牙還牙 (Contrite Tit-for-Tat, CTFT)

    專治 "雜訊引發的死亡螺旋"。普通 TFT 一旦自己手滑背叛 (內部 2% / 外部 5%
    雜訊)，就會跟對手陷入 C-D-C-D 無止盡互戕。CTFT 用 "聲望 (standing)" 機制
    分辨 "誰理虧"，主動為自己的失誤認錯。

    規則 (per-opponent 各自獨立計算)：
    1. 每個人 (我自己、對手) 都有 good / bad 兩種聲望，初始皆為 good。
    2. 一個 "動作" 是否 "正當 (justified)"：
       - 合作 → 永遠正當。
       - 背叛 → 只有在 "對方聲望是 bad" 時才正當 (正當報復)；
         若背叛了一個 good 聲望的對手 (不論是故意還是手滑) → 不正當。
    3. 做出 "不正當" 動作 → 聲望掉成 bad；做出 "正當" 動作 → 聲望回 good。
    4. 出招：只有在 "對手聲望 bad 且我自己聲望 good" 時才背叛；其餘一律合作。

    關鍵效果：
    - 我手滑背叛了 good 對手 → 我的聲望掉 bad。對手據此正當報復 (D)，
      對手聲望仍 good。我看到對手聲望 good → 不反報復，反而合作 "贖罪"，
      合作後我聲望回 good。雙方在 2 回合內回到互助，只損失 1 次報復。
    - 對真正的剝削者 (持續背叛 good 的我) → 對手聲望變 bad，我照常報復，
      不會被佔便宜。
    """

    def __init__(self):
        super().__init__()
        # True = good 聲望, False = bad 聲望
        self.my_standing: dict[str, bool] = {}
        self.opponent_standing: dict[str, bool] = {}

    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:

        # 預設聲望皆為 good (第一次遇到 / 尚無紀錄)
        my_good = self.my_standing.get(opponent_unique_id, True)
        opp_good = self.opponent_standing.get(opponent_unique_id, True)

        # 只有在 "對手理虧 (bad) 而我自己站得住腳 (good)" 時才報復
        if not opp_good and my_good:
            return Move.CHEAT

        # 其餘情況一律合作：
        # - 對手 good → 沒有報復的理由
        # - 我自己 bad → 先合作贖罪、把聲望賺回來
        return Move.COOPERATE

    def update(self,
               opponent_unique_id: str,
               my_intended_move: Move,
               my_actual_move: Move,
               opponent_intended_move: Move,
               opponent_actual_move: Move,
               match_result: MatchResult):

        # 1. 先讓 BaseStrategy 記錄歷史與總分
        super().update(
            opponent_unique_id,
            my_intended_move,
            my_actual_move,
            opponent_intended_move,
            opponent_actual_move,
            match_result
        )

        # 2. 取出 "本回合出招當下" 的聲望 (更新前的快照)，雙方都用它來判斷正當性
        my_good_before = self.my_standing.get(opponent_unique_id, True)
        opp_good_before = self.opponent_standing.get(opponent_unique_id, True)

        # 3. 用 "實際" 出招 (已含雜訊) 重新計算雙方聲望
        #    背叛只有在對方聲望 bad 時才正當；合作永遠正當。
        my_justified = (my_actual_move == Move.COOPERATE) or (not opp_good_before)
        opp_justified = (opponent_actual_move == Move.COOPERATE) or (not my_good_before)

        self.my_standing[opponent_unique_id] = my_justified
        self.opponent_standing[opponent_unique_id] = opp_justified

    def reset(self):
        super().reset()
        self.my_standing = {}
        self.opponent_standing = {}

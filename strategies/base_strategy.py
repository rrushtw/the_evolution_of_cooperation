# strategies/base_strategy.py
import abc
import uuid
from definitions import Move, MatchResult, PAYOFF  # 從根目錄的 definitions.py 匯入


class BaseStrategy(abc.ABC):
    """
    策略的抽象基底類別 (合約)

    紀錄內容包含：
    - 分數
    - 歷史
    """

    def __init__(self):
        self.unique_id = str(uuid.uuid4())  # 策略 "個體" 的唯一 ID

        # ( reset() 會被 super() 呼叫 )
        self.reset()

    def reset(self):
        # 歷史紀錄的 "key" 現在必須是 unique_id
        self.opponent_history: dict[str, list[dict]] = {}
        self.my_history: list[dict] = []
        self.total_score: int = 0

    @abc.abstractmethod
    def play(self,
             opponent_unique_id: str,
             opponent_history: list[dict]
             ) -> Move:
        """
        決定此回合 "打算" 出什麼招。
        Args:
            opponent_unique_id (str): 對手的 "個體" ID。
        """
        pass

    def update(self,
               opponent_unique_id: str,
               my_intended_move: Move,
               my_actual_move: Move,
               opponent_intended_move: Move,
               opponent_actual_move: Move,
               match_result: MatchResult):
        """
        由 'engine' 呼叫，用來告知此回合的 "最終" 結果。
        """

        round_record = {
            "my_intended_move": my_intended_move,
            "my_actual_move": my_actual_move,
            "opponent_intended_move": opponent_intended_move,
            "opponent_actual_move": opponent_actual_move,
            "match_result": match_result,
        }

        # 1. 依據 opponent 建立 match history
        if opponent_unique_id not in self.opponent_history:
            self.opponent_history[opponent_unique_id] = []

        self.opponent_history[opponent_unique_id].append(round_record)

        # 2. 建立自己的 match history
        self.my_history.append(round_record)

        # 3. 更新策略總分
        score = PAYOFF[match_result]
        self.total_score += score

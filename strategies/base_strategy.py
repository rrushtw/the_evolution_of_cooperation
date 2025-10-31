# strategies/base_strategy.py
import abc
from definitions import Move, MatchResult, PAYOFF  # 從根目錄的 definitions.py 匯入


class BaseStrategy(abc.ABC):
    """
    策略的抽象基底類別 (合約)

    紀錄內容包含：
    - 分數
    - 歷史
    """

    def __init__(self, name: str):
        self.name = name
        self.opponent_history: dict[str, list[dict]] = {}
        self.my_history: list[dict] = []
        self.total_score: int = 0

    def reset(self):
        self.opponent_history: dict[str, list[dict]] = {}
        self.my_history: list[dict] = []
        self.total_score: int = 0

    @abc.abstractmethod
    def play(self, opponent_id: str, opponent_history: list[dict]) -> Move:
        """
        決定此回合 "打算" 出什麼招。
        """
        pass

    def update(self,
               opponent_id: str,
               my_intended_move: Move,
               my_actual_move: Move,
               opponent_intended_move: Move,
               opponent_actual_move: Move,
               match_result: MatchResult):
        """
        由 'engine' 呼叫，用來告知此回合的 "最終" 結果。
        """

        # 1. 依據 opponent 建立 match history
        if opponent_id not in self.opponent_history:
            self.opponent_history[opponent_id] = []

        self.opponent_history[opponent_id].append({
            "my_intended_move": my_intended_move,
            "my_actual_move": my_actual_move,
            "opponent_intended_move": opponent_intended_move,
            "opponent_actual_move": opponent_actual_move,
            "match_result": match_result,
        })

        # 2. 建立自己的 match history
        self.my_history.append({
            "my_intended_move": my_intended_move,
            "my_actual_move": my_actual_move,
            "opponent_intended_move": opponent_intended_move,
            "opponent_actual_move": opponent_actual_move,
            "match_result": match_result,
        })

        # 3. 更新策略總分
        score = PAYOFF[match_result]
        self.total_score += score

    def __str__(self):
        return self.name

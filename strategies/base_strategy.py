# strategies/base_strategy.py
import abc
import random
import uuid
from definitions import Move, MatchResult, PAYOFF  # 從根目錄的 definitions.py 匯入


class BaseStrategy(abc.ABC):
    """
    策略的抽象基底類別 (合約)

    紀錄內容包含：
    - 分數
    - 歷史
    """

    P_INTERNAL_NOISE = 0.02  # 2% 內部雜訊

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
             opponent_history: list[dict],
             opponent_total_score: int,
             ) -> Move:
        """
        決定此回合 "打算" 出什麼招。
        Args:
            opponent_unique_id (str): 對手的 "個體" ID。
            opponent_history (list[dict]): 對手過往遊戲紀錄
            opponent_total_score (int): 對手當前總分
        """
        pass

    def apply_internal_noise(self, intended_move: Move) -> Move:
        """
        模擬 "內部雜訊"

        Args:
            intended_move (Move): 來自 play() 的 "真實意圖"。

        Returns:
            Move: "說出口的" 意圖 (Slipped Intent)。
        """
        if random.random() < self.P_INTERNAL_NOISE:
            # 2% 的機率 "手滑"
            return Move.CHEAT if intended_move == Move.COOPERATE else Move.COOPERATE

        return intended_move

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

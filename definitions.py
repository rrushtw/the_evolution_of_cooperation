from enum import Enum


class Move(Enum):
    """
    定義賽局中的可能行動
    - Cooperate: 合作
    - Cheat: 欺騙
    """
    COOPERATE = "Cooperate"  # 合作
    CHEAT = "Cheat"  # 欺騙


class MatchResult(Enum):
    """
    代表一回合中，單一玩家的 "結果"
    - R: Reward (獎勵) - 相互合作
    - T: Temptation (誘惑) - 你背叛了合作的對手
    - S: Sucker (傻瓜) - 你合作但被對手背叛
    - P: Punishment (懲罰) - 相互背叛
    """
    REWARD = "Reward"  # 相互合作
    TEMPTATION = "Temptation"  # 你背叛了合作的對手
    SUCKER = "Sucker"  # 你合作但被對手背叛
    PUNISHMENT = "Punishment"  # 相互背叛


PAYOFF = {
    MatchResult.TEMPTATION: 5,
    MatchResult.REWARD: 3,
    MatchResult.SUCKER: 0,
    MatchResult.PUNISHMENT: 1,
}

RESULT_MATRIX = {
    (Move.COOPERATE, Move.COOPERATE): (MatchResult.REWARD, MatchResult.REWARD),
    (Move.COOPERATE, Move.CHEAT): (MatchResult.SUCKER, MatchResult.TEMPTATION),
    (Move.CHEAT, Move.COOPERATE): (MatchResult.TEMPTATION, MatchResult.SUCKER),
    (Move.CHEAT, Move.CHEAT): (MatchResult.PUNISHMENT, MatchResult.PUNISHMENT),
}

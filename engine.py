import random
import itertools  # <-- 1. 匯入 itertools
from tqdm import tqdm  # <-- 2. 匯入 tqdm
from definitions import Move, RESULT_MATRIX
from strategies.base_strategy import BaseStrategy


def play_game(strategy1: BaseStrategy, strategy2: BaseStrategy, rounds: int, noise: float = 0.0):
    """
    模擬兩個策略之間的一場對戰 (包含 N 回合)。

    Args:
        strategy1 (BaseStrategy): 玩家 1
        strategy2 (BaseStrategy): 玩家 2
        rounds (int): 此場對戰的回合數
        noise (float): 雜訊發生率 (0.0 到 1.0)。0.0 表示沒有雜訊。
    """

    for _ in range(rounds):
        # 1. & 2. 取得雙方的 "公開日誌" (public log)，這符合您的設計
        strategy1_history = strategy1.my_history
        strategy2_history = strategy2.my_history

        # 3. & 4. 取得雙方的 "意圖" 出招
        intended_move1 = strategy1.play(
            opponent_id=strategy2.name, opponent_history=strategy2_history)
        intended_move2 = strategy2.play(
            opponent_id=strategy1.name, opponent_history=strategy1_history)

        # 5. 處理雜訊 (Noise Module)
        actual_move1 = apply_noise(intended_move1, noise)
        actual_move2 = apply_noise(intended_move2, noise)

        # 6. 查詢 "語意結果"
        (result1, result2) = RESULT_MATRIX[(actual_move1, actual_move2)]

        # 7. & 8. 呼叫 update
        # 策略會 "自己" 內部更新分數和歷史 (根據 BaseStrategy 的設計)

        strategy1.update(
            opponent_id=strategy2.name,
            my_intended_move=intended_move1,
            my_actual_move=actual_move1,
            opponent_intended_move=intended_move2,
            opponent_actual_move=actual_move2,
            match_result=result1
        )

        # 【關鍵設計】
        # 如果 strategy1 和 strategy2 是同一個物件 (自己對自己)
        # 我們 "不能" 呼叫 strategy2.update()，
        # 否則 s1 (即 s2) 的分數會被加兩次。
        if strategy1 is not strategy2:
            strategy2.update(
                opponent_id=strategy1.name,
                my_intended_move=intended_move2,
                my_actual_move=actual_move2,
                opponent_intended_move=intended_move1,
                opponent_actual_move=actual_move1,
                match_result=result2
            )


def apply_noise(intended_move: Move, noise: float) -> Move:
    """
    根據雜訊率，隨機翻轉一個 Move。
    """
    if noise > 0 and random.random() < noise:
        # 雜訊發生，翻轉出招
        return Move.CHEAT if intended_move == Move.COOPERATE else Move.COOPERATE

    # 沒有雜訊，回傳原意圖
    return intended_move


def run_tournament(strategies: list[BaseStrategy], rounds_per_game: int, noise: float = 0.0):
    """
    舉辦一場循環賽 (Round-Robin Tournament)。

    Args:
        strategies (list[BaseStrategy]): 所有參賽的策略物件
        rounds_per_game (int): 每兩個策略之間對戰的回合數
        noise (float): 雜訊率
    """

    print(
        f"--- 開始循環賽 ({len(strategies)} 位參賽者, {rounds_per_game} 回合/場, {noise*100:.1f}% 雜訊) ---")

    # 1. 【關鍵】在 "整個錦標賽" 開始前，重置所有策略的狀態
    for strategy in strategies:
        strategy.reset()

    # --- 2. 使用 itertools 建立所有對戰組合 ---
    # 需要的 (n * (n+1) / 2) 場比賽
    pair_iterator = itertools.combinations_with_replacement(strategies, 2)

    # 計算總對戰場數, 供 tqdm 顯示
    n = len(strategies)
    total_matches = (n * (n + 1)) // 2

    # --- 3. 使用 tqdm 包裹 iterator ---
    progress_bar = tqdm(
        pair_iterator,
        total=total_matches,  # 總步數
        desc="  單世代循環賽",  # 進度條的標題
        leave=False,  # 進度條完成後會消失 (在世代循環中比較乾淨)
        unit=" 場"
    )

    # 4. 進行循環賽，從 "巢狀迴圈" 改為 "單迴圈"
    for s1, s2 in progress_bar:
        # 執行一場對戰 (s1 vs s2)
        play_game(s1, s2, rounds_per_game, noise)

    # 由於 progress_bar (leave=False) 會清除該行，我們加一個 \r
    print("\r--- 循環賽結束 ---")

    # 5. 分數已經在策略物件內部了，直接排序
    sorted_strategies = sorted(
        strategies, key=lambda s: s.total_score, reverse=True)

    return sorted_strategies

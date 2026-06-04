import random
from tqdm import tqdm
from definitions import Move, RESULT_MATRIX
from strategies.base_strategy import BaseStrategy


def apply_noise(intended_move: Move, noise: float) -> Move:
    """
    根據雜訊率，隨機翻轉一個 Move。
    """
    if noise > 0 and random.random() < noise:
        return Move.CHEAT if intended_move == Move.COOPERATE else Move.COOPERATE

    return intended_move


def run_tournament(strategies: list[BaseStrategy], rounds_per_game: int, avg_matches_per_strategy: int, noise: float = 0.0, collect_stats: bool = False):
    """
    互動制模型 (Interaction-Based Model)

    這是一個 "回合制" 的隨機社交模型。
    主迴圈不再是 "比賽 (Matches)"，而是 "單一互動 (Interactions)"。

    1. 總共模擬 N * M * R/2 次 "單一互動"。
    2. 每一次互動，隨機抽 2 人 (s1, s2) 只玩 "1 回合"。

    Args:
        collect_stats: 若為 True，額外統計本世代 "實際出招" 的合作率，
            回傳 (sorted_strategies, coop_rate)；預設 False 時只回傳
            sorted_strategies（與既有呼叫端完全相容）。
    """

    # 1. 重置所有策略
    for strategy in strategies:
        strategy.reset()

    # --- 2. 計算總 "單一互動" 次數 ---
    population_size = len(strategies)

    # 總 "完整比賽" 的場次
    total_matches = (population_size * avg_matches_per_strategy) // 2

    # 總 "單一互動" 次數
    total_interactions = total_matches * rounds_per_game

    print(
        f"--- 開始循環賽 ({len(strategies)} 位參賽者, {avg_matches_per_strategy} 場均/人, {noise*100:.1f}% 雜訊) ---")
    print(f"--- 總互動次數: {total_interactions} (隨機回合配對) ---")

    # 3. 使用 tqdm 包裹 "總互動次數"
    progress_bar = tqdm(
        range(total_interactions),
        desc="  世代演化中",
        leave=False,
        unit=" 互動"  # 單位是 "互動" 而非 "場"
    )

    # 合作率統計（僅 collect_stats=True 時累計）
    coop_count = 0
    move_count = 0

    # 4. 【隨機互動迴圈】(主迴圈)
    for _ in progress_bar:

        # 隨機"不重複"地抽出 2 個個體
        strategy1, strategy2 = random.sample(strategies, 2)

        # 取得雙方的 "意圖" 出招
        true_intent1 = strategy1.play(
            opponent_unique_id=strategy2.unique_id,
            opponent_history=strategy2.my_history,
            opponent_total_score=strategy2.total_score,
        )
        true_intent2 = strategy2.play(
            opponent_unique_id=strategy1.unique_id,
            opponent_history=strategy1.my_history,
            opponent_total_score=strategy1.total_score,
        )

        # 取得 "手滑後的意圖" (Slipped Intent)
        slipped_intent1 = strategy1.apply_internal_noise(true_intent1)
        slipped_intent2 = strategy2.apply_internal_noise(true_intent2)

        # 5. 處理雜訊
        actual_move1 = apply_noise(slipped_intent1, noise)
        actual_move2 = apply_noise(slipped_intent2, noise)

        # 6. 查詢 "語意結果"
        (result1, result2) = RESULT_MATRIX[(actual_move1, actual_move2)]

        # 合作率統計：看 "實際出招"（已含雜訊，即社會中真正發生的合作）
        if collect_stats:
            move_count += 2
            if actual_move1 == Move.COOPERATE:
                coop_count += 1
            if actual_move2 == Move.COOPERATE:
                coop_count += 1

        # 7. & 8. 【立刻更新】
        #    雙方的 "my_history" (情緒) 和 "total_score" 被即時更新
        strategy1.update(
            opponent_unique_id=strategy2.unique_id,
            my_intended_move=slipped_intent1,
            my_actual_move=actual_move1,
            opponent_intended_move=slipped_intent2,
            opponent_actual_move=actual_move2,
            match_result=result1
        )

        strategy2.update(
            opponent_unique_id=strategy1.unique_id,
            my_intended_move=slipped_intent2,
            my_actual_move=actual_move2,
            opponent_intended_move=slipped_intent1,
            opponent_actual_move=actual_move1,
            match_result=result2
        )

    print("\r--- 循環賽結束 ---")

    # 4. 依分數排序 (保持不變)
    sorted_strategies = sorted(
        strategies, key=lambda s: s.total_score, reverse=True)

    if collect_stats:
        coop_rate = coop_count / move_count if move_count else 0.0
        return sorted_strategies, coop_rate

    return sorted_strategies

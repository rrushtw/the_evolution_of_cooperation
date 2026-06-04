import collections
import engine
from strategies.base_strategy import BaseStrategy


def _get_final_ranking(final_counts: collections.Counter, extinction_order: list[str], stable: bool) -> list[str]:
    """
    根據最終狀態產生排名。
    規則:
    1. 存活者優先於滅絕者。
    2. (穩定狀態) 存活者之間，依數量排名。
    3. 滅絕者之間，依滅絕順序反向排名 (最先滅絕 = 最後一名)。
    """
    survivors = []

    if stable:
        # 穩定狀態下，依數量排序存活者
        sorted_survivors = sorted(
            final_counts.items(), key=lambda item: item[1], reverse=True)
        survivors = [name for name, count in sorted_survivors]
    else:
        # 非穩定狀態 (例如只剩一個贏家)，直接列出
        survivors = list(final_counts.keys())

    # 最終排名 = 存活者列表 + (反轉的)滅絕者列表
    final_ranking_list = survivors + list(reversed(extinction_order))
    return final_ranking_list


def _equilibrium_coop_rate(coop_rate_history: list[float], window: int) -> float:
    """均衡合作率 = 最後 min(window, 世代數) 代的平均（反映穩定後的社會樣態）。"""
    if not coop_rate_history:
        return 0.0
    tail = coop_rate_history[-window:]
    return sum(tail) / len(tail)


def run_evolution_simulation(
    strategy_types: list[type],  # <-- 傳入的是 "類別" (e.g., TitForTat)
    initial_copies: int,         # e.g., 10
    kill_count: int,             # e.g., 5
    rounds_per_game: int,
    avg_matches_per_strategy: int,
    noise: float,
    stability_threshold: int,    # e.g., 100
    collect_coop_stats: bool = False
):
    """
    執行一個完整的演化模擬。

    Args:
        collect_coop_stats: 若為 True，逐代蒐集 "實際出招合作率"，終止時
            以最後 min(stability_threshold, 世代數) 代的平均作為 "均衡合作率"，
            回傳 (final_ranking, equilibrium_coop_rate)；預設 False 時行為不變，
            只回傳 final_ranking（與既有呼叫端完全相容）。
    """
    print("--- 🚀 開始演化模擬 ---")
    print(f"設定: {len(strategy_types)} 種策略, 每種 {initial_copies} 個體")
    print(f"淘汰/補位: {kill_count}")
    print(f"場均: {avg_matches_per_strategy}")
    print(f"回合/場: {rounds_per_game}")
    print(f"雜訊: {noise*100:.1f}%")
    print(f"穩定閾值: {stability_threshold} 世代")
    print("---------------------------------")

    # --- 1. 初始化群體 (Initialize Population) ---
    # 建立一個包含 N * 10 = 70 個 "個體 (instances)" 的列表
    population: list[BaseStrategy] = []
    for s_type in strategy_types:
        for _ in range(initial_copies):
            population.append(s_type())

    generation = 0
    stability_counter = 0

    # --- 2. 在迴圈外, 先印出 "初始狀態" (世代 0) ---
    current_counts = collections.Counter(type(s).__name__ for s in population)
    current_surviving_types_set = set(current_counts.keys())

    print("\n--- 世代 0 (初始狀態) ---")
    print(f"存活: {len(current_surviving_types_set)} 種")
    for name, count in current_counts.most_common():
        print(f"  - {name:<20}: {count} 個體")

    last_surviving_types_set = current_surviving_types_set
    extinction_order: list[str] = []
    coop_rate_history: list[float] = []  # 逐代合作率（僅 collect_coop_stats=True 時）

    # --- 3. 世代主迴圈 (Main Loop) ---
    while True:
        generation += 1

        # --- 4. 評估 (Evaluation) ---
        # 呼叫 engine.py 為 "所有" 個體 (70個) 進行評分
        # sorted_population 是依分數排序的 "個體 (instances)" 列表
        if collect_coop_stats:
            sorted_population, gen_coop_rate = engine.run_tournament(
                population,
                rounds_per_game,
                avg_matches_per_strategy,
                noise,
                collect_stats=True
            )
            coop_rate_history.append(gen_coop_rate)
        else:
            sorted_population = engine.run_tournament(
                population,
                rounds_per_game,
                avg_matches_per_strategy,
                noise
            )

        # --- 5. 演化 (Selection/Reproduction) ---
        population = sorted_population[:-kill_count]
        top_templates = sorted_population[:kill_count]
        new_clones = [type(template)() for template in top_templates]
        population.extend(new_clones)

        # --- 6. 統計與追蹤 (列印 "演化後" 的結果) ---
        current_counts = collections.Counter(
            type(s).__name__ for s in population)
        # 當前存活的 "種類" set
        current_surviving_types_set = set(current_counts.keys())

        print(f"\n--- 世代 {generation} (演化後) ---")
        print(
            f"存活: {len(current_surviving_types_set)} 種 | 穩定度: {stability_counter}/{stability_threshold}")
        # 依數量排序印出
        for name, count in current_counts.most_common():
            print(f"  - {name:<20}: {count} 個體")

        # --- 7. 檢查滅絕 ---
        just_extinct = last_surviving_types_set - current_surviving_types_set
        if just_extinct:
            for name in just_extinct:
                extinction_order.append(name)
                print(f"!!! 💀 滅絕事件: {name} 已被淘汰 !!!")

        # --- 8. 檢查終止條件 ---
        if stability_counter >= stability_threshold:
            print("\n" + "="*40)
            print(f"🏁 模擬結束：生態系已達穩定狀態 (連續 {stability_threshold} 世代)")
            print("="*40)
            ranking = _get_final_ranking(current_counts, extinction_order, stable=True)
            if collect_coop_stats:
                return ranking, _equilibrium_coop_rate(coop_rate_history, stability_threshold)
            return ranking

        # 條件 2: 只剩一個贏家 (或全滅)
        if len(current_surviving_types_set) <= 1:
            print("\n" + "="*40)
            print("🏁 模擬結束：已產生最終勝利者")
            print("="*40)
            ranking = _get_final_ranking(current_counts, extinction_order, stable=False)
            if collect_coop_stats:
                return ranking, _equilibrium_coop_rate(coop_rate_history, stability_threshold)
            return ranking

        # --- 9. 【關鍵】更新穩定度計數器 ---
        #    (移到迴圈的 "最後", 在檢查完終止條件 "之後")
        if current_surviving_types_set == last_surviving_types_set:
            stability_counter += 1
        else:
            stability_counter = 0
            last_surviving_types_set = current_surviving_types_set

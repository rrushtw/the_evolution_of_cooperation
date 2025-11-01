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


def run_evolution_simulation(
    strategy_types: list[type],  # <-- 傳入的是 "類別" (e.g., TitForTat)
    initial_copies: int,         # e.g., 10
    kill_count: int,             # e.g., 5
    rounds_per_game: int,
    noise: float,
    stability_threshold: int     # e.g., 100
):
    """
    執行一個完整的演化模擬。
    """
    print("--- 🚀 開始演化模擬 ---")
    print(f"設定: {len(strategy_types)} 種策略, 每種 {initial_copies} 個體")
    print(
        f"淘汰/補位: {kill_count} | 雜訊: {noise*100:.1f}% | 穩定閾值: {stability_threshold} 世代")
    print("---------------------------------")

    # --- 1. 初始化群體 (Initialize Population) ---
    # 建立一個包含 N * 10 = 70 個 "個體 (instances)" 的列表
    population: list[BaseStrategy] = []
    for s_type in strategy_types:
        for _ in range(initial_copies):
            population.append(s_type())

    total_population = len(population)
    generation = 0
    stability_counter = 0
    # 儲存 "上次" 存活的策略種類 (set of names)
    last_surviving_types_set = set()
    # 記錄滅絕順序 (最先滅絕的, 放在最前面)
    extinction_order: list[str] = []

    # --- 2. 世代主迴圈 (Main Loop) ---
    while True:
        generation += 1

        # --- 3. 評估 (Evaluation) ---
        # 呼叫 engine.py 為 "所有" 個體 (70個) 進行評分
        # sorted_population 是依分數排序的 "個體 (instances)" 列表
        sorted_population = engine.run_tournament(
            population,
            rounds_per_game,
            noise
        )

        # --- 4. 統計與追蹤 (Track) ---
        # 統計當前群體中, 各 "種類" 的數量
        current_counts = collections.Counter(
            type(s).__name__ for s in population)
        # 當前存活的 "種類" set
        current_surviving_types_set = set(current_counts.keys())

        print(f"\n--- 世代 {generation} ---")
        print(
            f"存活: {len(current_surviving_types_set)} 種 | 穩定度: {stability_counter}/{stability_threshold}")
        # 依數量排序印出
        for name, count in current_counts.most_common():
            print(f"  - {name:<20}: {count} 個體")

        # --- 5. 檢查滅絕 (Check Extinction) ---
        # 找出 "上次還在, 這次不見" 的種類
        just_extinct = last_surviving_types_set - current_surviving_types_set
        if just_extinct:
            for name in just_extinct:
                extinction_order.append(name)  # 加入滅絕列表
                print(f"!!! 💀 滅絕事件: {name} 已被淘汰 !!!")

        # --- 6. 檢查終止條件 (Termination) ---

        # 條件 1: 生態系穩定 (您要求的 100 輪)
        if current_surviving_types_set == last_surviving_types_set:
            stability_counter += 1
        else:
            stability_counter = 0  # 重置計數器
            last_surviving_types_set = current_surviving_types_set  # 更新

        if stability_counter >= stability_threshold:
            print("\n" + "="*40)
            print("🏁 模擬結束：生態系已達穩定狀態")
            print("="*40)
            return _get_final_ranking(current_counts, extinction_order, stable=True)

        # 條件 2: 只剩一個贏家 (或全滅)
        if len(current_surviving_types_set) <= 1:
            print("\n" + "="*40)
            print("🏁 模擬結束：已產生最終勝利者")
            print("="*40)
            return _get_final_ranking(current_counts, extinction_order, stable=False)

        # --- 7. 演化 (Evolution) ---

        # a) 淘汰 (Selection)
        # 移除分數最低的 5 個 "個體"
        population = sorted_population[:-kill_count]  # 保留分數高的

        # b) 補位 (Reproduction)
        # 複製分數最高的 5 個 "個體" 的 "種類"
        top_templates = sorted_population[:kill_count]
        new_clones = [type(template)() for template in top_templates]

        # 將 5 個新個體加入群體, 維持總數
        population.extend(new_clones)

        # 檢查總數是否恆定 (除錯用)
        if len(population) != total_population:
            print(f"警告: 群體數量異常! {len(population)}")

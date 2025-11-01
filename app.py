import importlib
import inspect
from pathlib import Path

# 1. 匯入 simulation 引擎
import simulation
# 2. 需要 BaseStrategy 來做類型檢查
from strategies.base_strategy import BaseStrategy


def load_strategy_types(directory: str) -> list[type]:
    """
    動態載入指定目錄下的所有策略 "類別 (Types)"。
    """
    strategy_types = []
    strategy_path = Path(directory)
    module_prefix = strategy_path.name

    for py_file in strategy_path.glob("*.py"):
        if py_file.name in ["__init__.py", "base_strategy.py"]:
            continue

        module_name = f"{module_prefix}.{py_file.stem}"

        try:
            module = importlib.import_module(module_name)

            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseStrategy) and \
                   cls is not BaseStrategy and \
                   cls.__module__ == module_name:

                    # 傳回 "類別 (cls)" 本身, 而不是 "實體 (cls())"
                    strategy_types.append(cls)
                    print(f"[Loader] 找到策略類別: {cls.__name__}")

        except ImportError as e:
            print(f"[Loader] 錯誤：無法匯入 {module_name}: {e}")

    return strategy_types


if __name__ == "__main__":

    # --- 1. 載入 "策略類別" ---
    print("--- 正在從 'strategies/' 目錄載入策略 ---")
    strategy_types_list = load_strategy_types("strategies")
    print(f"--- 成功找到 {len(strategy_types_list)} 種策略 ---\n")

    # --- 2. 設定演化參數 ---
    INITIAL_COPIES_PER_TYPE = 6
    KILL_AND_REPRODUCE_COUNT = 5
    ROUNDS_PER_GAME = 200
    STABILITY_THRESHOLD = 10

    # --- 3. 執行無雜訊的 "演化" ---
    noise_zero = 0.0
    final_ranking_zero_noise = simulation.run_evolution_simulation(
        strategy_types=strategy_types_list,
        initial_copies=INITIAL_COPIES_PER_TYPE,
        kill_count=KILL_AND_REPRODUCE_COUNT,
        rounds_per_game=ROUNDS_PER_GAME,
        noise=noise_zero,
        stability_threshold=STABILITY_THRESHOLD
    )

    # (第一次印出, 會被洗掉)
    print("\n" + "🏆"*20)
    print("=== 最終演化排名 (無雜訊) ===")
    for i, name in enumerate(final_ranking_zero_noise):
        print(f"#{i+1:<3} {name}")
    print("🏆"*20)

    # --- 4. 執行有雜訊的 "演化" ---
    noise_noisy = 0.05
    print("\n\n" + "="*40 + "\n")

    final_ranking_noisy = simulation.run_evolution_simulation(
        strategy_types=strategy_types_list,
        initial_copies=INITIAL_COPIES_PER_TYPE,
        kill_count=KILL_AND_REPRODUCE_COUNT,
        rounds_per_game=ROUNDS_PER_GAME,
        noise=noise_noisy,
        stability_threshold=STABILITY_THRESHOLD
    )

    # (第二次印出, 會被洗掉)
    print("\n" + "🏆"*20)
    print(f"=== 最終演化排名 ({noise_noisy*100:.0f}% 雜訊) ===")
    for i, name in enumerate(final_ranking_noisy):
        print(f"#{i+1:<3} {name}")
    print("🏆"*20)

    # --- 最終總結 (重新印出兩個列表) ---
    print("\n\n" + "🏆"*20)
    print("          === 🏆 最終總結 🏆 ===")
    print(" " * 20 + "並排比較")
    print("="*58)

    # 準備標頭
    header1 = f"(無雜訊 - {len(final_ranking_zero_noise)} 種)"
    header2 = f"({noise_noisy*100:.0f}% 雜訊 - {len(final_ranking_noisy)} 種)"
    print(f" 排名 | {header1:<25} | {header2:<25}")
    print("-" * 58)

    # 找出兩個列表中最長的長度，以便並排
    len1 = len(final_ranking_zero_noise)
    len2 = len(final_ranking_noisy)
    max_len = max(len1, len2)

    # 迭代並排印出
    for i in range(max_len):
        # 取得無雜訊的排名 (如果列表比較短，則填空)
        name1 = final_ranking_zero_noise[i] if i < len1 else ""
        # 取得有雜訊的排名 (如果列表比較短，則填空)
        name2 = final_ranking_noisy[i] if i < len2 else ""

        rank = f" #{i+1:<3}"
        print(f" {rank} | {name1:<25} | {name2:<25}")

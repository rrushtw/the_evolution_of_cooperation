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
    AVG_MATCHES_PER_STRATEGY = 100
    STABILITY_THRESHOLD = 100

    # 預設 5% 雜訊。若要執行無雜訊, 請手動改為 0.0
    NOISE = 0.05

    # --- 3. 執行 "單次" 演化模擬 ---
    final_ranking = simulation.run_evolution_simulation(
        strategy_types=strategy_types_list,
        initial_copies=INITIAL_COPIES_PER_TYPE,
        kill_count=KILL_AND_REPRODUCE_COUNT,
        rounds_per_game=ROUNDS_PER_GAME,
        avg_matches_per_strategy = AVG_MATCHES_PER_STRATEGY,
        noise=NOISE,
        stability_threshold=STABILITY_THRESHOLD
    )

    # --- 4. 印出最終排名 ---
    print("\n\n" + "🏆"*20)
    print(f"=== 最終演化排名 ({NOISE*100:.0f}% 雜訊) ===")
    print("="*40)
    for i, name in enumerate(final_ranking):
        print(f"#{i+1:<3} {name}")
    print("🏆"*20)

import importlib
import inspect
from pathlib import Path
import os
import json
import time
from datetime import datetime

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
        except Exception as e:
            print(f"[Loader] 載入 {module_name} 時發生未知錯誤: {e}")

    return strategy_types


def run_main_simulation():
    """
    【新增】將主邏輯封裝成一個函數，以便在迴圈中呼叫。
    """

    # --- 1. 載入 "策略類別" ---
    print("\n" + "="*50)
    print(f"--- 執行新一輪模擬 (時間: {datetime.now()}) ---")
    print("--- 正在從 'strategies/' 目錄載入策略 ---")
    strategy_types_list = load_strategy_types("strategies")

    if not strategy_types_list:
        print("[錯誤] 'strategies' 目錄中未找到任何策略。請檢查掛載。")
        return  # 提前退出此輪

    print(f"--- 成功找到 {len(strategy_types_list)} 種策略 ---\n")

    # --- 2. 【修改】從環境變數讀取演化參數 (提供預設值) ---
    INITIAL_COPIES_PER_TYPE = int(os.getenv("INITIAL_COPIES_PER_TYPE", 6))
    KILL_AND_REPRODUCE_COUNT = int(os.getenv("KILL_AND_REPRODUCE_COUNT", 5))
    ROUNDS_PER_GAME = int(os.getenv("ROUNDS_PER_GAME", 200))
    AVG_MATCHES_PER_STRATEGY = int(os.getenv("AVG_MATCHES_PER_STRATEGY", 100))
    STABILITY_THRESHOLD = int(os.getenv("STABILITY_THRESHOLD", 100))
    NOISE = float(os.getenv("NOISE", 0.05))  # 預設 5% 雜訊

    print("--- 模擬參數 ---")
    print(f"  NOISE: {NOISE*100:.1f}%")
    print(f"  INITIAL_COPIES_PER_TYPE: {INITIAL_COPIES_PER_TYPE}")
    print(f"  KILL_AND_REPRODUCE_COUNT: {KILL_AND_REPRODUCE_COUNT}")
    print(f"  ROUNDS_PER_GAME: {ROUNDS_PER_GAME}")
    print(f"  AVG_MATCHES_PER_STRATEGY: {AVG_MATCHES_PER_STRATEGY}")
    print(f"  STABILITY_THRESHOLD: {STABILITY_THRESHOLD}")
    print("------------------")

    # --- 3. 執行 "單次" 演化模擬 ---
    final_ranking = simulation.run_evolution_simulation(
        strategy_types=strategy_types_list,
        initial_copies=INITIAL_COPIES_PER_TYPE,
        kill_count=KILL_AND_REPRODUCE_COUNT,
        rounds_per_game=ROUNDS_PER_GAME,
        avg_matches_per_strategy=AVG_MATCHES_PER_STRATEGY,
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

    # --- 5. 【新增】將結果匯出到 /app/output ---
    output_dir = "/app/output"  # 此路徑對應 docker-compose.yml 中的掛載點
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 檔名包含雜訊率，方便辨識
    output_filename = f"ranking_{timestamp}_noise_{NOISE*100:.0f}pct.json"
    output_path = os.path.join(output_dir, output_filename)

    result_data = {
        "timestamp_iso": datetime.now().isoformat(),
        "parameters": {
            "noise": NOISE,
            "initial_copies": INITIAL_COPIES_PER_TYPE,
            "kill_count": KILL_AND_REPRODUCE_COUNT,
            "rounds_per_game": ROUNDS_PER_GAME,
            "avg_matches_per_strategy": AVG_MATCHES_PER_STRATEGY,
            "stability_threshold": STABILITY_THRESHOLD,
            "strategy_count": len(strategy_types_list),
            "strategies_loaded": [s.__name__ for s in strategy_types_list]
        },
        "ranking": final_ranking
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
        print(f"\n[結果] 模擬結果已儲存至: {output_path} (本地 ./output/ 目錄)")
    except Exception as e:
        print(f"\n[錯誤] 儲存結果失敗: {e}")


if __name__ == "__main__":

    # --- 【新增】持續執行的迴圈 ---
    # 讓程式可以 7x24 執行，自動進行一輪又一輪的模擬
    while True:
        try:
            run_main_simulation()
            # 休息 10 秒，準備下一輪
            print("\n--- 模擬完成。將在 10 秒後執行下一輪... (Ctrl+C 停止) ---")
            time.sleep(10)

        except KeyboardInterrupt:
            # 允許手動停止 (Ctrl+C)
            print("\n[服務] 偵測到手動停止 (KeyboardInterrupt)。正在關閉...")
            break
        except Exception as e:
            # 捕捉其他潛在錯誤，避免迴圈中斷
            print(f"\n[嚴重錯誤] 模擬主迴圈發生例外: {e}")
            print("--- 將在 60 秒後嘗試重啟... ---")
            time.sleep(60)

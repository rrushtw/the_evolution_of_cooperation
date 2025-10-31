from engine import run_tournament
# (可以從 strategies/ 目錄匯入更多策略)
from strategies.tit_for_tat import TitForTat
from strategies.always_cheat import AlwaysCheat
from strategies.always_cooperate import AlwaysCooperate
from strategies.random import Random
from strategies.pavlov import Pavlov
from strategies.global_pavlov import GlobalPavlov
from strategies.grudger import Grudger

if __name__ == "__main__":

    # 參賽者名單
    strategy_list = [
        TitForTat(),
        AlwaysCheat(),
        AlwaysCooperate(),
        Random(),
        Pavlov(),
        GlobalPavlov(),
        Grudger(),
    ]

    # --- 執行無雜訊的比賽 ---
    rounds = 3000
    noise = 0.0

    # 執行循環賽
    results = run_tournament(
        strategy_list, rounds_per_game=rounds, noise=noise)

    # 印出排名
    print("\n=== 最終排名 (無雜訊) ===")
    for i, strategy in enumerate(results):
        # 讓排名和名稱對齊
        print(f"#{i+1:<3} {strategy.name:<20} 得分: {strategy.total_score}")

    # --- 執行有雜訊的比賽 (例如 5% 雜訊) ---
    noise = 0.05

    print("\n" + "="*40 + "\n")

    # 執行循環賽
    # (run_tournament 內部會自動呼叫 strategy.reset()，清空上一場的分數)
    results_noisy = run_tournament(
        strategy_list, rounds_per_game=rounds, noise=noise)

    print(f"\n=== 最終排名 ({noise*100:.0f}% 雜訊) ===")
    for i, strategy in enumerate(results_noisy):
        print(f"#{i+1:<3} {strategy.name:<20} 得分: {strategy.total_score}")

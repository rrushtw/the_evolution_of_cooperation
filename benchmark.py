"""
基準量測工具 (Benchmark Harness)

純量測，不改動任何既有模擬邏輯。用途：
1. 在「固定 seed + 固定工作量」下計時 engine.run_tournament()，
   讓 CPython 與 PyPy 可以做 apples-to-apples 比較。
2. 印出「互動數/秒」與總分 checksum。
   - checksum 在相同 seed 下應可重現；CPython 與 PyPy 共用相容的
     Mersenne Twister，故兩者 checksum 應一致，可順便驗證邏輯沒被移植壞。

執行 (容器內)：
    python  -u benchmark.py      # CPython
    pypy3   -u benchmark.py      # PyPy

可用環境變數覆寫工作量 (預設值刻意對齊 app.py 的單一世代規模)：
    BENCH_COPIES, BENCH_ROUNDS, BENCH_MATCHES, BENCH_NOISE, BENCH_SEED
"""

import os
import sys
import gc
import time
import random
import platform

import engine
from app import load_strategy_types


def main():
    copies = int(os.getenv("BENCH_COPIES", 6))
    rounds = int(os.getenv("BENCH_ROUNDS", 200))
    matches = int(os.getenv("BENCH_MATCHES", 100))
    noise = float(os.getenv("BENCH_NOISE", 0.05))
    seed = int(os.getenv("BENCH_SEED", 42))

    # 固定 seed：random.sample 的配對與所有雜訊翻轉都變得可重現
    random.seed(seed)

    # 診斷開關：關閉 cyclic GC，驗證「大量長壽 dict 觸發 GC 掃描」是否為瓶頸
    no_gc = os.getenv("BENCH_NO_GC", "0") == "1"
    if no_gc:
        gc.disable()

    strategy_types = load_strategy_types("strategies")
    if not strategy_types:
        print("[錯誤] 找不到任何策略", file=sys.stderr)
        sys.exit(1)

    population = []
    for s_type in sorted(strategy_types, key=lambda c: c.__name__):  # 固定順序
        for _ in range(copies):
            population.append(s_type())

    pop_size = len(population)
    total_matches = (pop_size * matches) // 2
    total_interactions = total_matches * rounds

    runtime = f"{platform.python_implementation()} {platform.python_version()}"
    print("=" * 60)
    print(f"[Benchmark] runtime={runtime}")
    print(f"[Benchmark] 策略種類={len(strategy_types)}  個體={pop_size}  "
          f"copies={copies} rounds={rounds} matches={matches} noise={noise}")
    print(f"[Benchmark] 規劃互動數={total_interactions:,}  seed={seed}  gc={'OFF' if no_gc else 'ON'}")
    print("=" * 60)

    start = time.perf_counter()
    sorted_pop = engine.run_tournament(population, rounds, matches, noise)
    elapsed = time.perf_counter() - start

    checksum = sum(s.total_score for s in sorted_pop)
    rate = total_interactions / elapsed if elapsed > 0 else 0

    print("\n" + "-" * 60)
    print(f"[結果] runtime           : {runtime}")
    print(f"[結果] wall-time         : {elapsed:.3f} s")
    print(f"[結果] 互動數/秒         : {rate:,.0f} interactions/s")
    print(f"[結果] 總分 checksum     : {checksum}")
    print("-" * 60)


if __name__ == "__main__":
    main()

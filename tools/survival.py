"""
存活率/勝率研究 (Survival Study) — 忠實版（直接重用正式 app 的演化迴圈）

⚠️ 修正紀錄（2026-06-03）：
舊版自行重寫了一套「縮水」演化迴圈（ROUNDS=80/MATCHES=50、封頂 100 代），
與正式 app（ROUNDS=200/MATCHES=100、跑到 stability_threshold 連續穩定）規模
差 5 倍、且根本沒跑到均衡，導致結論完全失真——剝削者（Awkward/Joss）在「早期
暫態」假性勝出，掩蓋了真正的長期均衡（GTFT/TitForTwoTats/SkepticalRedeemer 等
nice reciprocator 勝出）。本版直接呼叫 simulation.run_evolution_simulation，與
app 同一套邏輯、同參數、跑到穩定，工具與 app 永遠不會再分岔。

每個 seed = 一次完整演化（跑到穩定），記錄最終排名。
聚合（對 N 個 seed）：
- 贏家頻率（rank 1 的比例）+ Wilson 95% CI
- top-3 / top-5 入榜頻率
- 平均最終名次

純分析，不修改任何策略 / 不刪檔。執行（從 /app）：
    python -m tools.survival
環境變數（預設＝正式 app 預設）：
    SURV_RUNS(30), SURV_COPIES(6), SURV_KILL(5), SURV_ROUNDS(200),
    SURV_MATCHES(100), SURV_NOISE(0.05), SURV_STABILITY(100), SURV_WORKERS

注意：跑到穩定每個 seed 約數十分鐘，請用 SURV_WORKERS 吃滿核心並平行。
"""

import os
import sys
import io
import math
import contextlib
import random
from multiprocessing import Pool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import simulation
from app import load_strategy_types

RUNS = int(os.getenv("SURV_RUNS", 30))
COPIES = int(os.getenv("SURV_COPIES", 6))
KILL = int(os.getenv("SURV_KILL", 5))
ROUNDS = int(os.getenv("SURV_ROUNDS", 200))
MATCHES = int(os.getenv("SURV_MATCHES", 100))
NOISE = float(os.getenv("SURV_NOISE", 0.05))
STABILITY = int(os.getenv("SURV_STABILITY", 100))
WORKERS = int(os.getenv("SURV_WORKERS", 0)) or None

Z = 1.96  # 95% 常態近似
_TYPES = None  # 由各 worker (fork) 繼承


def one_run(seed):
    """一個 seed 的完整演化（跑到穩定），回傳最終排名（best-first 的名稱清單）。"""
    random.seed(seed)
    sink = io.StringIO()
    # simulation 內部每代都會 print，導向黑洞避免洗版
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        ranking = simulation.run_evolution_simulation(
            _TYPES, COPIES, KILL, ROUNDS, MATCHES, NOISE, STABILITY)
    return ranking


def wilson_ci(k, n):
    """比例的 Wilson 95% 信賴區間 (lo, hi)，小樣本/極端比例比常態穩。"""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + Z * Z / n
    center = (p + Z * Z / (2 * n)) / denom
    margin = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def main():
    global _TYPES
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        _TYPES = load_strategy_types("strategies")
    all_names = sorted(t.__name__ for t in _TYPES)
    pop_total = len(_TYPES) * COPIES

    print("=" * 88)
    print(f"勝率研究（忠實版，重用正式 app 演化）：{len(_TYPES)} 策略 × {COPIES} 個體 = {pop_total}")
    print(f"參數：rounds={ROUNDS} matches={MATCHES} noise={NOISE:.0%} kill={KILL} "
          f"stability={STABILITY}（跑到穩定）| N={RUNS} 次完整演化")
    print("=" * 88, flush=True)

    win = {n: 0 for n in all_names}
    top3 = {n: 0 for n in all_names}
    top5 = {n: 0 for n in all_names}
    rank_sum = {n: 0 for n in all_names}

    done = 0
    with Pool(processes=WORKERS) as pool:
        # imap_unordered：seed 一跑完就回報，提供即時進度
        for ranking in pool.imap_unordered(one_run, list(range(1, RUNS + 1))):
            done += 1
            win[ranking[0]] += 1
            for name in ranking[:3]:
                top3[name] += 1
            for name in ranking[:5]:
                top5[name] += 1
            for pos, name in enumerate(ranking, start=1):
                rank_sum[name] += pos
            print(f"  [{done}/{RUNS}] 贏家 = {ranking[0]}", flush=True)

    n = RUNS
    rows = []
    for name in all_names:
        lo, hi = wilson_ci(win[name], n)
        rows.append({
            "name": name,
            "win": win[name],
            "win_rate": win[name] / n,
            "win_lo": lo,
            "win_hi": hi,
            "top3": top3[name] / n,
            "top5": top5[name] / n,
            "mean_rank": rank_sum[name] / n,
        })
    rows.sort(key=lambda x: (-x["win_rate"], -x["top5"], x["mean_rank"]))

    print(f"\nN={n} 次完整演化（每次跑到穩定）；贏家率誤差為 Wilson 95% CI\n")
    print(f"  {'策略':<20} {'奪冠':>5} {'贏家率 (95%CI)':>22} {'top3':>7} {'top5':>7} {'平均名次':>9}")
    print("  " + "-" * 82)
    for r in rows:
        winr = f"{r['win_rate']:.0%} [{r['win_lo']:.0%},{r['win_hi']:.0%}]"
        print(f"  {r['name']:<20} {r['win']:>5} {winr:>22} "
              f"{r['top3']:>6.0%} {r['top5']:>6.0%} {r['mean_rank']:>9.1f}")

    champs = [r for r in rows if r["win"] > 0]
    print(f"\n■ 曾奪冠的策略：{len(champs)} 個（N={n}）")
    for r in champs:
        print(f"  - {r['name']:<20} 奪冠 {r['win']}/{n}"
              f"（{r['win_rate']:.0%}, 95% CI [{r['win_lo']:.0%},{r['win_hi']:.0%}]）")


if __name__ == "__main__":
    main()

"""
存活率研究 (Survival Study) — 瘦身的「主信號」

在「真實多人演化生態」裡跑 N 次（固定 seed、可平行）有界世代演化，統計每個
策略的存活/滅絕表現。這比 1v1 指紋更能反映「在完整生態中誰是冗餘 / 長期墊底」，
因為它包含了跨對手耦合（如 GlobalPavlov 的遷怒）與族群動態。

每次演化（一個 seed）：
- 初始：每種策略 copies 個體。
- 每世代：engine.run_tournament 評分 → 淘汰最低 kill 個 → 複製最高 kill 個「種類」。
- 跑滿 MAX_GEN 世代，或剩 ≤1 種時提早結束。
- 記錄：最終各種類個體數、滅絕順序與世代。

聚合輸出（對 N 個 seed 平均）：
- survival_rate：該種類在「結束時仍存活」的 run 比例
- avg_share：結束時平均個體佔比
- extinct_rate / mean_ext_gen：滅絕比例與平均滅絕世代
- mean_rank：平均最終名次（1 = 最佳）

純分析，不修改任何策略 / 不刪檔。執行：
    python -m tools.survival            # 從 /app 執行
環境變數：SURV_RUNS, SURV_COPIES, SURV_KILL, SURV_ROUNDS, SURV_MATCHES,
          SURV_NOISE, SURV_MAXGEN, SURV_WORKERS
"""

import os
import sys
import io
import collections
import contextlib
import random
from multiprocessing import Pool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import engine
from app import load_strategy_types

RUNS = int(os.getenv("SURV_RUNS", 40))
COPIES = int(os.getenv("SURV_COPIES", 6))
KILL = int(os.getenv("SURV_KILL", 5))
ROUNDS = int(os.getenv("SURV_ROUNDS", 80))
MATCHES = int(os.getenv("SURV_MATCHES", 50))
NOISE = float(os.getenv("SURV_NOISE", 0.05))
MAX_GEN = int(os.getenv("SURV_MAXGEN", 100))
WORKERS = int(os.getenv("SURV_WORKERS", 0)) or None

_TYPES = None  # 由各 worker (fork) 繼承


def one_run(seed):
    """跑一個 seed 的有界演化，回傳該 run 的最終名次與滅絕資訊。"""
    random.seed(seed)
    population = [t() for t in _TYPES for _ in range(COPIES)]

    alive = set(t.__name__ for t in _TYPES)
    extinction = []  # [(gen, name), ...] 依滅絕先後
    counts = collections.Counter(type(s).__name__ for s in population)

    sink = io.StringIO()
    last_gen = 0
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        for gen in range(1, MAX_GEN + 1):
            last_gen = gen
            sorted_pop = engine.run_tournament(population, ROUNDS, MATCHES, NOISE)
            population = sorted_pop[:-KILL] + [type(t)() for t in sorted_pop[:KILL]]
            counts = collections.Counter(type(s).__name__ for s in population)
            now = set(counts)
            for dead in sorted(alive - now):
                extinction.append((gen, dead))
            alive = now
            if len(alive) <= 1:
                break

    # 該 run 的名次：存活者依個體數由多到少，其後接「滅絕者反序」（最晚滅絕排前）
    survivors = [n for n, _ in counts.most_common()]
    extinct_names = [n for _, n in extinction]
    ranking = survivors + list(reversed(extinct_names))

    return {
        "final_counts": dict(counts),
        "extinction": extinction,
        "ranking": ranking,
        "generations": last_gen,
    }


def main():
    global _TYPES
    _TYPES = load_strategy_types("strategies")
    all_names = sorted(t.__name__ for t in _TYPES)
    pop_total = len(_TYPES) * COPIES

    print("=" * 84)
    print(f"存活率研究：{len(_TYPES)} 策略 × {COPIES} 個體 = {pop_total}  |  "
          f"{RUNS} runs, 上限 {MAX_GEN} 世代")
    print(f"參數：rounds={ROUNDS} matches={MATCHES} noise={NOISE:.0%} kill={KILL}")
    print("=" * 84)

    with Pool(processes=WORKERS) as pool:
        results = pool.map(one_run, list(range(1, RUNS + 1)))

    n = len(results)
    agg = {name: {
        "survive": 0, "share_sum": 0.0, "extinct": 0,
        "ext_gen_sum": 0, "rank_sum": 0,
    } for name in all_names}

    for r in results:
        total = sum(r["final_counts"].values()) or 1
        for name in all_names:
            cnt = r["final_counts"].get(name, 0)
            if cnt > 0:
                agg[name]["survive"] += 1
                agg[name]["share_sum"] += cnt / total
        for gen, name in r["extinction"]:
            agg[name]["extinct"] += 1
            agg[name]["ext_gen_sum"] += gen
        for rank, name in enumerate(r["ranking"], start=1):
            agg[name]["rank_sum"] += rank

    rows = []
    for name in all_names:
        a = agg[name]
        rows.append({
            "name": name,
            "survival_rate": a["survive"] / n,
            "avg_share": a["share_sum"] / n,
            "extinct_rate": a["extinct"] / n,
            "mean_ext_gen": (a["ext_gen_sum"] / a["extinct"]) if a["extinct"] else None,
            "mean_rank": a["rank_sum"] / n,
        })

    # 依 (存活率↓, 平均佔比↓, 平均名次↑) 排序
    rows.sort(key=lambda x: (-x["survival_rate"], -x["avg_share"], x["mean_rank"]))

    avg_gen = sum(r["generations"] for r in results) / n
    print(f"\n平均每 run 跑了 {avg_gen:.0f} 世代\n")
    print(f"  {'#':>2} {'策略':<22} {'存活率':>7} {'平均佔比':>9} {'滅絕率':>7} "
          f"{'平均滅絕世代':>12} {'平均名次':>9}")
    print("  " + "-" * 80)
    for i, r in enumerate(rows, 1):
        ext_gen = f"{r['mean_ext_gen']:.0f}" if r["mean_ext_gen"] is not None else "—"
        print(f"  {i:>2} {r['name']:<22} {r['survival_rate']:>6.0%} "
              f"{r['avg_share']:>8.1%} {r['extinct_rate']:>6.0%} "
              f"{ext_gen:>12} {r['mean_rank']:>9.1f}")

    # 標記長期墊底（存活率低 且 滅絕率高）
    chronic = [r for r in rows if r["survival_rate"] <= 0.2 and r["extinct_rate"] >= 0.6]
    print(f"\n■ 長期墊底候選（存活率 ≤20% 且 滅絕率 ≥60%）：{len(chronic)} 個")
    for r in chronic:
        eg = f"{r['mean_ext_gen']:.0f}" if r["mean_ext_gen"] is not None else "—"
        print(f"  - {r['name']:<22} 存活率 {r['survival_rate']:.0%}, "
              f"滅絕率 {r['extinct_rate']:.0%}, 平均滅絕世代 {eg}")


if __name__ == "__main__":
    main()

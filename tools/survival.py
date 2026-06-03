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
import math
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
    Z = 1.96  # 95% 常態近似

    # 收集每個策略「逐 run」的樣本，才能算變異數 / 信賴區間
    # （單跑一次只是一個樣本；N 個獨立 seed 才能給出有誤差棒的 concrete conclusion）
    shares = {name: [] for name in all_names}    # 每 run 的最終佔比（該 run 滅絕計 0）
    survived = {name: [] for name in all_names}  # 每 run 是否存活 (1/0)
    ext_gens = {name: [] for name in all_names}  # 滅絕世代（僅滅絕的 run）
    ranks = {name: [] for name in all_names}     # 每 run 的最終名次

    for r in results:
        total = sum(r["final_counts"].values()) or 1
        for name in all_names:
            cnt = r["final_counts"].get(name, 0)
            shares[name].append(cnt / total)
            survived[name].append(1 if cnt > 0 else 0)
        for gen, name in r["extinction"]:
            ext_gens[name].append(gen)
        for rank, name in enumerate(r["ranking"], start=1):
            ranks[name].append(rank)

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    def stdev(xs):
        if len(xs) < 2:
            return 0.0
        m = mean(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    def mean_ci_radius(xs):
        """平均值的 95% 信賴半徑（常態近似 Z·s/√n）。"""
        return Z * stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0

    def wilson_ci(k, total):
        """比例的 Wilson 95% 信賴區間 (lo, hi)，小樣本/極端比例比常態更穩。"""
        if total == 0:
            return 0.0, 0.0
        p = k / total
        denom = 1 + Z * Z / total
        center = (p + Z * Z / (2 * total)) / denom
        margin = Z * math.sqrt(p * (1 - p) / total + Z * Z / (4 * total * total)) / denom
        return max(0.0, center - margin), min(1.0, center + margin)

    rows = []
    for name in all_names:
        surv_k = sum(survived[name])
        surv_lo, surv_hi = wilson_ci(surv_k, n)
        rows.append({
            "name": name,
            "survival_rate": surv_k / n,
            "surv_lo": surv_lo,
            "surv_hi": surv_hi,
            "avg_share": mean(shares[name]),
            "share_ci": mean_ci_radius(shares[name]),
            "extinct_rate": len(ext_gens[name]) / n,
            "mean_ext_gen": mean(ext_gens[name]) if ext_gens[name] else None,
            "mean_rank": mean(ranks[name]) if ranks[name] else None,
        })

    # 依 (存活率↓, 平均佔比↓, 平均名次↑) 排序
    rows.sort(key=lambda x: (-x["survival_rate"], -x["avg_share"], x["mean_rank"] or 0))

    avg_gen = mean([r["generations"] for r in results])
    print(f"\nN={n} 獨立演化（seeds 1..{n}），平均每 run 跑了 {avg_gen:.0f} 世代；誤差為 95% CI\n")
    print(f"  {'#':>2} {'策略':<20} {'存活率 (95%CI)':>22} {'平均佔比 (95%CI)':>20} "
          f"{'平均滅絕世代':>12} {'平均名次':>9}")
    print("  " + "-" * 92)
    for i, r in enumerate(rows, 1):
        ext_gen = f"{r['mean_ext_gen']:.0f}" if r["mean_ext_gen"] is not None else "—"
        rank = f"{r['mean_rank']:.1f}" if r["mean_rank"] is not None else "—"
        surv = f"{r['survival_rate']:.0%} [{r['surv_lo']:.0%},{r['surv_hi']:.0%}]"
        share = f"{r['avg_share']:.1%} ±{r['share_ci']:.1%}"
        print(f"  {i:>2} {r['name']:<20} {surv:>22} {share:>20} "
              f"{ext_gen:>12} {rank:>9}")

    # 具體結論（用信賴區間判定，而非單點）：
    #   穩健優勢者 = 平均佔比 95% CI 下界仍 > 5%
    #   穩健滅絕者 = 存活率 95% CI 上界 < 5%
    dominant = [r for r in rows if r["avg_share"] - r["share_ci"] > 0.05]
    robust_extinct = [r for r in rows if r["surv_hi"] < 0.05]
    print(f"\n■ 穩健優勢者（平均佔比 95% CI 下界 > 5%）：{len(dominant)} 個")
    for r in dominant:
        lo = max(0.0, r["avg_share"] - r["share_ci"])
        print(f"  - {r['name']:<20} 平均佔比 {r['avg_share']:.1%} (95% CI ≥ {lo:.1%}), "
              f"存活率 {r['survival_rate']:.0%} [{r['surv_lo']:.0%},{r['surv_hi']:.0%}]")
    print(f"\n■ 穩健滅絕者（存活率 95% CI 上界 < 5%）：{len(robust_extinct)} 個")
    if robust_extinct:
        print("  " + "、".join(r["name"] for r in robust_extinct))
    else:
        print("  （無——樣本數不足以把任一策略的存活率上界壓到 5% 以下，請增大 SURV_RUNS）")


if __name__ == "__main__":
    main()

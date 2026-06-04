"""
社會互動稀疏化研究 (Society Study) — 「未來陰影」旋鈕掃描

問題：現代社會中，每個個體跟同一個人重複互動的次數變少了，合作會怎樣？

本工具把 rounds_per_game 當旋鈕掃描。此模型是「隨機配對、每次只玩 1 回合」，
rounds_per_game 實為「總單次互動數的乘數」，可推得：

    每對個體平均重複相遇次數 ≈ total_interactions / C(pop, 2)
                            = (pop * matches // 2 * rounds) / (pop*(pop-1)/2)

往下轉 rounds → 重複相遇變少（同時總互動量變少）→ 越接近「一次性、匿名」的
現代社會 → 「下次再算帳」的威懾失效 → 預期合作出現相變式崩潰。

每個 rounds 值跑 N 次完整演化（忠實重用正式 app 的 run_evolution_simulation、
跑到穩定），記錄每次的〔奪冠者 + 均衡合作率〕，彙整出三個產出：
  1. 臨界點：合作率曲線最陡降段 + 50% 交越點（內插）
  2. 各 rounds 的霸主：奪冠策略名稱與頻率
  3. 「rounds × 合作率」曲線：均衡合作率 mean ± 95% CI（含 ASCII 圖 + CSV）

純分析，不修改任何策略 / 不刪檔。執行（從 /app）：
    python -m tools.society
環境變數（其餘＝正式 app 預設）：
    SOC_ROUNDS("1,2,3,5,8,12,20,35,60,100,200"), SOC_RUNS(50),
    SOC_COPIES(6), SOC_KILL(5), SOC_MATCHES(100), SOC_NOISE(0.05),
    SOC_STABILITY(100), SOC_WORKERS

注意：高 rounds 值每個 seed 跑到穩定約數十分鐘，請用 SOC_WORKERS 吃滿核心。
"""

import os
import sys
import io
import math
import contextlib
import random
import collections
from multiprocessing import Pool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import simulation
from app import load_strategy_types

ROUNDS_GRID = [int(x) for x in os.getenv(
    "SOC_ROUNDS", "1,2,3,5,8,12,20,35,60,100,200").split(",") if x.strip()]
RUNS = int(os.getenv("SOC_RUNS", 50))
COPIES = int(os.getenv("SOC_COPIES", 6))
KILL = int(os.getenv("SOC_KILL", 5))
MATCHES = int(os.getenv("SOC_MATCHES", 100))
NOISE = float(os.getenv("SOC_NOISE", 0.05))
STABILITY = int(os.getenv("SOC_STABILITY", 100))
WORKERS = int(os.getenv("SOC_WORKERS", 0)) or None

Z = 1.96  # 95% 常態近似
_TYPES = None  # 由各 worker (fork) 繼承


def one_run(task):
    """一個 (rounds, seed) 的完整演化（跑到穩定）。回傳 (rounds, 奪冠者, 均衡合作率)。"""
    rounds, seed = task
    random.seed(seed)
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        ranking, coop_rate = simulation.run_evolution_simulation(
            _TYPES, COPIES, KILL, rounds, MATCHES, NOISE, STABILITY,
            collect_coop_stats=True)
    return rounds, ranking[0], coop_rate


def mean_ci(values):
    """平均值的 95% 信賴區間 (mean, lo, hi)，用 mean ± Z·s/√n。"""
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0
    mean = sum(values) / n
    if n == 1:
        return mean, mean, mean
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    margin = Z * math.sqrt(var / n)
    return mean, max(0.0, mean - margin), min(1.0, mean + margin)


def repeat_meetings(rounds, pop):
    """每對個體平均重複相遇次數 ≈ total_interactions / C(pop, 2)。"""
    total_interactions = (pop * MATCHES // 2) * rounds
    pairs = pop * (pop - 1) / 2
    return total_interactions / pairs if pairs else 0.0


def ascii_curve(rows):
    """畫一條 rounds(對數) × 合作率 的 ASCII 曲線。"""
    height = 12
    lines = []
    lines.append("  合作率")
    for level in range(height, -1, -1):
        threshold = level / height
        row = f"  {threshold*100:3.0f}% |"
        for r in rows:
            cr = r["coop_mean"]
            # 每個 rounds 值一欄，合作率落在此高度就畫 ●
            if cr >= threshold - 0.5 / height and cr < threshold + 0.5 / height:
                row += " ●"
            elif level == 0:
                row += " ─"
            else:
                row += "  "
        lines.append(row)
    # x 軸標籤
    axis = "       +" + "──" * len(rows)
    labels = "        "
    for r in rows:
        labels += f"{r['rounds']:>2}"[:2]
    lines.append(axis)
    lines.append(labels + "   ← rounds（每對重複相遇 ≈ 0.73×rounds）")
    return "\n".join(lines)


def find_critical(rows):
    """臨界點：(a) 相鄰點合作率最陡降段；(b) 合作率 50% 的內插交越點。"""
    # (a) 最陡降
    steepest = None
    for i in range(1, len(rows)):
        drop = rows[i - 1]["coop_mean"] - rows[i]["coop_mean"]
        if steepest is None or drop > steepest[0]:
            steepest = (drop, rows[i - 1]["rounds"], rows[i]["rounds"])

    # (b) 50% 交越（合作率由高到低穿越 0.5；rows 已按 rounds 由小到大，故反向找）
    crossing = None
    ordered = sorted(rows, key=lambda r: r["rounds"])
    for i in range(1, len(ordered)):
        lo, hi = ordered[i - 1], ordered[i]
        if (lo["coop_mean"] - 0.5) * (hi["coop_mean"] - 0.5) <= 0 and \
           lo["coop_mean"] != hi["coop_mean"]:
            # 線性內插 rounds（對數空間更合理，但點密時差異不大）
            t = (0.5 - lo["coop_mean"]) / (hi["coop_mean"] - lo["coop_mean"])
            crossing = lo["rounds"] + t * (hi["rounds"] - lo["rounds"])
            break
    return steepest, crossing


def main():
    global _TYPES
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        _TYPES = load_strategy_types("strategies")
    pop = len(_TYPES) * COPIES

    print("=" * 96)
    print(f"社會互動稀疏化研究：{len(_TYPES)} 策略 × {COPIES} 個體 = {pop}")
    print(f"旋鈕 rounds ∈ {ROUNDS_GRID}")
    print(f"固定參數：matches={MATCHES} noise={NOISE:.0%} kill={KILL} "
          f"stability={STABILITY}（跑到穩定）| 每點 N={RUNS}")
    print("=" * 96, flush=True)

    # 攤平所有 (rounds, seed) 任務一起平行，低 rounds 跑得快可填滿核心
    tasks = [(rounds, seed)
             for rounds in ROUNDS_GRID
             for seed in range(1, RUNS + 1)]

    by_rounds = {r: {"coop": [], "winners": collections.Counter()}
                 for r in ROUNDS_GRID}
    done = 0
    total = len(tasks)
    with Pool(processes=WORKERS) as pool:
        for rounds, winner, coop_rate in pool.imap_unordered(one_run, tasks):
            by_rounds[rounds]["coop"].append(coop_rate)
            by_rounds[rounds]["winners"][winner] += 1
            done += 1
            if done % RUNS == 0 or done == total:
                print(f"  進度 {done}/{total}", flush=True)

    # 彙整每個 rounds 值
    rows = []
    for rounds in ROUNDS_GRID:
        coop = by_rounds[rounds]["coop"]
        winners = by_rounds[rounds]["winners"]
        mean, lo, hi = mean_ci(coop)
        top = winners.most_common(2)
        champ = f"{top[0][0]} ({top[0][1]}/{RUNS})" if top else "-"
        runner = f"{top[1][0]} ({top[1][1]})" if len(top) > 1 else "-"
        rows.append({
            "rounds": rounds,
            "meet": repeat_meetings(rounds, pop),
            "coop_mean": mean, "coop_lo": lo, "coop_hi": hi,
            "champ": champ, "runner": runner,
        })

    # 產出 2 + 3：每 rounds 摘要表
    print(f"\nN={RUNS} 每點；合作率為「實際出招」均衡合作率，誤差為 95% CI\n")
    print(f"  {'rounds':>6} {'重複相遇/對':>11} {'合作率 (95% CI)':>24} "
          f"{'霸主 (奪冠/N)':<28} {'亞軍':<20}")
    print("  " + "-" * 92)
    for r in rows:
        cr = f"{r['coop_mean']:.0%} [{r['coop_lo']:.0%},{r['coop_hi']:.0%}]"
        print(f"  {r['rounds']:>6} {r['meet']:>10.1f}x {cr:>24} "
              f"{r['champ']:<28} {r['runner']:<20}")

    # 產出 3：ASCII 曲線
    print("\n【合作率 vs rounds 曲線】")
    print(ascii_curve(rows))

    # 產出 1：臨界點
    steepest, crossing = find_critical(rows)
    print("\n【臨界點 / 相變】")
    if steepest:
        print(f"  最陡降段：rounds {steepest[1]} → {steepest[2]} "
              f"間合作率掉 {steepest[0]:.0%}")
    if crossing is not None:
        print(f"  合作率 50% 交越點：rounds ≈ {crossing:.1f}"
              f"（每對重複相遇 ≈ {repeat_meetings(crossing, pop):.1f} 次）")
    else:
        print("  合作率未在掃描範圍內穿越 50%（可能整段偏高或偏低）")

    # 產出 4：CSV（供繪圖）
    print("\n【CSV】rounds,repeat_meetings,coop_mean,coop_lo,coop_hi,champion,champion_wins")
    for r in rows:
        champ_name = r["champ"].split(" (")[0]
        champ_wins = r["champ"].split("(")[-1].split("/")[0] if "(" in r["champ"] else "0"
        print(f"  {r['rounds']},{r['meet']:.2f},{r['coop_mean']:.4f},"
              f"{r['coop_lo']:.4f},{r['coop_hi']:.4f},{champ_name},{champ_wins}")


if __name__ == "__main__":
    main()

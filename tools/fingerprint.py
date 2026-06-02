"""
行為指紋去重 (Behavioral Fingerprinting) — 軟指紋版

目的：找出「行為幾乎相同」的冗餘策略，當作瘦身的參考。

做法（軟指紋，貼近真實生態）：
1. 取一組固定 panel（AllC / AllD / TFT / Grudger / Random）當「探針」。
2. 對每個 (受測策略, panel 成員)，在**實際雜訊環境**下
   （外部 5% + 各策略內部 2%）跑 M 個 seed、每個 ROUNDS 回合 head-to-head，
   記錄受測策略的「平均合作率」與「平均每回合得分」，對 M 個 seed 取平均。
3. 軟指紋 = 對全 panel 的「合作率向量」(+ 得分向量作為輔助)。
4. 用歐氏距離分群：距離 < 門檻的視為近似冗餘。

為什麼用軟指紋而非「逐回合 move 完全相同」：
- 真實 sim 有雜訊與分數不對稱；無雜訊的乾淨對局會把
  「只在領先時才作弊」的策略（Bully/SmartEnvious）誤判成 AllCooperate。
- 多 seed 平均後，Random 探針也能穩定使用，且隨機型策略一視同仁。

純分析，不修改任何策略。執行：
    python -m tools.fingerprint        # 從 /app 執行
"""

import os
import sys
import math
import random
import itertools

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from definitions import Move, RESULT_MATRIX, PAYOFF
from engine import apply_noise
from app import load_strategy_types

PANEL_NAMES = ["AlwaysCooperate", "AlwaysCheat", "TitForTat", "Grudger", "Random"]
ROUNDS = 100
SEEDS = list(range(1, 16))   # 15 個 seed 取平均
NOISE = 0.05                 # 外部雜訊，貼近 sim 預設
NEAR_THRESHOLD = 0.10        # (合作率 ⊕ 正規化得分) 向量歐氏距離 < 此值 → 近似冗餘


def head_to_head(StratCls, PanelCls, rounds):
    """有雜訊對戰，回傳 (受測策略合作率, 受測策略平均每回合得分)。"""
    s = StratCls()
    p = PanelCls()
    coop = 0
    score = 0
    for _ in range(rounds):
        i_s = s.apply_internal_noise(s.play(p.unique_id, p.my_history, p.total_score))
        i_p = p.apply_internal_noise(p.play(s.unique_id, s.my_history, s.total_score))
        a_s = apply_noise(i_s, NOISE)
        a_p = apply_noise(i_p, NOISE)
        r_s, r_p = RESULT_MATRIX[(a_s, a_p)]
        s.update(p.unique_id, i_s, a_s, i_p, a_p, r_s)
        p.update(s.unique_id, i_p, a_p, i_s, a_s, r_p)
        if a_s == Move.COOPERATE:
            coop += 1
        score += PAYOFF[r_s]
    return coop / rounds, score / rounds


def soft_fingerprint(StratCls, panel):
    """回傳 (合作率向量, 得分向量)，各維對應一個 panel 成員，對 SEEDS 取平均。"""
    coop_vec, score_vec = [], []
    for P in panel:
        cs, ss = [], []
        for seed in SEEDS:
            random.seed(seed)
            c, s = head_to_head(StratCls, P, ROUNDS)
            cs.append(c)
            ss.append(s)
        coop_vec.append(sum(cs) / len(cs))
        score_vec.append(sum(ss) / len(ss))
    return coop_vec, score_vec


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main():
    types = load_strategy_types("strategies")
    by_name = {c.__name__: c for c in types}
    panel = [by_name[n] for n in PANEL_NAMES if n in by_name]
    panel_labels = [c.__name__ for c in panel]

    coop = {}
    score = {}
    for cls in sorted(types, key=lambda c: c.__name__):
        coop[cls.__name__], score[cls.__name__] = soft_fingerprint(cls, panel)

    names = sorted(coop)

    # 指紋向量 = 合作率 ⊕ 正規化得分(÷5)，讓「合作率相同但機制不同」的策略分得開
    def vec(n):
        return coop[n] + [s / 5.0 for s in score[n]]

    # 近似配對（指紋向量歐氏距離）
    pairs = []
    for a, b in itertools.combinations(names, 2):
        d = dist(vec(a), vec(b))
        if d < NEAR_THRESHOLD:
            pairs.append((d, a, b))
    pairs.sort()

    # 將近似配對連成群組（連通分量）
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _, a, b in pairs:
        parent[find(a)] = find(b)
    groups = {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    redundant_groups = [sorted(g) for g in groups.values() if len(g) > 1]

    # 輸出
    print("=" * 78)
    print(f"軟指紋分析：{len(types)} 策略  panel={panel_labels}")
    print(f"每對 {ROUNDS} 回合 × {len(SEEDS)} seeds, 外部雜訊 {NOISE:.0%}")
    print("=" * 78)

    print(f"\n■ 合作率指紋（對 {panel_labels}）")
    header = "  " + " ".join(f"{lbl[:6]:>6}" for lbl in panel_labels)
    print(f"  {'策略':<22}" + header)
    for n in names:
        row = " ".join(f"{v:6.2f}" for v in coop[n])
        print(f"  {n:<22}  {row}")

    print(f"\n■ 平均每回合得分指紋（對 {panel_labels}）")
    print(f"  {'策略':<22}" + header)
    for n in names:
        row = " ".join(f"{v:6.2f}" for v in score[n])
        print(f"  {n:<22}  {row}")

    print(f"\n■ 近似行為群組（合作率⊕得分 向量歐氏距離 < {NEAR_THRESHOLD}）：{len(redundant_groups)} 組")
    if not redundant_groups:
        print("  （無）")
    for g in sorted(redundant_groups, key=lambda x: (-len(x), x[0])):
        print(f"  - {{{', '.join(g)}}}")

    print(f"\n■ 最相近的前 15 對：")
    for d, a, b in pairs[:15]:
        print(f"  - {a:<22} ≈ {b:<22} (距離 {d:.3f})")


if __name__ == "__main__":
    main()

# 策略瘦身分析報告

> 初版日期：2026-06-02 · 更新：2026-06-03（依機制多樣性原則收斂，並**實際執行刪除**）
> 分析工具：`tools/fingerprint.py`、`tools/survival.py`（數據於遠端 20 核測試機重產，固定 seed 可重現）

## TL;DR

- 原始 23 個策略，**實際只刪 2 個**（`ForgivingTitForTat`、`GreedyProber`）→ 精簡到 **21 個**。
- 一開始指紋分析「建議砍 7 個」，但逐一複查後**收斂到 2 個**。核心教訓：

  > **🔑 機制多樣性 > 輸出指紋。** 行為指紋量的是「對固定 panel 的**輸出行為**」，但本 repo 的策略大多靠**內部機制／觸發條件**區分。**輸出相似 ≠ 機制相同** —— 1v1 對 panel 觸發不了嫉妒、救贖、永久拉黑等獨特邏輯，於是指紋把機制完全不同的策略誤併。指紋只能當「嫌疑」，不能當「判決」。

- 真正站得住的刪除只有「骨架/職能逐行重複、且重複成分已單獨存在」的 2 個。經典參考策略（TFT / AllC / AllD / Random / Grudger / Pavlov）一律保留作為科學錨點。

---

## 方法

兩個互補信號，皆在容器內、固定 seed、可重現：

| 信號 | 工具 | 看什麼 | 限制 |
|---|---|---|---|
| **行為指紋**（找嫌疑） | `fingerprint.py` | 對固定 panel（AllC/AllD/TFT/Grudger/Random）的「合作率＋得分」向量，多 seed 平均（雜訊 5%） | 1v1 量測，**看不到跨對手耦合**（如 GlobalPavlov 的遷怒），也觸發不了只對特定對手才顯現的條件邏輯（嫉妒/救贖/拉黑） |
| **存活率**（生態背景） | `survival.py` | 真實多人演化跑 40 runs × 100 世代，統計存活/滅絕 | 結果隨選擇壓力變動；本生態趨向「贏家通吃」，**滅絕≠冗餘** |

---

## 一、存活率研究（生態背景，21 策略）

40 runs × 100 世代，`rounds=80 matches=50 noise=5% kill=5`，初始每種 6 個體。平均每 run 跑滿 100 世代（Awkward+Joss 穩定共存，族群從不縮到 ≤1 種）。

| # | 策略 | 存活率 | 平均佔比 | 滅絕率 | 平均滅絕世代 | 平均名次 |
|---|---|---|---|---|---|---|
| 1 | **Awkward** | 100% | 66.7% | 0% | — | 1.0 |
| 2 | **Joss** | 100% | 31.7% | 0% | — | 2.1 |
| 3 | GenerousTitForTat | 2% | 0.9% | 98% | 68 | 3.1 |
| 4 | ChaoticRedeemer | 2% | 0.6% | 98% | 17 | 13.1 |
| 5 | TolerantGrudger | 2% | 0.1% | 98% | 46 | 5.5 |
| 6 | TitForTat | 2% | 0.0% | 98% | 55 | 4.1 |
| 7 | Redeemer | 2% | 0.0% | 98% | 44 | 6.6 |
| 8 | TitForTwoTats | 0% | — | 100% | 42 | 7.3 |
| 9 | LimitedPunisher | 0% | — | 100% | 39 | 8.6 |
| 10 | SkepticalRedeemer | 0% | — | 100% | 38 | 8.9 |
| 11 | Statistical | 0% | — | 100% | 37 | 9.5 |
| 12 | SmartProber | 0% | — | 100% | 29 | 11.8 |
| 13 | AlwaysCooperate | 0% | — | 100% | 28 | 12.2 |
| 14 | SmartEnvious | 0% | — | 100% | 19 | 12.9 |
| 15 | Grudger | 0% | — | 100% | 13 | 14.8 |
| 16 | Random | 0% | — | 100% | 11 | 16.5 |
| 17 | StochasticPavlov | 0% | — | 100% | 10 | 17.1 |
| 18 | GlobalPavlov | 0% | — | 100% | 11 | 17.2 |
| 19 | Pavlov | 0% | — | 100% | 10 | 18.3 |
| 20 | AlwaysCheat | 0% | — | 100% | 8 | 19.6 |
| 21 | Bully | 0% | — | 100% | 4 | 20.9 |

**解讀：**
- **Awkward + Joss 通吃**（合計佔比 ~98%）。兩者本質都是「大多合作、約 10% 偷背叛、不記仇」。
- 高雜訊環境（外部 5% + 內部 2% + Awkward 自帶 10% 手滑）下，**會報復的策略（TFT/Grudger 家族）被雜訊拖進互相懲罰而自我毀滅**，不報復的寬容者勝出——噪音 IPD 的已知結論。
- ⚠️「滅絕率高」**不等於**「該刪」——TFT 等是因生態被 Awkward 主宰而落敗，非本身冗餘。這份榜單是**背景**，不是刪除清單。

---

## 二、行為指紋（找嫌疑，21 策略）

合作率指紋（對 panel，多 seed 平均；數值=合作比例）：

```
策略                  AllC   AllD   TFT    Grudg  Rand
AlwaysCheat           0.08   0.08   0.08   0.08   0.07
AlwaysCooperate       0.92   0.92   0.92   0.92   0.93
Awkward               0.84   0.84   0.84   0.84   0.85
Bully                 0.37   0.92   0.83   0.91   0.93
ChaoticRedeemer       0.42   0.12   0.28   0.19   0.19
GenerousTitForTat     0.88   0.23   0.62   0.29   0.55
GlobalPavlov          0.58   0.51   0.49   0.53   0.51
Grudger               0.21   0.09   0.14   0.14   0.08
Joss                  0.78   0.13   0.39   0.15   0.45
LimitedPunisher       0.92   0.61   0.92   0.64   0.82
Pavlov                0.58   0.51   0.49   0.53   0.51
Random                0.50   0.50   0.50   0.50   0.51
Redeemer              0.92   0.10   0.77   0.17   0.22
SkepticalRedeemer     0.93   0.17   0.93   0.26   0.69
SmartEnvious          0.92   0.92   0.92   0.92   0.93
SmartProber           0.73   0.73   0.73   0.73   0.61
Statistical           0.92   0.16   0.92   0.20   0.47
StochasticPavlov      0.51   0.48   0.56   0.49   0.49
TitForTat             0.87   0.14   0.46   0.19   0.52
TitForTwoTats         0.92   0.19   0.90   0.25   0.73
TolerantGrudger       0.92   0.10   0.92   0.18   0.24
```

**近似行為群組**（合作率⊕正規化得分 向量歐氏距離 < 0.10）：3 組

1. `{GlobalPavlov, Pavlov, Random, StochasticPavlov}`
2. `{AlwaysCooperate, SmartEnvious}`
3. `{SkepticalRedeemer, TitForTwoTats}`

最相近前 6 對：`GlobalPavlov≈Pavlov (0.000)`、`AlwaysCooperate≈SmartEnvious (0.004)`、`SkepticalRedeemer≈TitForTwoTats (0.062)`、`Random≈StochasticPavlov (0.074)`、`GlobalPavlov≈Random (0.090)`、`Pavlov≈Random (0.090)`。

> 刪掉 2 檔後，原本的 `{ForgivingTitForTat, TitForTat}` 群組整個消失（TFT 現在獨立），GreedyProber 也從 Pavlov/Random blob 移除——證實這 2 個確實是「輸出與既有策略雷同」的重複。

**逐組判讀（指紋只是嫌疑，機制才是判決）：**

- **群組 1（~0.5 blob）**：`GlobalPavlov` 在 1v1 下「全局上一場」≡「對此對手上一場」，故與 `Pavlov` 指紋天生相同（距離 0.000）——但它在多人 sim 有獨特「遷怒」跨對手耦合（README 招牌機制），指紋看不到。`Random` 是純擲硬幣、`StochasticPavlov` 是機率性 WSLS（輸了會猶豫不切換），三者只是邊際統計 ~0.5 巧合，機制全不同。**→ 全留。**
- **群組 2**：`SmartEnvious` 對此 panel 等同 `AllCooperate`，是因為 1v1 嫉妒條件幾乎不觸發（雙方都合作→分數相等→`opp>me` 為假）。它真正的機制是「嫉妒觸發的條件式剝削」，指紋天生看不到。**→ 留。**
- **群組 3**：`SkepticalRedeemer` 對 panel 的淨合作率近似 `TitForTwoTats`，但機制完全不同（機率誤審＋救贖計數＋讀意圖 vs 只看最近 2 回合實際手）。**→ 留。**

---

## 三、最終決策（已執行）

逐一複查每個「指紋嫌疑」後，**只刪 2 個真冗餘，其餘全部保留**。

### 🔴 已刪除（2）— 唯一站得住的真冗餘

| 策略 | 冗餘對象 | 證據 |
|---|---|---|
| `GreedyProber` | `SmartProber` | 偵察/分類/剝削骨架**逐行相同**，唯一差別是「對好人改演 GTFT＋Joss 偷襲」；而 `Joss` 已單獨存在 → 偵察骨架與 Joss 味兩個成分都重複。 |
| `ForgivingTitForTat` | `TitForTat` | 與 TFT 近重複（指紋群組 3 已消失即證）；保留 TFT（科學基準）＋ GTFT（誠實的機率性抗噪），FTFT 的 intended-oracle 抗噪職能由 GTFT 以更正當方式覆蓋。 |

### 🟢 指紋曾標「冗餘」但**保留**（機制獨特，指紋誤判）

| 策略 | 指紋為何誤判 | 真正的獨特機制 |
|---|---|---|
| `SkepticalRedeemer` | 淨合作率近 TitForTwoTats | 唯一具「機率性誤審 25%（對惡意 75% 放過、對無辜 25% 錯罰）＋ 救贖計數（互助 −1）＋ 讀意圖」 |
| `TolerantGrudger` | 對 panel 近多個寬容者 | 「三振**終身**放逐」——與 Grudger（一振終身）、TitForTwoTats（報復一次就原諒）皆不同 |
| `SmartEnvious` | 1v1 觸發不了嫉妒，看似 AllC | 嫉妒觸發的**條件式剝削**（對手均分>我 且 作弊率<3% 才攻擊） |
| `ChaoticRedeemer` | 在 Redeemer 家族中 | 「**對稱**噪音感知」——Redeemer 三兄弟「完美感知→對稱噪音→非對稱偏誤」階梯的中間階，刪了階梯就斷 |
| `StochasticPavlov` | ~0.5 blob | 機率性 Win-Stay-Lose-Shift（輸了會「猶豫」不一定切換），非確定性 Pavlov |

### ⚪ 其餘保留（經典錨點 + 生態主角 + 獨特機制）
`AlwaysCooperate`、`AlwaysCheat`、`TitForTat`、`Random`、`Grudger`、`Pavlov`（Axelrod 經典參考）；`Awkward`、`Joss`（生態主角）；`GenerousTitForTat`（最強善良/誠實抗噪）；`GlobalPavlov`（遷怒跨對手耦合，專案招牌）；`Bully`（攀附強者/霸凌弱者）；`Redeemer`、`SmartProber`、`Statistical`、`LimitedPunisher`、`TitForTwoTats`（各有獨特機制）。

→ 23 − 2 = **21 個策略**。

---

## 如何重現

```bash
# 行為指紋（數十秒）
docker run --rm -e TQDM_DISABLE=1 -v "$(pwd):/app" <image> python -u -m tools.fingerprint

# 存活率研究（多核平行；可用 SURV_* 環境變數調整規模，建議 SURV_WORKERS=核心數）
docker run --rm -e TQDM_DISABLE=1 -e SURV_WORKERS=20 -v "$(pwd):/app" <image> python -u -m tools.survival
```

> 本次 21 策略數據於遠端 20 核測試機重產（`SURV_WORKERS=20`，固定 seed）。拜 Phase 1 的 22× 加速所賜，40 runs × 100 世代得以在數分鐘內跑完。

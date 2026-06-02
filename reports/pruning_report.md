# 策略瘦身分析報告

> 產生日期：2026-06-02 · 分析工具：`tools/fingerprint.py`、`tools/survival.py`
> **本報告只提供分析與建議，不移動/刪除任何策略檔。最終取捨由你決定。**

## TL;DR

- 目前 23 個策略，**建議精簡到約 16 個**（砍 ~7 個冗餘/重疊變體），可加速抽樣且不損科學價值。
- 刪除依據以**行為指紋冗餘**為主（找「行為近乎雷同」的雙胞胎），**存活率研究**為輔（生態背景）。
- 經典參考策略（TFT / AllC / AllD / Random / Grudger / Pavlov）即使在本生態中落敗，仍**建議保留**作為科學錨點。

---

## 方法

兩個互補信號，皆在容器內、固定 seed、可重現：

| 信號 | 工具 | 看什麼 | 限制 |
|---|---|---|---|
| **行為指紋**（主，去重用） | `fingerprint.py` | 對固定 panel（AllC/AllD/TFT/Grudger/Random）的「合作率＋得分」向量，多 seed 平均（雜訊 5%） | 1v1 量測，**看不到跨對手耦合**（如 GlobalPavlov 的遷怒），也無法觸發只對特定對手才顯現的行為 |
| **存活率**（輔，生態背景） | `survival.py` | 真實多人演化跑 40 runs × 100 世代，統計存活/滅絕 | 結果隨選擇壓力與參數變動；本生態趨向「贏家通吃」 |

---

## 一、存活率研究（生態背景）

40 runs × 100 世代，`rounds=80 matches=50 noise=5% kill=5`，初始每種 6 個體。

| # | 策略 | 存活率 | 平均佔比 | 滅絕率 | 平均滅絕世代 | 平均名次 |
|---|---|---|---|---|---|---|
| 1 | **Awkward** | 100% | 63.5% | 0% | — | 1.1 |
| 2 | **Joss** | 95% | 30.3% | 5% | 91 | 2.2 |
| 3 | GenerousTitForTat | 15% | 4.2% | 85% | 78 | 2.9 |
| 4 | TitForTat | 10% | 0.6% | 90% | 63 | 3.9 |
| 5 | TolerantGrudger | 8% | 0.8% | 92% | 49 | 6.3 |
| 6 | ChaoticRedeemer | 5% | 0.3% | 95% | 23 | 14.4 |
| 7 | Redeemer | 5% | 0.1% | 95% | 49 | 6.4 |
| 8 | TitForTwoTats | 2% | 0.2% | 98% | 46 | 8.1 |
| 9 | ForgivingTitForTat | 0% | — | 100% | 46 | 7.8 |
| 10 | SkepticalRedeemer | 0% | — | 100% | 41 | 9.7 |
| 11 | Statistical | 0% | — | 100% | 41 | 9.9 |
| 12 | LimitedPunisher | 0% | — | 100% | 40 | 10.3 |
| 13 | GreedyProber | 0% | — | 100% | 30 | 13.2 |
| 14 | SmartProber | 0% | — | 100% | 28 | 14.0 |
| 15 | AlwaysCooperate | 0% | — | 100% | 28 | 14.2 |
| 16 | SmartEnvious | 0% | — | 100% | 24 | 14.3 |
| 17 | Grudger | 0% | — | 100% | 14 | 16.6 |
| 18 | StochasticPavlov | 0% | — | 100% | 12 | 18.4 |
| 19 | Random | 0% | — | 100% | 12 | 18.7 |
| 20 | GlobalPavlov | 0% | — | 100% | 12 | 19.4 |
| 21 | Pavlov | 0% | — | 100% | 11 | 19.8 |
| 22 | AlwaysCheat | 0% | — | 100% | 9 | 21.6 |
| 23 | Bully | 0% | — | 100% | 5 | 22.8 |

**解讀：**
- **Awkward + Joss 通吃**（合計佔比 ~94%）。兩者本質都是「大多合作、約 10% 偷背叛、且不記仇」。
- 在這種高雜訊環境（外部 5% + 內部 2% + Awkward 自帶 10% 手滑），**會報復的策略（TFT/Grudger 家族）被雜訊拖進互相懲罰而自我毀滅**，不報復的寬容者反而勝出——這是噪音 IPD 的已知結論。
- **AllCheat（第 22）、Bully（第 23）最早滅絕**：背叛者在族群中互相懲罰（P=1），打不過合作叢集（R=3）。
- ⚠️ 因此「滅絕率高」**不等於**「該刪」——TFT 等是因生態被 Awkward 主宰而落敗，非本身冗餘。這份榜單是**背景**，不是刪除清單。

---

## 二、行為指紋去重（主信號）

合作率指紋（對 panel，多 seed 平均；數值=合作比例）：

```
策略                  AllC   AllD   TFT    Grudg  Rand
AlwaysCheat           0.08   0.08   0.08   0.08   0.07
AlwaysCooperate       0.92   0.92   0.92   0.92   0.93
Awkward               0.84   0.84   0.84   0.84   0.85
Bully                 0.37   0.92   0.83   0.91   0.93
ChaoticRedeemer       0.42   0.12   0.28   0.19   0.19
ForgivingTitForTat    0.91   0.10   0.48   0.16   0.51
GenerousTitForTat     0.88   0.23   0.62   0.29   0.55
GlobalPavlov          0.58   0.51   0.49   0.53   0.51
GreedyProber          0.52   0.52   0.52   0.52   0.52
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

**近似行為群組**（合作率⊕正規化得分 向量歐氏距離 < 0.10）：

1. `{GlobalPavlov, GreedyProber, Pavlov, Random, StochasticPavlov}`
2. `{AlwaysCooperate, SmartEnvious}`
3. `{ForgivingTitForTat, TitForTat}`
4. `{SkepticalRedeemer, TitForTwoTats}`

**逐組判讀（重要——指紋只是嫌疑，不是判決）：**

- **群組 1（~0.5 blob）**：這 5 個對 panel 的合作率/得分都 ~0.5，難以區分。但要小心兩個假象：
  - `GlobalPavlov`：1v1 下「全局上一場」≡「對此對手上一場」，故與 `Pavlov` 指紋**天生相同**（距離 0.000）；但它在多人 sim 有獨特的「遷怒」耦合（README 的招牌機制）→ **不該僅憑指紋刪**。
  - `Random`：純擲硬幣，機制與 Pavlov 完全不同，只是邊際統計巧合 ~0.5。
  - 真正可視為冗餘的是 `StochasticPavlov`（Pavlov 的隨機版）與 `GreedyProber`（淨合作率 ~0.5，探測後行為接近 random/pavlov）。
- **群組 2**：`SmartEnvious` 對此 panel 表現等同 `AllCooperate`（它只在「嫉妒且對手是和平主義者」時才剝削，panel 沒有這種觸發對象）。其獨特邏輯指紋看不到，但生態中也快速滅絕（第 24 世代）。
- **群組 3**：`ForgivingTitForTat` ≈ `TitForTat`，差別只在偶爾原諒——與 `GenerousTitForTat` 的「寬容」職能重疊。
- **群組 4**：`SkepticalRedeemer` ≈ `TitForTwoTats`（兩者都「需兩次背叛才反應」式的寬容）。

---

## 三、建議（你來決定，我不動檔）

把策略分三層：

### 🟢 建議保留（11）— 經典錨點 + 生態主角 + 機制獨特
`AlwaysCooperate`、`AlwaysCheat`、`TitForTat`、`Random`、`Grudger`、`Pavlov`（經典 Axelrod 參考組）；
`Awkward`、`Joss`（本生態主角）；`GenerousTitForTat`（噪音環境的代表寬容者、最強善良策略）；
`GlobalPavlov`（獨特「遷怒」跨對手耦合，專案招牌）；`Bully`（獨特「攀附強者/霸凌弱者」社會階層機制）。

### 🟡 建議刪除候選（7）— 行為冗餘 + 生態無競爭力
| 策略 | 冗餘對象 | 證據 |
|---|---|---|
| `StochasticPavlov` | Pavlov | 群組 1；滅絕世代 12 |
| `GreedyProber` | SmartProber | 群組 1（淨 ~0.5）；保留 SmartProber 當探測代表 |
| `ForgivingTitForTat` | TitForTat / GTFT | 群組 3；寬容職能與 GTFT 重疊 |
| `SkepticalRedeemer` | TitForTwoTats | 群組 4 |
| `ChaoticRedeemer` | Redeemer 家族 | redeemer 三變體取一即可；滅絕世代 23 |
| `SmartEnvious` | AlwaysCooperate | 群組 2（vs panel 等同 AllC） |
| `TitForTwoTats` 或 `TolerantGrudger` | 二擇一 | 兩者都是「延遲反應/寬容怨恨」變體，職能重疊，留一個 |

→ 砍 7 個後剩 **16 個**。

### ⚪ 邊界案例（你的研究偏好決定）
- `Statistical`、`LimitedPunisher`、`Redeemer`、`SmartProber`：各有獨特機制（滑動窗口/有限懲罰/救贖/試探分類），雖在本生態落敗，但**機制不重複**，保留與否看你想保留多少「行為多樣性」。
- `SmartEnvious`：若你想保留「嫉妒剝削」這個獨特行為維度，可改用一個能觸發它的 panel 重測再決定。

---

## 如何重現

```bash
# 行為指紋（數十秒）
docker run --rm -e TQDM_DISABLE=1 -v "$(pwd):/app" <image> python -u -m tools.fingerprint

# 存活率研究（多核平行；可用 SURV_* 環境變數調整規模）
docker run --rm -e TQDM_DISABLE=1 -v "$(pwd):/app" <image> python -u -m tools.survival
```

> 拜 Phase 1 的 22× 加速所賜，40 runs × 100 世代的存活率研究才得以在可接受時間內跑完——這正是「賽局加速」帶來的紅利。

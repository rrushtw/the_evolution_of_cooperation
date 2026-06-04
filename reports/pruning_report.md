# 策略瘦身分析報告

> 初版日期：2026-06-02 · 更新：2026-06-03（依機制多樣性原則收斂並**實際刪除**；**修正 survival 參數失真**，改為忠實重用正式 app 演化、N=50 跑到穩定）
> 分析工具：`tools/fingerprint.py`、`tools/survival.py`（數據於遠端 20 核測試機重產，固定 seed 可重現）

## TL;DR

- 原始 23 個策略，**實際只刪 2 個**（`ForgivingTitForTat`、`GreedyProber`）→ 精簡到 **21 個**。
- 一開始指紋分析「建議砍 7 個」，但逐一複查後**收斂到 2 個**。核心教訓：

  > **🔑 機制多樣性 > 輸出指紋。** 行為指紋量的是「對固定 panel 的**輸出行為**」，但本 repo 的策略大多靠**內部機制／觸發條件**區分。**輸出相似 ≠ 機制相同** —— 1v1 對 panel 觸發不了嫉妒、救贖、永久拉黑等獨特邏輯，於是指紋把機制完全不同的策略誤併。指紋只能當「嫌疑」，不能當「判決」。

- 真正站得住的刪除只有「骨架/職能逐行重複、且重複成分已單獨存在」的 2 個。經典參考策略（TFT / AllC / AllD / Random / Grudger / Pavlov）一律保留作為科學錨點。

---

## 方法

兩個互補信號，皆在容器內、固定 seed、可重現：

**行為指紋（找嫌疑）— `fingerprint.py`**
- 看什麼：對固定 panel（AllC/AllD/TFT/Grudger/Random）的「合作率＋得分」向量，多 seed 平均（雜訊 5%）。
- 限制：1v1 量測，**看不到跨對手耦合**（如 GlobalPavlov 的遷怒），也觸發不了只對特定對手才顯現的條件邏輯（嫉妒/救贖/拉黑）。

**勝率（生態背景）— `survival.py`**
- 看什麼：**直接重用正式 app 的演化迴圈**（`simulation.run_evolution_simulation`，`rounds=200 matches=100 noise=5% kill=5`、跑到 `stability=100` 連續穩定），跑 N=50 個 seed，統計每個策略的**奪冠頻率**（Wilson 95% CI）、top-3/top-5 入榜率、平均名次。
- 限制：結果隨選擇壓力變動；**奪冠≠不可刪、墊底≠該刪**（去重看指紋，不看生態）。

---

## 一、勝率研究（生態背景，21 策略）

> ⚠️ **修正紀錄（2026-06-03）**：本節初版用了一個**自行重寫的縮水演化迴圈**（`rounds=80 matches=50`、封頂 100 代），與正式 app（`rounds=200 matches=100`、跑到穩定）規模差 5 倍且沒跑到均衡，得出「Awkward+Joss 通吃、報復者自滅」的**失真結論**——那只是「早期剝削暫態」的假象。現已把 `survival.py` 改成**直接重用正式 app 的 `simulation.run_evolution_simulation`**，工具與 app 永不再分岔。以下為更正後結果。

**N=50 次完整演化**（seeds 1..50，每次**跑到穩定**），參數＝正式 app 預設（`rounds=200 matches=100 noise=5% kill=5 stability=100`，初始每種 6 個體）。記錄每次的**奪冠者**與最終名次；奪冠率附 Wilson 95% CI。遠端 20 核跑了 ~4.4 小時。

| 策略 | 奪冠 | 奪冠率 (95% CI) | top-3 | top-5 | 平均名次 |
|---|---|---|---|---|---|
| **GenerousTitForTat** | 39/50 | **78% [65%,87%]** | 96% | 96% | **1.5** |
| **SkepticalRedeemer** | 5/50 | 10% [4%,21%] | 66% | 96% | 3.1 |
| **TitForTwoTats** | 3/50 | 6% [2%,16%] | 36% | 90% | 3.9 |
| SmartProber | 2/50 | 4% [1%,13%] | 56% | 84% | 3.5 |
| Awkward | 1/50 | 2% [0%,10%] | 2% | 4% | 10.5 |
| LimitedPunisher | 0/50 | 0% [0%,7%] | 12% | 62% | 5.1 |
| AlwaysCooperate | 0/50 | 0% [0%,7%] | 24% | 56% | 5.0 |
| TitForTat | 0/50 | 0% [0%,7%] | 6% | 8% | 7.1 |
| TolerantGrudger | 0/50 | 0% [0%,7%] | 2% | 4% | 8.5 |
| Statistical | 0/50 | 0% [0%,7%] | 0% | 0% | 7.9 |
| Redeemer | 0/50 | 0% [0%,7%] | 0% | 0% | 9.8 |
| SmartEnvious | 0/50 | 0% [0%,7%] | 0% | 0% | 12.4 |
| Joss | 0/50 | 0% [0%,7%] | 0% | 0% | 12.6 |
| ChaoticRedeemer | 0/50 | 0% [0%,7%] | 0% | 0% | 14.0 |
| Grudger | 0/50 | 0% [0%,7%] | 0% | 0% | 15.0 |
| AlwaysCheat | 0/50 | 0% [0%,7%] | 0% | 0% | 16.0 |
| GlobalPavlov | 0/50 | 0% [0%,7%] | 0% | 0% | 17.2 |
| Random | 0/50 | 0% [0%,7%] | 0% | 0% | 17.8 |
| StochasticPavlov | 0/50 | 0% [0%,7%] | 0% | 0% | 19.5 |
| Pavlov | 0/50 | 0% [0%,7%] | 0% | 0% | 19.5 |
| Bully | 0/50 | 0% [0%,7%] | 0% | 0% | 21.0 |

**具體結論：**
- **🏆 系統治冠軍**：`GenerousTitForTat`（奪冠 78%、top-5 96%、平均名次 1.5）——這是**經典 Axelrod 結果**：善良（不先背叛）＋ 會報復 ＋ 寬容（10% 機率原諒，打破噪音死亡螺旋）的 nice reciprocator 長期勝出。
- **🥈 穩定強者**：`SkepticalRedeemer`（奪冠 10%、**top-5 96%**）、`TitForTwoTats`（奪冠 6%、**top-5 90%**）——兩者幾乎每局都進前五，是僅次於 GTFT 的常勝群。`SmartProber`、`AlwaysCooperate`、`LimitedPunisher` 也常在前段。
- **💀 背叛/剝削者墊底**：`Joss`（平均名次 12.6、**0 奪冠**）、`Bully`(21.0)、`AlwaysCheat`(16.0)、Pavlov 家族與 `Random` 全在後段。`Awkward` 雖僥倖奪冠 1 次，平均名次也只有 10.5（中後段）。
- ⚠️「墊底」**不等於**「該刪」——這份榜單只是**生態背景**，去重的判準是行為指紋（見下節），不是勝率。經典參考策略（TFT/AllC/AllD/Random/Grudger/Pavlov）即使在本生態落敗仍保留作科學錨點。

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

- **`GreedyProber`（冗餘於 `SmartProber`）**：偵察/分類/剝削骨架**逐行相同**，唯一差別是「對好人改演 GTFT＋Joss 偷襲」；而 `Joss` 已單獨存在 → 偵察骨架與 Joss 味兩個成分都重複。
- **`ForgivingTitForTat`（冗餘於 `TitForTat`）**：與 TFT 近重複（指紋群組 3 已消失即證）；保留 TFT（科學基準）＋ GTFT（誠實的機率性抗噪），FTFT 的 intended-oracle 抗噪職能由 GTFT 以更正當方式覆蓋。

### 🟢 指紋曾標「冗餘」但**保留**（機制獨特，指紋誤判）

- **`SkepticalRedeemer`**：指紋誤判是因淨合作率近 TitForTwoTats；但它是唯一具「機率性誤審 25%（對惡意 75% 放過、對無辜 25% 錯罰）＋ 救贖計數（互助 −1）＋ 讀意圖」者。
- **`TolerantGrudger`**：指紋誤判是因對 panel 近多個寬容者；但它是「三振**終身**放逐」——與 Grudger（一振終身）、TitForTwoTats（報復一次就原諒）皆不同。
- **`SmartEnvious`**：指紋誤判是因 1v1 觸發不了嫉妒、看似 AllC；真正機制是嫉妒觸發的**條件式剝削**（對手均分>我 且 作弊率<3% 才攻擊）。
- **`ChaoticRedeemer`**：指紋誤判是因落在 Redeemer 家族中；它是「**對稱**噪音感知」——Redeemer 三兄弟「完美感知→對稱噪音→非對稱偏誤」階梯的中間階，刪了階梯就斷。
- **`StochasticPavlov`**：指紋誤判是因落在 ~0.5 blob；它是機率性 Win-Stay-Lose-Shift（輸了會「猶豫」不一定切換），非確定性 Pavlov。

### ⚪ 其餘保留（經典錨點 + 生態主角 + 獨特機制）
`AlwaysCooperate`、`AlwaysCheat`、`TitForTat`、`Random`、`Grudger`、`Pavlov`（Axelrod 經典參考）；`Awkward`、`Joss`（生態主角）；`GenerousTitForTat`（最強善良/誠實抗噪）；`GlobalPavlov`（遷怒跨對手耦合，專案招牌）；`Bully`（攀附強者/霸凌弱者）；`Redeemer`、`SmartProber`、`Statistical`、`LimitedPunisher`、`TitForTwoTats`（各有獨特機制）。

→ 23 − 2 = **21 個策略**。

---

## 如何重現

```bash
# 行為指紋（數十秒）
docker run --rm -e TQDM_DISABLE=1 -v "$(pwd):/app" <image> python -u -m tools.fingerprint

# 勝率研究（忠實重用正式 app 演化，跑到穩定；本報告用 N=50，工具預設 SURV_RUNS=30）
docker run --rm -e TQDM_DISABLE=1 -e SURV_RUNS=50 -e SURV_WORKERS=20 -v "$(pwd):/app" <image> python -u -m tools.survival
```

> 本報告的勝率數據於遠端 20 核測試機以 **N=50 次完整演化**（seeds 1..50，每次**跑到 `stability=100` 穩定**，固定可重現）重產，耗時 ~4.4 小時。工具直接呼叫 `simulation.run_evolution_simulation`（與正式 app 同一套邏輯、同預設參數），輸出每策略的奪冠率（Wilson 95% CI）、top-3/top-5 入榜率與平均名次。
> ⚠️ 切勿為了加速而調小 `SURV_ROUNDS`/`SURV_MATCHES` 或封頂世代——初版正因此（80/50、封頂 100 代）停在「早期剝削暫態」，得出與正式 app 完全相反的失真結論。

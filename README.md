# 合作的演化：演化模擬器 (Evolutionary Simulation)

這是一個受到 Robert Axelrod 經典著作《合作的演化》(The Evolution of Cooperation) 啟發的 Python 專案。

本專案從一個「單次循環賽」模擬器，已升級為一個完整的「演化模擬器」。它不再是回答「哪個策略單次最強？」，而是回答「哪個策略能在演化中存活下來？」。

## 專案核心機制

本模擬器採用「世代」(Generation) 推進的模式：

1. 初始化 (Initialize): 系統會為 strategies/ 目錄下的每種策略，產生 N 個「個體 (instances)」(例如 10 個)，建立一個大型群體。
2. 評估 (Evaluation): 在每個世代，群體中的所有個體都會進行一次完整的循環賽 (由 engine.py 搭配 tqdm 進度條執行)。
3. 演化 (Evolve):
    - 淘汰 (Selection): 該世代中得分最低的 5 個個體將被淘汰（死亡）。
    - 補位 (Reproduction): 得分最高的 5 個個體的「種類 (Type)」將被複製（誕生），並加入群體中，維持總數恆定。
4. 排名 (Ranking): 最終排名由「種類的滅絕順序」決定。最先在群體中歸零的策略種類，排名最低。
5. 終止 (Termination): 當生態系達到穩定（存活的種類組合連續 100 世代不變），或只剩下一種策略時，模擬結束。

## 專案結構
```
project/
├── .devcontainer/         # <-- 包含 Dev Container 設定
├── app.py                 # <-- 專案主程式 (啟動演化模擬)
├── simulation.py          # <-- 【新】演化模擬器 (管理世代、淘汰、補位)
├── engine.py              # <-- 核心循環賽引擎 (被 simulation 呼叫)
├── definitions.py         # <-- 遊戲核心定義 (Move, MatchResult, PAYOFF)
├── requirements.txt
└── strategies/            # <-- 存放所有策略的目錄
    ├── base_strategy.py   # <-- 所有策略的 "抽象合約"
    ├── always_cheat.py
    ├── always_cooperate.py
    ├── tit_for_tat.py
    ├── grudger.py
    ├── pavlov.py
    ├── global_pavlov.py
    ├── random.py
    └── ... (所有其他策略)
```

## 如何執行

本專案已配置 Dev Container，推薦使用。

1. 使用 Dev Container (推薦)
    1. 在 VS Code 中開啟此專案。
    2. VS Code 偵測到 `.devcontainer` 後，選擇 "Reopen in Container"。
    3. `postCreateCommand` 將自動執行 `pip install -r requirements.txt` 安裝所有依賴。
    4. 待容器建立完成後，直接在 VS Code 的終端機中執行：
    ``` sh
    python app.py
    ```
2. 在本機 (Local) 執行
如果您未在 Dev Container 中開啟，請手動執行以下步驟：
    1. 安裝依賴 (包含 tqdm)：
    ``` sh
    pip install -r requirements.txt
    ```
    2. 執行主程式 `app.py`：
    ``` sh
    python app.py
    ```

app.py 會自動從 strategies/ 目錄載入所有策略，並執行兩次完整的演化模擬：
1. 無雜訊 (0% Noise) 環境。
2. 有雜訊 (5% Noise) 環境。

模擬結束後，您會在終端機底部看到一份並排的「最終總結排名」。

## S策略的雙重記憶系統

本專案的 `BaseStrategy` 具有一個獨特的雙重記憶系統：

1. 私有記憶 (`self.opponent_history`): 策略與特定對手的「私怨」。
2. 公開日誌 (`self.my_history`): 策略的「全局歷史」。

在 `play` 時，`engine` 會將對手的「公開日誌」(`opponent_history`) 傳遞給策略，使其可以同時分析「私怨」和「公評」來做出決策。
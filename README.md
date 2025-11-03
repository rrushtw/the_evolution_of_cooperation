# 合作的演化：演化模擬器 (Evolutionary Simulation)

這是一個受到 Robert Axelrod 經典著作《合作的演化》(The Evolution of Cooperation) 啟發的 Python 專案。

本專案從一個「單次循環賽」模擬器，已升級為一個完整的「演化模擬器」。它不再是回答「哪個策略*單次*最強？」，而是回答「哪個策略能在*演化*中存活下來？」。

## 專案核心機制

本模擬器採用「世代」(Generation) 推進的模式：

1.  **初始化 (Initialize):** 系統會為 `strategies/` 目錄下的**每種**策略，產生 N 個「個體 (instances)」(例如 10 個)，建立一個大型群體。

2.  **評估 (Evaluation):** 在**每個世代**，`engine.py` 會執行一個「**隨機互動模型**」。在總互動次數（例如 700,000 次）內，*每一次*都**隨機**抽取 2 個個體進行 1 回合的互動。
    * 這個機制使得策略（如 `GlobalPavlov`）的「情緒」可以真實地「遷怒」到下一個隨機對手，完美模擬了「路徑依賴」(path-dependent) 的現實社交。

3.  **演化 (Evolve):**
    * **淘汰 (Selection):** 該世代中得分**最低**的 5 個個體將被淘汰（死亡）。
    * **補位 (Reproduction):** 得分**最高**的 5 個個體的「種類 (Type)」將被複製（誕生），並加入群體中，維持總數恆定。

4.  **排名 (Ranking):** 最終排名由「種類的滅絕順序」決定。最先在群體中歸零的策略種類，排名最低。

5.  **終止 (Termination):** 當生態系達到穩定（存活的種類組合連續 100 世代不變），或只剩下一種策略時，模擬結束。

## 核心機制：雙重雜訊模型 (Dual Noise Model)

本模擬器實現了兩種截然不同的「雜訊」，以創造一個更真實的環境：

1.  **內部雜訊 (Internal Noise / 2%):**
    * 由 `BaseStrategy` 的 `apply_internal_noise()` 方法控制（預設 2%）。
    * 這模擬「**手滑**」或「**口吃**」。一個策略的「真實意圖」在「說出口」的瞬間被翻轉。
    * **關鍵：** `engine` 會將這個「手滑後的意圖」傳遞給 `update` 函式。因此，所有策略（包括「上帝視角」的 `ForgivingRedeemer`）**都會**將此視為「**故意的**」行為並進行懲罰。

2.  **外部雜訊 (External Noise / 5%):**
    * 由 `engine.py` 的 `apply_noise()` 方法控制（預設 5%）。
    * 這模擬「**環境干擾**」或「**誤解**」（例如訊號不良）。
    * **關鍵：** `engine` *不會*將此雜訊告知 `update` 函式。「看意圖」的策略（如 `Forgiving...`）**可以**看穿這種雜訊，從而原諒「意外」。

## 策略的雙重記憶系統

本專案的 `BaseStrategy` 具有一個獨特的雙重記憶系統：

1.  **私有記憶 (`self.opponent_history`)**: 策略與特定對手的「私怨」（使用 `unique_id` 區分）。
2.  **公開日誌 (`self.my_history`)**: 策略的「全局歷史」（用於「遷怒」）。

在 `play` 時，`engine` 會將對手的「公開日誌」(`opponent_history`) 傳遞給策略，使其可以同時分析「私怨」和「公評」來做出決策。

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

### 1. 使用 Dev Container (推薦)

1.  在 VS Code 中開啟此專案。
2.  VS Code 偵測到 `.devcontainer` 後，選擇 "Reopen in Container"。
3.  `postCreateCommand` 將自動執行 `pip install -r requirements.txt` 安裝所有依賴。
4.  待容器建立完成後，直接在 VS Code 的終端機中執行：

    ```bash
    python app.py
    ```

### 2. 在本機 (Local) 執行

1.  安裝依賴 (包含 `tqdm`)：

    ```bash
    pip install -r requirements.txt
    ```

2.  執行主程式 `app.py`：

    ```bash
    python app.py
    ```

---

`app.py` 會自動從 `strategies/` 目錄載入所有策略，並執行**一次**演化模擬（預設 5% 雜訊）。

## 🐳 如何執行 (Docker 7x24 模擬)

此專案已打包成 Docker 服務，使其可以在任何支援 Docker 的機器（例如您的測試伺服器）上 7x24 持續運行、監控策略、並匯出統計結果。

### 先決條件

* 已安裝 [Docker Engine](https://docs.docker.com/engine/install/)

### 快速啟動 (前景執行)

1.  **建立 `output` 資料夾**：
    ```bash
    mkdir -p output
    ```

2.  **建置並啟動服務**：
    此命令會自動建置映像檔，並以「前景模式」啟動服務。您會在終端機中即時看到所有日誌 (`print` 訊息)：

    ```bash
    docker-compose up --build
    ```

3.  **停止服務**：
    在終端機中按下 `Ctrl + C`。

---

### 伺服器部署 (背景執行)

1.  **啟動 (背景模式)**：
    使用 `-d` (detached) 參數在背景啟動服務。
    ```bash
    docker-compose up --build -d
    ```

2.  **查看日誌**：
    使用 `-f` (follow) 來即時追蹤日誌 (按下 `Ctrl + C` 退出追蹤，服務會繼續在背景運行)：
    ```bash
    docker-compose logs -f
    ```

3.  **停止服務**：
    ```bash
    docker-compose down
    ```

### 工作流程：動態調整與查看結果

這個 Docker 服務的核心優勢是使用了 `volumes` (掛載)：

* **查看結果**: 容器會持續將 `ranking_..._noise_...pct.json` 檔案寫入 `/app/output`。由於已掛載，這些 JSON 檔案會**即時**出現在您本地的 `./output` 資料夾中，供您分析。
* **調整策略**: 您**不需要**停止服務。您可以直接在本地的 `./strategies` 資料夾中新增、刪除或修改策略的 `.py` 檔案。`app.py` 會在**下一輪**模擬開始時自動重新載入該目錄，並使用您更新後的策略組合。
* **調整參數**: 您可以在 `docker-compose.yml` 檔案中修改 `environment` 區塊的參數 (例如 `NOISE=0.01`)。修改完成後，只需執行 `docker-compose up -d --no-deps` 即可讓容器使用新參數重啟。

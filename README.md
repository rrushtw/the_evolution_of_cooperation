# The Evolution of Cooperation: 重複囚徒困境 (IPD) 模擬器

這是一個受到 Robert Axelrod 經典著作《合作的演化》(The Evolution of Cooperation) 啟發的 Python 專案。

本專案旨在建立一個靈活的模擬引擎，用於測試在「重複囚徒困境」(Iterated Prisoner's Dilemma, IPD) 賽局中，不同策略的演化與生存能力。

## 專案核心設計

與傳統的 IPD 模擬不同，本專案的 `BaseStrategy` (策略基底) 具有一個獨特的雙重記憶系統：

1. 私有記憶 (`self.opponent_history`):
    - 策略儲存其與特定對手的「私怨」。
    - 例如 `TitForTat` (牙還牙) 只會查看這份記憶。
2. 公開日誌 (`self.my_history`):
    - 策略儲存其在所有比賽中的「全局歷史」。
    - `engine` (模擬引擎) 會在每次 `play` 時，將一方的「公開日誌」作為參數 (`opponent_history`) 傳遞給另一方。

這使得高階策略（例如「偵探」策略）不僅可以分析「私怨」，還可以分析對手的「公評」，來決定如何行動。

## 專案結構
```
project/
├── app.py                 # <-- 專案主程式 (執行循環賽)
├── engine.py              # <-- 核心模擬引擎 (play_game, run_tournament)
├── definitions.py         # <-- 遊戲核心定義 (Move, MatchResult, PAYOFF, RESULT_MATRIX)
├── requirements.txt
└── strategies/            # <-- 存放所有策略的目錄
    ├── base_strategy.py   # <-- 所有策略的 "抽象合約"
    ├── always_cheat.py
    ├── always_cooperate.py
    ├── tit_for_tat.py
    ├── grudger.py
    ├── pavlov.py
    ├── global_pavlov.py
    └── random.py
```

## 如何執行

執行主程式 app.py：
``` bash
python app.py
```

`app.py` 預設會執行兩場循環賽：一場在 `0%` 雜訊環境下，一場在 `5%` 雜訊環境下，以便您比較策略在不同環境下的強韌性。

## 目前已實作的策略

- AlwaysCheat: 永遠背叛 (All-D)。
- AlwaysCooperate: 永遠合作 (All-C)。
- TitForTat (TFT): 牙還牙。善良、寬容、易辨識。
- Grudger (怨恨者): 恐怖策略 (Grim Trigger)。善良，但絕不寬恕。
- Pavlov (WSLS): 巴甫洛夫 (贏定輸變)。根據與特定對手的上一回合結果來決策。
- GlobalPavlov: 全局巴甫洛夫。根據自己的全局上一回合（無論對手是誰）的結果來決策。
- Random: 隨機出招 (50% 合作, 50% 背叛)。

## 如何新增您自己的策略

這個架構的擴充性非常高：
1. 在 `strategies/` 目錄下建立一個新檔案 (例如 `my_strategy.py`)。
2. 從 `base_strategy` 匯入並繼承 `BaseStrategy`。
3. 實作 `__init__` (給它一個名字) 和 `play` 方法。
4. `play` 方法會接收 `opponent_id` (私怨) 和 `opponent_history` (對手的公評)。
5. 在 `app.py` 中匯入您的新策略，並將其實例化後加入 `strategy_list`。
6. 執行 `python app.py` 觀察它的表現！
``` py
# strategies/my_strategy.py
from strategies.base_strategy import BaseStrategy
from definitions import Move, MatchResult

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Cool Strategy")

    def play(self, opponent_id: str, opponent_history: list[dict]) -> Move:
        #
        # 在這裡實作您的決策邏輯...
        #
        # 您可以讀取 "私怨":
        # private_log = self.opponent_history.get(opponent_id, [])
        #
        # 您也可以讀取 "公評":
        # public_log = opponent_history
        #
        if len(opponent_history) > 10:
             return Move.CHEAT # 範例
        
        return Move.COOPERATE
```

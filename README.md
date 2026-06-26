# Video Subtitle Translator & Summarizer (通用影音字幕翻譯與重點摘要工具)

自動將影片或音訊進行語音辨識，產生雙語字幕，並藉由 AI 將逐字稿提煉整理為「重點摘要」或「結構化會議紀錄」的完整 Pipeline 自動化工具。

本專案由 [點哥工作坊](https://www.youtube.com/@ckonetw) 頻道主導與推廣，旨在展示如何利用大語言模型 (LLM) 與 AI 語音辨識技術來簡化日常的影音字幕製作、學習摘要與會議紀錄流程。

---

## 💡 專案特色

- **多任務輸出模式**：執行時可藉由 AI 互動選單選擇：
  - 🎥 **雙語字幕翻譯 (subs)**：輸出原文與譯文時間碼對齊的 `.srt` 字幕。
  - 📝 **重點摘要整理 (summary)**：提煉出核心主旨、重點條列摘要（5-10個核心點）、關鍵詞彙解釋的 Markdown 檔案。
  - 💼 **會議紀錄整理 (minutes)**：整理討論主旨、議題討論細節、決議事項與後續行動方案 (Action Items) 的 Markdown 檔案。
  - 🎛️ **全部執行 (all)**：一次生成雙語字幕、重點摘要與會議紀錄。
- **支援純音訊輸入**：不限影片格式，單純的錄音檔（如 `.mp3`, `.wav`, `.m4a`）也可直接轉換為逐字稿，並一鍵產出重點摘要或會議紀錄。
- **通用多語系對翻**：支援任意語系雙向對翻（如英翻中、英翻日、中翻英、中翻日、日翻英等），執行時互動詢問轉換條件。
- **中日語自動切段優化**：針對中/日語等無空格語言引入字元級重新切段演算法，解決傳統英文單字切段在漢字語系失效的問題。
- **超限音訊智慧壓縮**：針對長影音，當抽取出的音軌大於 Groq API 限制（25MB）時，系統會自動分析音訊時長，動態計算出最適合的目標碼率，並進行二次壓縮，確保數小時長片也能順利辨識。
- **環境自動檢測**：程式啟動時會自動偵測系統是否已安裝 `ffmpeg` 與 `ffprobe`，若無則主動引導安裝，亦支援直接將執行檔放於根目錄運行。

---

## 🛠️ 開啟使用六步驟 (Pipeline)

```
            影片/音訊輸入
                  ↓
  ↓ step1: ffmpeg 抽取音訊（若超過 24MB 自動壓縮）
  ↓ step2: 呼叫 Groq Whisper 進行語音辨識，輸出原始 raw 逐字稿
                  ↓
  ┌───────────────┼────────────────┐
  ↓               ↓                ↓ (根據選擇任務執行)
(字幕翻譯)     (重點摘要)       (會議紀錄)
  ↓ step3         ↓ step6          ↓ step6
Gemini 翻譯    Gemini 摘要      Gemini 會議紀錄
  ↓ step4         ↓                ↓
翻譯驗證       輸出 .md 報告     輸出 .md 會議紀錄
  ↓ step5
輸出雙語 .srt
```

---

## 🚀 快速開始

### 1. 安裝 Python 依賴套件
```bash
pip install groq google-generativeai pydub pyyaml
```

### 2. 設定環境 API 與參數
1. 將本專案中的 `config.yaml.example` 複製一份並命名為 `config.yaml`。
2. 開啟 `config.yaml` 並填入您的金鑰：
   - **groq_api_key**: 取得自 [Groq Console](https://console.groq.com)
   - **gemini_api_key**: 取得自 [Google AI Studio](https://aistudio.google.com)

### 3. 安裝 ffmpeg 影音處理工具
本專案依賴 `ffmpeg` 與 `ffprobe`。程式啟動時會自動檢測。
* **Windows 使用者**：
  1. 至 [ffmpeg.org](https://ffmpeg.org/download.html) 下載 Windows 版本的 `ffmpeg.exe` 與 `ffprobe.exe`。
  2. 解壓縮後將含有該檔案的 `bin` 目錄路徑加入系統的 **環境變數 (PATH)** 中。
  3. *或者：* 直接將 `ffmpeg.exe` 和 `ffprobe.exe` 複製並放入本專案的根目錄下。
* **macOS 使用者**：
  ```bash
  brew install ffmpeg
  ```
* **Linux/Ubuntu 使用者**：
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```

---

## 📖 執行方式

在專案目錄下打開終端機，執行以下指令：

```bash
# 基本語法（會自動判斷影片或音訊）
python run.py <影片或音訊路徑>

# 範例
python run.py input_videos/sample.mp4
```

### 常用命令參數
- `--task`：指定任務模式。可選值包括 `subs` (僅字幕，預設)、`summary` (僅產生重點摘要)、`minutes` (僅產生會議紀錄)、`all` (產出所有結果)。若未指定且設定檔為空，啟動時將以選單互動詢問。
- `--source-lang`：來源語言代碼（例如 `en`, `zh`, `ja`）。若未設定且 `config.yaml` 也未指定，啟動時將以互動式選單詢問。輸入 `auto` 可開啟自動語音偵測。
- `--target-lang`：目標翻譯語言（例如 `繁體中文`, `English`, `日本語`）。同上，若未設定將以互動式選單詢問。
- `--config`：指定不同的設定檔路徑（預設 `config.yaml`）
- `--output`：指定字幕輸出路徑（預設 `./output`）
- `--verbose`：印出更詳細的執行日誌與 API 響應細節
- `--step <1-5>`：只執行 Pipeline 的特定單一處理步驟（除錯調校用）

---

## 📺 關於點哥工作坊

本專案與教學資源由 **點哥工作坊** 提供支持。
* **YouTube 頻道**：[點哥工作坊](https://www.youtube.com/@ckonetw)
* **核心分享內容**：
  - AI 代理 (AI Agent) 的實戰與系統化設計
  - 提示詞工程 (Prompt Engineering) 優化技巧
  - 數位工具與自動化工作流實踐
  - 如何運用主管思維，將 AI 轉化為高效的高階助理

歡迎訂閱頻道獲取更多關於 AI 自動化、影片製作與程式開發的最新實戰教學！

---

## 👨‍💻 關於作者

**點哥（昇鴻）** — 哲學與生命教育背景的程式設計教師、正念催眠培訓師。
相信「程式是表達思想的工具」，致力於讓完全不會寫程式的人也能透過 AI 實現自己的想法。

- **GitHub**: [https://github.com/ckhotgav](https://github.com/ckhotgav)
- **Facebook**: [https://facebook.com/jshpapa](https://facebook.com/jshpapa)


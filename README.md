# Video Subtitle Translator (視頻字幕翻譯工具)

自動將英文影片/音訊進行語音辨識，並將字幕翻譯成繁體中文的完整自動化 Pipeline 工具。

本專案由 [點哥工作坊](https://www.youtube.com/@%E9%BB%9E%E5%93%A5%E5%B7%A5%E4%BD%9C%E5%9D%8A) 頻道主導與推廣，旨在展示如何利用大語言模型 (LLM) 與 AI 語音辨識技術來簡化日常的影片字幕製作流程。

---

## 💡 專案特色

- **高效率語音辨識**：採用 Groq Whisper-large-v3-turbo 模型，極速產出 word-level 時間碼。
- **高品質繁中翻譯**：利用 Google Gemini 3.1 Flash Lite 進行智慧批次翻譯，確保翻譯口吻流暢且符合台灣本土習慣。
- **嚴格的時間碼驗證**：獨家開發 step4 翻譯驗證機制，保證譯文與原文時間碼完全對齊，段落不遺漏，不合格自動重試。
- **環境自動檢測**：程式啟動時會自動偵測系統是否已安裝 `ffmpeg` 與 `ffprobe`，若無則主動引導安裝，亦支援直接將執行檔放於根目錄運行。

---

## 🛠️ 開啟使用五步驟 (Pipeline)

```
影片/音訊輸入
  ↓ step1: ffmpeg 抽取音訊並壓縮至 24MB 以下
  ↓ step2: 呼叫 Groq Whisper 進行語音辨識，輸出英文 raw 字幕
  ↓ step3: 使用 Gemini 翻譯（批次處理，強制保持時間碼）
  ↓ step4: 進行嚴格翻譯驗證（行數、時間碼與格式對齊）
  ↓ step5: 輸出最終雙語字幕檔 ( _en.srt 與 _zh.srt )
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
- `--config`：指定不同的設定檔路徑（預設 `config.yaml`）
- `--output`：指定字幕輸出路徑（預設 `./output`）
- `--verbose`：印出更詳細的執行日誌與 API 響應細節
- `--step <1-5>`：只執行 Pipeline 的特定單一處理步驟（除錯調校用）

---

## 📺 關於點哥工作坊

本專案與教學資源由 **點哥工作坊** 提供支持。
* **YouTube 頻道**：[點哥工作坊](https://www.youtube.com/@%E9%BB%9E%E5%93%A5%E5%B7%A5%E4%BD%9C%E5%9D%8A)
* **核心分享內容**：
  - AI 代理 (AI Agent) 的實戰與系統化設計
  - 提示詞工程 (Prompt Engineering) 優化技巧
  - 數位工具與自動化工作流實踐
  - 如何運用主管思維，將 AI 轉化為高效的高階助理

歡迎訂閱頻道獲取更多關於 AI 自動化、影片製作與程式開發的最新實戰教學！

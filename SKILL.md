---
name: video-subtitle-translator
description: >
  自動將英文影片翻譯成繁體中文字幕的完整 Pipeline 技能。
  輸入影片或音檔，輸出原文 SRT 與繁體中文 SRT 兩個獨立檔案，嚴格保證時間碼對齊。

  觸發時機（請積極觸發）：
  - 使用者說「幫我翻譯影片字幕」、「影片加中文字幕」、「英文影片翻成中文」
  - 使用者提到「字幕翻譯」、「subtitle translation」、「幫我做翻譯字幕」
  - 使用者上傳影片或提供影片路徑，詢問如何加字幕
  - 使用者說「幫我生成 SRT」、「產出雙語字幕」、「英翻中字幕檔」
  - 任何涉及影片翻譯、字幕生成、英文轉中文字幕的請求，即使使用者沒說完整指令也要觸發
---

# Video Subtitle Translator：英文影片 → 繁體中文字幕

將英文影片自動產出**原文 SRT**（英文）＋**譯文 SRT**（繁體中文）兩個獨立字幕檔。
時間碼嚴格對齊，不合格自動重試，確保字幕與影片同步。

## 使用的 API（均有免費額度）

| 工具 | 用途 | 免費額度 |
|------|------|----------|
| **Groq Whisper-large-v3-turbo** | 語音辨識，產生 word-level 時間碼 | 每日 7,200 秒音訊 |
| **Google Gemini 2.5 Flash** | 翻譯繁體中文（批次處理） | 每日 1,500 次 |
| **ffmpeg** | 從影片抽取音訊 | 本機免費 |

## 支援輸入格式

`mp4`, `mkv`, `mov`, `avi`, `webm`, `mp3`, `wav`, `m4a`

## 輸出檔案

```
output/
├── {filename}_en.srt    ← 原文英文字幕
└── {filename}_zh.srt    ← 繁體中文字幕
```

---

## Pipeline 五步驟

```
影片/音檔輸入
  ↓ step1_extract.py      ffmpeg 抽取音訊 → mp3（若輸入已是音檔則跳過）
  ↓ step2_transcribe.py   Groq Whisper → word-level 時間碼 → 原文 SRT
  ↓ step3_translate.py    Gemini 批次翻譯 → 繁中 SRT（嚴格保留時間碼）
  ↓ step4_validate.py     三重驗證（段數/時間碼/時間連續性）
  ↓ step5_export.py       輸出 _en.srt 與 _zh.srt
```

---

## 時間碼把關機制（核心）

### 翻譯三條鐵律

step3_translate.py 呼叫 Gemini 時，Prompt 強制要求：

1. **時間碼神聖不可侵犯** — `HH:MM:SS,mmm --> HH:MM:SS,mmm` 完整複製，一個字元都不能動
2. **段落一對一對應** — 輸入 N 段，輸出必須 N 段，不得合併、拆分、新增、刪除
3. **只翻譯文字** — 序號、空行、時間碼格式全部維持原樣

違反任一條 → 自動重試，最多 3 次 → 仍失敗則保留原文並標記 `[翻譯失敗]`

### step4_validate.py 驗證清單

- ✅ 段落總數與原文 SRT 相同
- ✅ 每段時間碼與原文 SRT 完全一致（逐字元比對）
- ✅ 時間碼格式正確（regex 驗證）
- ✅ 每段結束時間 > 開始時間
- ✅ 相鄰段落不重疊（允許 0ms 間隔）

---

## 快速開始

### 1. 安裝依賴

```bash
pip install groq google-generativeai pydub pyyaml
# ffmpeg（系統層級）
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

### 2. 設定 config.yaml

```yaml
groq_api_key: "YOUR_GROQ_KEY"       # https://console.groq.com
gemini_api_key: "YOUR_GEMINI_KEY"   # https://aistudio.google.com

# 翻譯設定
target_language: "繁體中文"
translation_batch_size: 30           # 每次批次翻譯幾段（建議 20-50）
max_retry: 3                         # 驗證失敗最多重試幾次

# 語音辨識設定
whisper_model: "whisper-large-v3-turbo"
max_file_size_mb: 24                 # Groq 限制 25MB，留 1MB 緩衝

# 字幕切段設定
segment_min_sec: 1.0                 # 最短字幕段（秒）
segment_max_sec: 5.0                 # 最長字幕段（秒）
segment_max_chars: 80                # 每段英文最多字元數
```

### 3. 執行

```bash
# 基本用法
python run.py video.mp4

# 指定輸出目錄
python run.py video.mp4 --output ./subtitles

# 只跑指定步驟（除錯用）
python run.py video.mp4 --step 3

# 跳過音訊抽取（已有 mp3）
python run.py audio.mp3

# 詳細 log
python run.py video.mp4 --verbose
```

---

## 專案檔案結構

```
video-subtitle-translator/
├── run.py                  ← 主入口，串接所有步驟
├── config.yaml             ← API 金鑰與參數設定
├── requirements.txt
├── scripts/
│   ├── step1_extract.py    ← ffmpeg 音訊抽取
│   ├── step2_transcribe.py ← Groq Whisper 語音辨識
│   ├── step3_translate.py  ← Gemini 翻譯 + 時間碼保護
│   ├── step4_validate.py   ← 嚴格驗證器
│   └── step5_export.py     ← 輸出 _en.srt 和 _zh.srt
└── output/                 ← 輸出目錄（自動建立）
```

---

## 使用本技能的方式

當使用者要求建立此系統時：

1. **詢問目前狀態** — 從零開始，還是已有部分腳本？
2. **逐步生成腳本** — 依 step1 → step5 順序，每次產出一支完整腳本
3. **生成 run.py + config.yaml** — 串接主入口
4. **測試指引** — 提供測試指令與常見錯誤排除

詳細實作請參閱：
- `references/pipeline-scripts.md` — 各步驟完整實作說明
- `references/prompts.md` — Gemini 翻譯 Prompt 範本

---

## 常見問題排除

| 問題 | 原因 | 解法 |
|------|------|------|
| `413 File too large` | 音檔超過 25MB | step1 自動壓縮，確認 ffmpeg 已安裝 |
| 段數驗證失敗 | Gemini 合併了段落 | 自動重試 3 次，失敗則保留原文 |
| 時間碼不一致 | Gemini 改動了時間碼 | 驗證器會拒絕並重試 |
| `429 Rate limit` | Gemini 超過每分鐘限制 | step3 內建重試，自動等待 60 秒 |
| 翻譯品質不佳 | 批次過大 | 調小 `translation_batch_size`（改為 15） |

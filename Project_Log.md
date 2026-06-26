# Video Subtitle Translator 專案工作日誌

## 專案核心設定異動 (2026-06-26)

> [!IMPORTANT]
> **翻譯模型標準化**：經實測與確認，為避免免費額度 (Free Tier) 的限制 (Rate Limit) 以及模型命名的相容性問題，未來的預設翻譯模型全面改用 **`gemini-3.1-flash-lite`**。此版本速度最快、穩定度高，且 API 呼叫額度充裕，適合處理大量批次的字幕翻譯。

---

## 2026-06-26 流程與修復紀錄

### 1. 專案結構與路徑調整
- **動作**：將原本打包的 `video-subtitle-translator.skill` 解壓縮，並將完整的專案目錄移至 `d:\ANTI 課程AI整理區\影片製作\VST\video-subtitle-translator`，以便集中管理。
- **輸入目錄**：建立專屬的 `input_videos` 資料夾供放置待處理影片。

### 2. 錯誤排除與修復 (Troubleshooting)

在實際處理第一支測試影片 (`The_Illusion_of_Control_Architecting_the_Self-Taught_AI.mp4`) 時，遭遇並修復了以下四個關鍵問題：

#### 🔧 問題一：Windows 終端機編碼錯誤 (UnicodeEncodeError)
- **狀況**：腳本在印出帶有 Emoji (例如 🎬) 的 Log 時，因 Windows 預設的 `cp950` (Big5) 編碼無法解析而引發例外。
- **修復**：在 `run.py` 開頭加入 `sys.stdout.reconfigure(encoding='utf-8')`，強制終端機輸出使用 UTF-8，解決了所有亂碼與崩潰問題。

#### 🔧 問題二：缺少核心依賴套件 (ffmpeg 未安裝)
- **狀況**：系統缺乏 `ffmpeg` 無法抽取影片音軌。
- **修復**：為避免污染使用者的全域環境變數，改採「免安裝版 (Portable)」策略，下載 `ffmpeg-release-essentials.zip`，並將提取出的 `ffmpeg.exe` 直接放置於專案根目錄中。腳本執行時會動態將當前目錄加入 PATH 即可順利調用。

#### 🔧 問題三：Groq API 回傳格式異動 (AttributeError: 'dict' object has no attribute 'text')
- **狀況**：新版的 Groq API 處理 Whisper 語音辨識時，回傳的片段 (segments) 資料結構為字典 (`dict`)，但原始腳本 (`step2_transcribe.py`) 誤用物件屬性方式 (`seg.text`, `seg.start`) 存取，導致程式崩潰。
- **修復**：全面將腳本內的屬性存取方式改為字典鍵值存取 (例如：`seg['text']`, `seg['start']`, `seg['end']`)，順利完成時間碼切段與重組。

#### 🔧 問題四：Gemini 模型名稱與 Rate Limit 限制
- **狀況**：最初嘗試呼叫 `gemini-3.1-flash`（端點尚未支援此名稱，回報 404）以及 `gemini-3.5-flash`（受限於 Free Tier 每分鐘 5 次的嚴格限制，引發 429 Too Many Requests 錯誤）。
- **修復**：採納建議，將翻譯模型改用 **`gemini-3.1-flash-lite`**。此模型擁有充足的免費額度，能穩定且快速地完成批次翻譯。

### 3. 測試執行結果
- **測試檔案**：`The_Illusion_of_Control_Architecting_the_Self-Taught_AI.mp4`
- **結果**：在修復上述所有問題並更換模型後，系統成功將 125 個字幕段落分 5 個批次送出翻譯。
- **驗證**：所有時間碼與段落數的嚴格驗證皆於**第一次就完美通過**，成功輸出 `_en.srt` 與 `_zh.srt` 雙語字幕檔。

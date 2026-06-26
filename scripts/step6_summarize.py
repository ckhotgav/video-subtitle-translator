"""
step6_summarize.py - 使用 Gemini 將逐字稿整理為重點摘要或會議紀錄
"""

import os
import google.generativeai as genai


def summarize_transcript(
    segments: list[dict],
    output_dir: str,
    input_path: str,
    config: dict,
    task_type: str,
) -> str:
    """
    將逐字稿整理為重點摘要或會議紀錄。
    task_type: 'summary' 或 'minutes'
    回傳產出的檔案路徑。
    """
    # 1. 組合逐字稿，附帶時間戳以利 AI 定位時間點
    full_text = "\n".join(f"[{seg['start']}] {seg['text']}" for seg in segments)

    # 2. 設定 Gemini
    genai.configure(api_key=config["gemini_api_key"])
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    target_lang = config.get("target_language", "繁體中文")
    stem = os.path.splitext(os.path.basename(input_path))[0]

    if task_type == "summary":
        prompt = f"""請閱讀以下語音辨識逐字稿（附帶時間碼標記），並使用 {target_lang} 進行系統化的重點摘要整理。

【格式要求，請以 Markdown 輸出】：
# 🎬 影音重點摘要與精簡整理

## 📌 核心主旨
(請用一至兩句話說明此影音的核心內容與主題)

## 📝 重點條列摘要
(請使用條列式整理出最關鍵的 5-10 個核心重點，必須包含具體細節、核心論點或數據，不需加入時間戳記)

## 🔑 關鍵詞彙與名詞解釋
(列出 5 個最重要的關鍵字、術語或概念，並做簡短的說明)

---
【逐字稿內容】：
{full_text}
"""
        out_filename = f"{stem}_summary.md"
        title = "重點摘要"
    else:  # minutes
        prompt = f"""請閱讀以下會議/演講語音辨識逐字稿（附帶時間碼標記），並整理出一份詳細且結構清晰的「會議紀錄（{target_lang}）」。

【格式要求，請以 Markdown 輸出】：
# 💼 影音會議紀錄 / 精準演講整理

## 📝 主題與核心討論
(請說明本次會議/演講的主題與核心大綱)

## 議題討論細節與論點整理
(詳細記錄主要討論議題、各個段落的核心內容、發言者主要論點，可附加適當的時間區間標記如 [00:01:23 - 00:03:15])

## 🎯 決議事項與行動方案 (Action Items)
(條列出本次會議中提及的具體決議事項、待辦工作，以及後續需要追蹤的具體行動方案)

## 🔍 專有名詞與概念註釋
(列出會議中提及的專業術語、專有名詞與簡短解釋)

---
【逐字稿內容】：
{full_text}
"""
        out_filename = f"{stem}_minutes.md"
        title = "會議紀錄"

    print(f"[step6] 正在呼叫 Gemini 生成 {title}...")
    response = model.generate_content(prompt)
    result_md = response.text.strip()

    # 寫出 Markdown 檔案
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, out_filename)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(result_md)

    print(f"[step6] ✅ {title}已導出：{out_path}")
    return out_path

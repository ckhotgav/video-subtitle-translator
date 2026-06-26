"""
step3_translate.py - Gemini 批次翻譯英文字幕為繁體中文
核心機制：嚴格保留時間碼，段落一對一，失敗自動重試
"""

import time
import os
import sys
import google.generativeai as genai
from .step4_validate import validate_translation


def translate(segments: list[dict], config: dict) -> list[dict]:
    """
    批次翻譯所有字幕段落。
    回傳：zh_segments（時間碼與 segments 完全相同，text 為繁體中文）
    """
    genai.configure(api_key=config["gemini_api_key"])
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    batch_size = config.get("translation_batch_size", 30)
    max_retry = config.get("max_retry", 3)
    source_lang = config.get("source_language", "auto")
    target_lang = config.get("target_language", "繁體中文")

    zh_segments = []
    total = len(segments)
    total_batches = (total + batch_size - 1) // batch_size

    for batch_start in range(0, total, batch_size):
        batch = segments[batch_start : batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        end_idx = min(batch_start + batch_size, total)
        print(f"[step3] 批次 {batch_num}/{total_batches}（段落 {batch_start+1}–{end_idx}）")

        translated_batch = None
        last_errors = []

        for attempt in range(1, max_retry + 1):
            try:
                translated_batch = _translate_batch(
                    model, batch, source_lang, target_lang,
                    retry=(attempt > 1), prev_errors=last_errors
                )
                errors = validate_translation(batch, translated_batch)
                if not errors:
                    print(f"[step3]   ✅ 批次 {batch_num} 通過驗證")
                    break
                last_errors = errors
                print(f"[step3]   ⚠️ 第 {attempt} 次驗證失敗（{len(errors)} 個問題）：{errors[0]}")
                if attempt < max_retry:
                    time.sleep(5 * attempt)
                    translated_batch = None
            except Exception as e:
                print(f"[step3]   ❌ 第 {attempt} 次異常：{e}")
                if attempt < max_retry:
                    time.sleep(10 * attempt)
                translated_batch = None

        # 所有重試失敗：保留原文並標記
        if translated_batch is None or validate_translation(batch, translated_batch):
            print(f"[step3]   ⚠️ 批次 {batch_num} 最終失敗，保留原文")
            translated_batch = [
                {**seg, "text": f"[翻譯失敗] {seg['text']}"}
                for seg in batch
            ]

        zh_segments.extend(translated_batch)

        # Rate limit 緩衝（非最後一批）
        if batch_start + batch_size < total:
            time.sleep(1)

    print(f"[step3] ✅ 翻譯完成，共 {len(zh_segments)} 段")
    return zh_segments


def _translate_batch(
    model,
    batch: list[dict],
    source_lang: str,
    target_lang: str,
    retry: bool = False,
    prev_errors: list = None,
) -> list[dict]:
    """
    呼叫 Gemini 翻譯一個批次。
    使用「序號|文字」格式分離序號與內容，防止時間碼被意外修改。
    """
    numbered_texts = "\n".join(
        f"{seg['index']}|{seg['text']}"
        for seg in batch
    )

    # 重試時加入錯誤說明
    retry_note = ""
    if retry and prev_errors:
        retry_note = (
            f"\n⚠️ 上次翻譯失敗原因：{prev_errors[0]}\n"
            "請嚴格遵守格式，每行必須是「序號|譯文」，不得合併或增刪行。\n"
        )

    source_desc = f"（來源語言：{source_lang}）" if source_lang != "auto" else ""
    prompt = f"""你是專業字幕翻譯師，請將以下字幕{source_desc}逐行翻譯為{target_lang}。
{retry_note}
【嚴格規則，違反將導致重新執行】
1. 輸出格式：每行必須是「序號|譯文」，序號與原文完全相同
2. 行數對應：輸入 {len(batch)} 行 → 輸出必須恰好 {len(batch)} 行，不得多也不得少
3. 不得合併多行：每個字幕段落必須獨立翻譯，保持各自的行
4. 翻譯語言：自然流暢的{target_lang}，符合口語字幕習慣
5. 只輸出翻譯結果：不要任何前言、後記、說明或備註

輸入（共 {len(batch)} 行）：
{numbered_texts}

輸出（恰好 {len(batch)} 行）："""

    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    # 解析：過濾空行，取前 N 行
    lines = [l.strip() for l in raw_output.split("\n") if l.strip()]

    result = []
    for seg, line in zip(batch, lines):
        if "|" in line:
            _, zh_text = line.split("|", 1)
        else:
            # 容錯：沒有豎線，整行當譯文
            zh_text = line

        result.append({
            "index": seg["index"],
            "start": seg["start"],   # ← 時間碼完整複製，絕對不修改
            "end": seg["end"],       # ← 時間碼完整複製，絕對不修改
            "text": zh_text.strip(),
        })

    return result

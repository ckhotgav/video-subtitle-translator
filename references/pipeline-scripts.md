# Pipeline Scripts 完整實作說明

---

## step1_extract.py — 音訊抽取

```python
"""
step1_extract.py
用途：從影片檔抽取音訊，壓縮至 Groq 25MB 限制以內
輸入：影片路徑（mp4/mkv/mov/avi/webm）或音檔（mp3/wav/m4a）
輸出：audio_temp.mp3（寫入 output 目錄）
"""

import os
import subprocess
import shutil
import sys

def extract_audio(input_path: str, output_dir: str, config: dict) -> str:
    """
    抽取音訊並壓縮。若輸入已是音檔，直接複製或轉換。
    回傳：audio_temp.mp3 的完整路徑
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "audio_temp.mp3")
    max_mb = config.get("max_file_size_mb", 24)

    # 檢查 ffmpeg
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg 未安裝，請先安裝：brew install ffmpeg / sudo apt install ffmpeg")

    ext = os.path.splitext(input_path)[1].lower()
    audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

    if ext in audio_exts:
        # 音檔：直接轉成 mp3（統一格式）
        cmd = ["ffmpeg", "-y", "-i", input_path,
               "-ar", "16000", "-ac", "1", "-b:a", "64k", out_path]
    else:
        # 影片：抽取音軌
        cmd = ["ffmpeg", "-y", "-i", input_path,
               "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k", out_path]

    print(f"[step1] 抽取音訊：{input_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 失敗：{result.stderr}")

    # 檢查大小
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    if size_mb > max_mb:
        print(f"[step1] 檔案 {size_mb:.1f}MB 超過 {max_mb}MB，進行二次壓縮...")
        tmp = out_path + ".tmp.mp3"
        bitrate = int(max_mb * 1024 * 8 / (size_mb / 0.064) * 0.9)
        bitrate = max(16, min(bitrate, 64))
        cmd2 = ["ffmpeg", "-y", "-i", out_path, "-b:a", f"{bitrate}k", tmp]
        subprocess.run(cmd2, check=True, capture_output=True)
        os.replace(tmp, out_path)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"[step1] 完成：{out_path}（{size_mb:.1f} MB）")
    return out_path
```

---

## step2_transcribe.py — Groq Whisper 語音辨識

```python
"""
step2_transcribe.py
用途：呼叫 Groq Whisper，取得 word-level 時間碼，切成字幕段，輸出原文 SRT
輸入：audio_temp.mp3
輸出：{filename}_en.srt（暫存於 output 目錄）
"""

import os
import re
from groq import Groq

def transcribe(audio_path: str, output_dir: str, config: dict) -> list[dict]:
    """
    回傳 segments 列表：
    [{"index": 1, "start": "00:00:01,200", "end": "00:00:03,450", "text": "Hello world"}, ...]
    """
    client = Groq(api_key=config["groq_api_key"])

    print(f"[step2] 上傳至 Groq Whisper...")
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model=config.get("whisper_model", "whisper-large-v3-turbo"),
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            language="en",
        )

    # 使用 segment-level 時間碼（比 word-level 更穩定）
    raw_segments = response.segments
    print(f"[step2] 辨識完成，共 {len(raw_segments)} 個原始段落")

    # 重新切段：控制長度與時間
    segments = _resegment(raw_segments, config)
    print(f"[step2] 切段完成，共 {len(segments)} 段")

    # 寫出暫存 SRT
    srt_path = os.path.join(output_dir, "_en_raw.srt")
    _write_srt(segments, srt_path)
    print(f"[step2] 原文 SRT 暫存：{srt_path}")
    return segments


def _resegment(raw_segments, config) -> list[dict]:
    """將 Whisper 的 segment 重新切分為適合字幕的長度"""
    min_sec = config.get("segment_min_sec", 1.0)
    max_sec = config.get("segment_max_sec", 5.0)
    max_chars = config.get("segment_max_chars", 80)

    result = []
    idx = 1

    for seg in raw_segments:
        text = seg.text.strip()
        duration = seg.end - seg.start

        if not text:
            continue

        # 太長就切分
        if duration > max_sec or len(text) > max_chars:
            words = text.split()
            chunk = []
            chunk_start = seg.start
            time_per_word = duration / max(len(words), 1)

            for i, word in enumerate(words):
                chunk.append(word)
                chunk_text = " ".join(chunk)
                chunk_duration = time_per_word * len(chunk)

                if (chunk_duration >= min_sec and len(chunk_text) >= 20) or \
                   len(chunk_text) > max_chars or i == len(words) - 1:
                    chunk_end = chunk_start + chunk_duration
                    result.append({
                        "index": idx,
                        "start": _sec_to_srt(chunk_start),
                        "end": _sec_to_srt(min(chunk_end, seg.end)),
                        "text": chunk_text
                    })
                    idx += 1
                    chunk_start = chunk_end
                    chunk = []
        else:
            result.append({
                "index": idx,
                "start": _sec_to_srt(seg.start),
                "end": _sec_to_srt(seg.end),
                "text": text
            })
            idx += 1

    return result


def _sec_to_srt(seconds: float) -> str:
    """將秒數轉換為 SRT 時間格式 HH:MM:SS,mmm"""
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_srt(segments: list[dict], path: str):
    """將 segments 寫成標準 SRT 格式"""
    lines = []
    for seg in segments:
        lines.append(str(seg["index"]))
        lines.append(f"{seg['start']} --> {seg['end']}")
        lines.append(seg["text"])
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
```

---

## step3_translate.py — Gemini 翻譯（嚴格時間碼保護）

```python
"""
step3_translate.py
用途：批次翻譯英文字幕為繁體中文，嚴格保留時間碼
輸入：segments 列表
輸出：zh_segments 列表（時間碼與原文完全一致，只有文字被替換）
"""

import time
import google.generativeai as genai
from .step4_validate import validate_translation

def translate(segments: list[dict], config: dict) -> list[dict]:
    """
    批次翻譯，失敗自動重試
    回傳：zh_segments（時間碼與 segments 完全相同，text 為繁體中文）
    """
    genai.configure(api_key=config["gemini_api_key"])
    model = genai.GenerativeModel("gemini-2.5-flash")

    batch_size = config.get("translation_batch_size", 30)
    max_retry = config.get("max_retry", 3)
    target_lang = config.get("target_language", "繁體中文")

    zh_segments = []
    total = len(segments)

    for batch_start in range(0, total, batch_size):
        batch = segments[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"[step3] 翻譯批次 {batch_num}/{total_batches}（段落 {batch_start+1}–{min(batch_start+batch_size, total)}）")

        translated_batch = None
        for attempt in range(1, max_retry + 1):
            try:
                translated_batch = _translate_batch(model, batch, target_lang)
                # 即時驗證（只驗證此批次）
                errors = validate_translation(batch, translated_batch)
                if not errors:
                    break
                print(f"[step3] 批次 {batch_num} 第 {attempt} 次驗證失敗：{errors[:2]}")
                if attempt < max_retry:
                    time.sleep(5)
            except Exception as e:
                print(f"[step3] 批次 {batch_num} 第 {attempt} 次異常：{e}")
                if attempt < max_retry:
                    time.sleep(10)

        if translated_batch is None or validate_translation(batch, translated_batch):
            # 最終失敗：保留原文並標記
            print(f"[step3] ⚠️ 批次 {batch_num} 翻譯失敗，保留原文")
            translated_batch = [
                {**seg, "text": f"[翻譯失敗] {seg['text']}"}
                for seg in batch
            ]

        zh_segments.extend(translated_batch)
        time.sleep(1)  # 避免 Rate Limit

    print(f"[step3] 翻譯完成，共 {len(zh_segments)} 段")
    return zh_segments


def _translate_batch(model, batch: list[dict], target_lang: str) -> list[dict]:
    """
    呼叫 Gemini 翻譯一個批次
    Prompt 強制要求：時間碼不動、段落一對一、只改文字
    """
    # 構建輸入（只傳文字，時間碼由程式自己對應）
    numbered_texts = "\n".join(
        f"{seg['index']}|{seg['text']}"
        for seg in batch
    )

    prompt = f"""你是專業字幕翻譯師，請將以下英文字幕逐行翻譯為{target_lang}。

嚴格規則（違反任何一條將導致翻譯被拒絕重新執行）：
1. 每行格式必須是「序號|譯文」，序號與原文完全相同，不得新增或刪除行
2. 輸入有幾行，輸出必須恰好有幾行
3. 只翻譯豎線後的文字，豎線前的序號原封不動
4. 翻譯為自然流暢的{target_lang}，符合口語字幕習慣
5. 不要加任何解釋、備註或額外內容

輸入（共 {len(batch)} 行）：
{numbered_texts}

輸出（必須恰好 {len(batch)} 行）："""

    response = model.generate_content(prompt)
    output_text = response.text.strip()

    # 解析回應
    result = []
    lines = [l.strip() for l in output_text.split("\n") if l.strip()]

    for seg, line in zip(batch, lines):
        if "|" in line:
            _, zh_text = line.split("|", 1)
        else:
            zh_text = line  # 容錯：沒有豎線就整行當譯文

        result.append({
            "index": seg["index"],
            "start": seg["start"],   # 時間碼完整複製，絕對不改
            "end": seg["end"],       # 時間碼完整複製，絕對不改
            "text": zh_text.strip()
        })

    return result
```

---

## step4_validate.py — 嚴格驗證器

```python
"""
step4_validate.py
用途：驗證翻譯結果，確保時間碼完全對齊、段數一致
"""

import re

TIMECODE_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}$")


def validate_translation(original: list[dict], translated: list[dict]) -> list[str]:
    """
    驗證翻譯結果。
    回傳錯誤列表，空列表表示驗證通過。
    """
    errors = []

    # 1. 段落總數
    if len(original) != len(translated):
        errors.append(
            f"段落數不符：原文 {len(original)} 段，譯文 {len(translated)} 段"
        )
        return errors  # 數量不對，後續比對無意義

    for i, (orig, trans) in enumerate(zip(original, translated)):
        n = i + 1

        # 2. 序號一致
        if orig["index"] != trans["index"]:
            errors.append(f"段落 {n}：序號不符（原文 {orig['index']}，譯文 {trans['index']}）")

        # 3. 時間碼完全相同
        if orig["start"] != trans["start"]:
            errors.append(f"段落 {n}：開始時間不符（{orig['start']} → {trans['start']}）")
        if orig["end"] != trans["end"]:
            errors.append(f"段落 {n}：結束時間不符（{orig['end']} → {trans['end']}）")

        # 4. 時間碼格式正確
        if not TIMECODE_PATTERN.match(trans["start"]):
            errors.append(f"段落 {n}：開始時間格式錯誤：{trans['start']}")
        if not TIMECODE_PATTERN.match(trans["end"]):
            errors.append(f"段落 {n}：結束時間格式錯誤：{trans['end']}")

        # 5. 譯文不為空
        if not trans["text"].strip():
            errors.append(f"段落 {n}：譯文為空")

    # 6. 時間連續性（全局）
    all_ok = not errors
    if all_ok:
        for i in range(len(translated) - 1):
            cur_end = _srt_to_ms(translated[i]["end"])
            nxt_start = _srt_to_ms(translated[i + 1]["start"])
            if cur_end > nxt_start + 100:  # 允許 100ms 誤差
                errors.append(
                    f"時間重疊：段落 {i+1} 結束 {translated[i]['end']} > "
                    f"段落 {i+2} 開始 {translated[i+1]['start']}"
                )

    return errors


def validate_srt_file(segments: list[dict]) -> list[str]:
    """驗證最終輸出的 SRT 完整性"""
    errors = []
    for i, seg in enumerate(segments):
        # 開始 < 結束
        start_ms = _srt_to_ms(seg["start"])
        end_ms = _srt_to_ms(seg["end"])
        if start_ms >= end_ms:
            errors.append(f"段落 {i+1}：開始時間 >= 結束時間")
    return errors


def _srt_to_ms(timecode: str) -> int:
    """SRT 時間碼轉毫秒"""
    try:
        h, m, rest = timecode.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    except Exception:
        return 0
```

---

## step5_export.py — 輸出最終 SRT 檔案

```python
"""
step5_export.py
用途：將 segments 輸出為標準 SRT 檔案
輸出：{stem}_en.srt 與 {stem}_zh.srt
"""

import os


def export(
    en_segments: list[dict],
    zh_segments: list[dict],
    input_path: str,
    output_dir: str,
) -> tuple[str, str]:
    """
    輸出原文和譯文 SRT 檔案。
    回傳：(en_srt_path, zh_srt_path)
    """
    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(input_path))[0]

    en_path = os.path.join(output_dir, f"{stem}_en.srt")
    zh_path = os.path.join(output_dir, f"{stem}_zh.srt")

    _write_srt(en_segments, en_path)
    _write_srt(zh_segments, zh_path)

    print(f"[step5] ✅ 原文字幕：{en_path}")
    print(f"[step5] ✅ 繁中字幕：{zh_path}")
    return en_path, zh_path


def _write_srt(segments: list[dict], path: str):
    """寫出標準 SRT 格式"""
    lines = []
    for seg in segments:
        lines.append(str(seg["index"]))
        lines.append(f"{seg['start']} --> {seg['end']}")
        lines.append(seg["text"])
        lines.append("")  # 段落間空行

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    
    print(f"[step5] 寫出 {path}（{len(segments)} 段）")
```

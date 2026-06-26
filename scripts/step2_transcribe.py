"""
step2_transcribe.py - Groq Whisper 語音辨識，產生原文 SRT
"""

import os
from groq import Groq


def transcribe(audio_path: str, output_dir: str, config: dict) -> list[dict]:
    """
    語音辨識 + 切段。
    回傳：segments 列表
    """
    client = Groq(api_key=config["groq_api_key"])

    print(f"[step2] 上傳音訊至 Groq Whisper...")
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model=config.get("whisper_model", "whisper-large-v3-turbo"),
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="en",
        )

    raw_segments = response.segments
    print(f"[step2] 辨識完成，{len(raw_segments)} 個原始段落")

    segments = _resegment(raw_segments, config)
    print(f"[step2] 切段完成，共 {len(segments)} 段")

    # 寫出暫存 SRT（供除錯或指定步驟使用）
    raw_srt_path = os.path.join(output_dir, "_en_raw.srt")
    _write_srt(segments, raw_srt_path)

    return segments


def _resegment(raw_segments, config) -> list[dict]:
    """重新切分為適合字幕的長度"""
    min_sec = config.get("segment_min_sec", 1.0)
    max_sec = config.get("segment_max_sec", 5.0)
    max_chars = config.get("segment_max_chars", 80)

    result = []
    idx = 1

    for seg in raw_segments:
        text = seg['text'].strip()
        duration = seg['end'] - seg['start']

        if not text:
            continue

        # 太長需要切分
        if duration > max_sec or len(text) > max_chars:
            words = text.split()
            if not words:
                continue

            chunk = []
            chunk_start = seg['start']
            time_per_word = duration / len(words)

            for i, word in enumerate(words):
                chunk.append(word)
                chunk_text = " ".join(chunk)
                chunk_duration = time_per_word * len(chunk)

                should_flush = (
                    (chunk_duration >= min_sec and len(chunk_text) >= 20) or
                    len(chunk_text) > max_chars or
                    i == len(words) - 1
                )

                if should_flush and chunk:
                    chunk_end = min(chunk_start + chunk_duration, seg['end'])
                    result.append({
                        "index": idx,
                        "start": _sec_to_srt(chunk_start),
                        "end": _sec_to_srt(chunk_end),
                        "text": chunk_text,
                    })
                    idx += 1
                    chunk_start = chunk_end
                    chunk = []
        else:
            result.append({
                "index": idx,
                "start": _sec_to_srt(seg['start']),
                "end": _sec_to_srt(seg['end']),
                "text": text,
            })
            idx += 1

    return result


def _sec_to_srt(seconds: float) -> str:
    """秒數 → SRT 時間碼 HH:MM:SS,mmm"""
    ms = int(round(max(0.0, seconds) * 1000))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1_000
    ms %= 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_srt(segments: list[dict], path: str):
    lines = []
    for seg in segments:
        lines.extend([
            str(seg["index"]),
            f"{seg['start']} --> {seg['end']}",
            seg["text"],
            "",
        ])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

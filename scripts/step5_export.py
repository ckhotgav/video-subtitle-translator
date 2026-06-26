"""
step5_export.py - 輸出最終 SRT 檔案
"""

import os


def export(
    en_segments: list[dict],
    zh_segments: list[dict],
    input_path: str,
    output_dir: str,
) -> tuple[str, str]:
    """
    輸出原文和譯文 SRT 到 output_dir。
    回傳 (en_srt_path, zh_srt_path)。
    """
    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(input_path))[0]

    en_path = os.path.join(output_dir, f"{stem}_en.srt")
    zh_path = os.path.join(output_dir, f"{stem}_zh.srt")

    _write_srt(en_segments, en_path)
    _write_srt(zh_segments, zh_path)

    print(f"[step5] ✅ 原文字幕：{en_path}（{len(en_segments)} 段）")
    print(f"[step5] ✅ 繁中字幕：{zh_path}（{len(zh_segments)} 段）")
    return en_path, zh_path


def _write_srt(segments: list[dict], path: str):
    """寫出標準 SRT 格式，UTF-8，LF 換行"""
    lines = []
    for seg in segments:
        lines.append(str(seg["index"]))
        lines.append(f"{seg['start']} --> {seg['end']}")
        lines.append(seg["text"])
        lines.append("")  # 段落間空行

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

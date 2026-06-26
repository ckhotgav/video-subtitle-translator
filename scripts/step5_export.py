"""
step5_export.py - 輸出最終 SRT 檔案
"""

import os


def export(
    en_segments: list[dict],
    zh_segments: list[dict],
    input_path: str,
    output_dir: str,
    config: dict,
) -> tuple[str, str]:
    """
    輸出原文和譯文 SRT 到 output_dir。
    回傳 (source_srt_path, target_srt_path)。
    """
    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(input_path))[0]

    source_lang = config.get("source_language", "auto")
    target_lang = config.get("target_language", "繁體中文")

    def get_suffix(lang_str):
        lang_str = lang_str.lower()
        if "繁體中文" in lang_str or "zh" in lang_str or "中文" in lang_str:
            return "zh"
        elif "ja" in lang_str or "日" in lang_str:
            return "ja"
        elif "en" in lang_str or "英" in lang_str:
            return "en"
        return lang_str[:3]

    src_suffix = get_suffix(source_lang)
    tgt_suffix = get_suffix(target_lang)

    source_path = os.path.join(output_dir, f"{stem}_{src_suffix}.srt")
    target_path = os.path.join(output_dir, f"{stem}_{tgt_suffix}.srt")

    _write_srt(en_segments, source_path)
    _write_srt(zh_segments, target_path)

    print(f"[step5] ✅ 原文字幕：{source_path}（{len(en_segments)} 段）")
    print(f"[step5] ✅ 譯文字幕：{target_path}（{len(zh_segments)} 段）")
    return source_path, target_path


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

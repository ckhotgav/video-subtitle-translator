"""
step4_validate.py - 嚴格驗證翻譯結果：段數、時間碼、連續性
"""

import re

TIMECODE_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}$")


def validate_translation(original: list[dict], translated: list[dict]) -> list[str]:
    """
    驗證翻譯結果與原文的對應。
    回傳錯誤列表；空列表 = 通過。
    """
    errors = []

    # 1. 段落總數必須相同
    if len(original) != len(translated):
        errors.append(
            f"段落數不符：原文 {len(original)} 段，譯文 {len(translated)} 段"
        )
        return errors  # 數量錯誤時後續比對無意義

    for i, (orig, trans) in enumerate(zip(original, translated)):
        n = i + 1

        # 2. 序號一致
        if str(orig["index"]) != str(trans["index"]):
            errors.append(
                f"段落 {n}：序號不符（原 {orig['index']}，譯 {trans['index']}）"
            )

        # 3. 時間碼完全相同（逐字元比對）
        if orig["start"] != trans["start"]:
            errors.append(
                f"段落 {n}：開始時間被修改（{orig['start']} → {trans['start']}）"
            )
        if orig["end"] != trans["end"]:
            errors.append(
                f"段落 {n}：結束時間被修改（{orig['end']} → {trans['end']}）"
            )

        # 4. 時間碼格式正確
        if not TIMECODE_PATTERN.match(trans.get("start", "")):
            errors.append(f"段落 {n}：開始時間格式錯誤：'{trans.get('start')}'")
        if not TIMECODE_PATTERN.match(trans.get("end", "")):
            errors.append(f"段落 {n}：結束時間格式錯誤：'{trans.get('end')}'")

        # 5. 譯文不為空
        if not trans.get("text", "").strip():
            errors.append(f"段落 {n}：譯文為空")

    # 6. 時間連續性（若前面沒有時間碼錯誤才檢查）
    if not errors:
        for i in range(len(translated) - 1):
            cur_end = _srt_to_ms(translated[i]["end"])
            nxt_start = _srt_to_ms(translated[i + 1]["start"])
            # 允許 200ms 誤差（Whisper 時間碼本身有浮點誤差）
            if cur_end > nxt_start + 200:
                errors.append(
                    f"時間重疊：段落 {i+1} 結束 {translated[i]['end']} > "
                    f"段落 {i+2} 開始 {translated[i+1]['start']}"
                )

    return errors


def validate_srt_file(segments: list[dict]) -> list[str]:
    """驗證最終 SRT 的完整性（開始 < 結束）"""
    errors = []
    for i, seg in enumerate(segments):
        start_ms = _srt_to_ms(seg.get("start", ""))
        end_ms = _srt_to_ms(seg.get("end", ""))
        if start_ms >= end_ms:
            errors.append(
                f"段落 {i+1}：開始時間 {seg['start']} >= 結束時間 {seg['end']}"
            )
    return errors


def _srt_to_ms(timecode: str) -> int:
    """SRT 時間碼轉毫秒"""
    try:
        h, m, rest = timecode.split(":")
        s, ms = rest.split(",")
        return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)
    except Exception:
        return 0

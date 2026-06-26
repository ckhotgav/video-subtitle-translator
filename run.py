#!/usr/bin/env python3
"""
run.py - Video Subtitle Translator 主入口
用法：python run.py <影片或音檔路徑> [選項]
"""

import argparse
import os
import sys
import shutil
sys.stdout.reconfigure(encoding='utf-8')
import yaml

# 確保 scripts 模組可被 import
sys.path.insert(0, os.path.dirname(__file__))

from scripts.step1_extract import extract_audio
from scripts.step2_transcribe import transcribe
from scripts.step3_translate import translate
from scripts.step4_validate import validate_translation, validate_srt_file
from scripts.step5_export import export


def check_dependencies():
    ffmpeg_exists = shutil.which("ffmpeg") or os.path.exists("ffmpeg.exe") or os.path.exists("ffmpeg")
    ffprobe_exists = shutil.which("ffprobe") or os.path.exists("ffprobe.exe") or os.path.exists("ffprobe")
    if not ffmpeg_exists or not ffprobe_exists:
        print("=" * 50)
        print("⚠️  錯誤：找不到 ffmpeg 或 ffprobe！")
        print("本專案需要 ffmpeg 進行影片/音訊抽取與壓縮，以及 ffprobe 取得音訊長度。")
        print("請嘗試以下方式安裝：")
        print("  - macOS:  brew install ffmpeg")
        print("  - Ubuntu: sudo apt install ffmpeg")
        print("  - Windows:")
        print("    1. 前往 https://ffmpeg.org/download.html 下載 Windows 執行檔")
        print("    2. 解壓縮並將 bin 目錄（包含 ffmpeg.exe, ffprobe.exe）路徑加入系統 PATH 環境變數")
        print("    3. 或者，將 ffmpeg.exe 與 ffprobe.exe 複製放入專案根目錄下")
        print("=" * 50)
        sys.exit(1)


def load_config(config_path: str = "config.yaml") -> dict:
    if not os.path.exists(config_path):
        print(f"❌ 找不到設定檔：{config_path}")
        print("請複製 config.yaml.example 並填入 API 金鑰")
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    check_dependencies()
    parser = argparse.ArgumentParser(

        description="Video Subtitle Translator：英文影片 → 繁體中文字幕"
    )
    parser.add_argument("input", help="影片或音檔路徑")
    parser.add_argument("--output", default="output", help="輸出目錄（預設：./output）")
    parser.add_argument("--config", default="config.yaml", help="設定檔路徑")
    parser.add_argument("--step", type=int, help="只執行指定步驟（1-5，除錯用）")
    parser.add_argument("--verbose", action="store_true", help="顯示詳細 log")
    args = parser.parse_args()

    # 載入設定
    config = load_config(args.config)

    input_path = args.input
    output_dir = args.output

    if not os.path.exists(input_path):
        print(f"❌ 找不到輸入檔案：{input_path}")
        sys.exit(1)

    print("=" * 50)
    print("🎬 Video Subtitle Translator")
    print(f"   輸入：{input_path}")
    print(f"   輸出：{output_dir}/")
    print("=" * 50)

    # ── Step 1：抽取音訊 ──────────────────────────────
    if args.step is None or args.step == 1:
        audio_path = extract_audio(input_path, output_dir, config)
    else:
        audio_path = os.path.join(output_dir, "audio_temp.mp3")

    # ── Step 2：語音辨識 ──────────────────────────────
    if args.step is None or args.step == 2:
        en_segments = transcribe(audio_path, output_dir, config)
    else:
        # 從暫存 SRT 讀取（若指定單步）
        en_segments = _load_srt(os.path.join(output_dir, "_en_raw.srt"))

    # ── Step 3：翻譯 ──────────────────────────────────
    if args.step is None or args.step == 3:
        zh_segments = translate(en_segments, config)
    else:
        zh_segments = _load_srt(os.path.join(output_dir, "_zh_raw.srt"))

    # ── Step 4：最終驗證 ──────────────────────────────
    if args.step is None or args.step == 4:
        errors = validate_translation(en_segments, zh_segments)
        if errors:
            print(f"⚠️  最終驗證發現 {len(errors)} 個問題：")
            for e in errors[:5]:
                print(f"   - {e}")
            print("   （已保留原文的段落標記為 [翻譯失敗]）")
        else:
            print("[step4] ✅ 驗證通過：時間碼完全對齊，段落數一致")

        srt_errors = validate_srt_file(zh_segments)
        if srt_errors:
            print(f"⚠️  SRT 完整性問題：{srt_errors[:3]}")

    # ── Step 5：輸出 ──────────────────────────────────
    if args.step is None or args.step == 5:
        en_path, zh_path = export(en_segments, zh_segments, input_path, output_dir)

        print()
        print("=" * 50)
        print("🎉 完成！")
        print(f"   📄 原文字幕：{en_path}")
        print(f"   🇹🇼 繁中字幕：{zh_path}")
        print("=" * 50)


def _load_srt(path: str) -> list[dict]:
    """從 SRT 檔案讀取 segments（除錯用）"""
    if not os.path.exists(path):
        print(f"❌ 找不到暫存 SRT：{path}，請先執行前置步驟")
        sys.exit(1)

    segments = []
    with open(path, encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                times = lines[1].split(" --> ")
                text = "\n".join(lines[2:])
                segments.append({
                    "index": index,
                    "start": times[0].strip(),
                    "end": times[1].strip(),
                    "text": text
                })
            except (ValueError, IndexError):
                pass

    return segments


if __name__ == "__main__":
    main()

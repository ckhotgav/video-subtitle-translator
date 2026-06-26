"""
step1_extract.py - 從影片抽取音訊，壓縮至 Groq 限制以內
"""

import os
import subprocess
import shutil
import sys


def extract_audio(input_path: str, output_dir: str, config: dict) -> str:
    """
    抽取並壓縮音訊。
    回傳：output_dir/audio_temp.mp3 路徑
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "audio_temp.mp3")
    max_mb = config.get("max_file_size_mb", 24)

    ffmpeg_cmd = "ffmpeg"
    if not shutil.which("ffmpeg"):
        if os.path.exists("ffmpeg.exe"):
            ffmpeg_cmd = "ffmpeg.exe"
        elif os.path.exists("ffmpeg"):
            ffmpeg_cmd = "./ffmpeg"
        else:
            raise RuntimeError(
                "ffmpeg 未安裝！\n"
                "  macOS:  brew install ffmpeg\n"
                "  Ubuntu: sudo apt install ffmpeg\n"
                "  Windows: https://ffmpeg.org/download.html"
            )

    ext = os.path.splitext(input_path)[1].lower()
    audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

    if ext in audio_exts:
        print(f"[step1] 音檔格式，直接轉換：{input_path}")
        cmd = [ffmpeg_cmd, "-y", "-i", input_path,
               "-ar", "16000", "-ac", "1", "-b:a", "64k", out_path]
    else:
        print(f"[step1] 影片格式，抽取音軌：{input_path}")
        cmd = [ffmpeg_cmd, "-y", "-i", input_path,
               "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k", out_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 失敗：\n{result.stderr[-500:]}")

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"[step1] 音訊大小：{size_mb:.1f} MB")

    if size_mb > max_mb:
        print(f"[step1] 超過 {max_mb}MB，進行二次壓縮...")
        # 計算目標 bitrate
        duration_sec = _get_duration(out_path)
        target_bitrate = max(16, int(max_mb * 8 * 1024 / duration_sec * 0.9))
        target_bitrate = min(target_bitrate, 48)

        tmp = out_path + ".tmp.mp3"
        cmd2 = ["ffmpeg", "-y", "-i", out_path,
                "-ar", "16000", "-ac", "1",
                "-b:a", f"{target_bitrate}k", tmp]
        subprocess.run(cmd2, check=True, capture_output=True)
        os.replace(tmp, out_path)

        new_size = os.path.getsize(out_path) / (1024 * 1024)
        print(f"[step1] 壓縮後：{new_size:.1f} MB（bitrate: {target_bitrate}k）")

    print(f"[step1] ✅ 音訊就緒：{out_path}")
    return out_path


def _get_duration(path: str) -> float:
    """用 ffprobe 取得音訊時長（秒）"""
    ffprobe_cmd = "ffprobe"
    if not shutil.which("ffprobe"):
        if os.path.exists("ffprobe.exe"):
            ffprobe_cmd = "ffprobe.exe"
        elif os.path.exists("ffprobe"):
            ffprobe_cmd = "./ffprobe"

    result = subprocess.run(
        [ffprobe_cmd, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 3600.0  # 預設 1 小時（保守估計）

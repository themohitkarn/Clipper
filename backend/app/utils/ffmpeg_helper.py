import os
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

_FFMPEG_PATH: Optional[str] = None
_FFPROBE_PATH: Optional[str] = None

def find_system_ffmpeg() -> Tuple[Optional[str], Optional[str]]:
    """Search for ffmpeg and ffprobe on system path or standard directories."""
    # 1. Check PATH
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg:
        return ffmpeg, ffprobe or ffmpeg.replace("ffmpeg", "ffprobe")

    # 2. Check local bin directory in project
    local_bin = Path(__file__).resolve().parent.parent.parent / "bin"
    if (local_bin / "ffmpeg.exe").exists():
        ffmpeg = str(local_bin / "ffmpeg.exe")
        ffprobe = str(local_bin / "ffprobe.exe") if (local_bin / "ffprobe.exe").exists() else None
        return ffmpeg, ffprobe

    # 3. Check AppData WinGet Gyan.FFmpeg or common package locations
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        winget_path = Path(appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_path.exists():
            for p in winget_path.glob("**/ffmpeg.exe"):
                ffmpeg = str(p)
                probe_cand = p.parent / "ffprobe.exe"
                ffprobe = str(probe_cand) if probe_cand.exists() else None
                return ffmpeg, ffprobe

    # 4. Check imageio_ffmpeg if installed
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg and os.path.exists(ffmpeg):
            return ffmpeg, None
    except Exception:
        pass

    # 5. Check common program files
    common_paths = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    ]
    for cp in common_paths:
        if os.path.exists(cp):
            probe_p = cp.replace("ffmpeg.exe", "ffprobe.exe")
            return cp, probe_p if os.path.exists(probe_p) else None

    return None, None

def get_ffmpeg_path() -> str:
    global _FFMPEG_PATH, _FFPROBE_PATH
    if not _FFMPEG_PATH:
        _FFMPEG_PATH, _FFPROBE_PATH = find_system_ffmpeg()
    if not _FFMPEG_PATH:
        raise RuntimeError("FFmpeg executable not found. Please install FFmpeg or place ffmpeg.exe in the 'bin/' folder.")
    return _FFMPEG_PATH

def get_ffprobe_path() -> Optional[str]:
    global _FFMPEG_PATH, _FFPROBE_PATH
    if not _FFPROBE_PATH:
        _FFMPEG_PATH, _FFPROBE_PATH = find_system_ffmpeg()
    return _FFPROBE_PATH

def run_ffmpeg(args: list[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)

def get_media_info(file_path: str) -> Dict[str, Any]:
    """Inspect duration, dimensions, and bitrate via ffprobe or ffmpeg fallback."""
    ffprobe_exe = get_ffprobe_path()
    if ffprobe_exe and os.path.exists(ffprobe_exe):
        try:
            cmd = [
                ffprobe_exe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0))
            
            width, height = 1920, 1080
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = int(stream.get("width", 1920))
                    height = int(stream.get("height", 1080))
                    break
            return {"duration": duration, "width": width, "height": height}
        except Exception:
            pass

    # Fallback using ffmpeg -i
    try:
        ffmpeg_exe = get_ffmpeg_path()
        res = subprocess.run([ffmpeg_exe, "-i", file_path], capture_output=True, text=True)
        out = res.stderr
        import re
        duration = 0.0
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", out)
        if dur_match:
            h, m, s = dur_match.groups()
            duration = int(h) * 3600 + int(m) * 60 + float(s)

        width, height = 1920, 1080
        dim_match = re.search(r"Video:.*?(\d{3,4})x(\d{3,4})", out)
        if dim_match:
            width = int(dim_match.group(1))
            height = int(dim_match.group(2))

        return {"duration": duration, "width": width, "height": height}
    except Exception:
        return {"duration": 0.0, "width": 1920, "height": 1080}

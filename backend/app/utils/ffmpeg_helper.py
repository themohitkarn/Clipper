import os
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

_FFMPEG_PATH: Optional[str] = None
_FFPROBE_PATH: Optional[str] = None

def _verify_executable(path: Optional[str]) -> bool:
    """Verify that a binary can actually be invoked without being blocked by OS policies."""
    if not path or not os.path.exists(path):
        return False
    try:
        res = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False

def find_system_ffmpeg() -> Tuple[Optional[str], Optional[str]]:
    """Search for working ffmpeg and ffprobe on system path or standard directories."""
    candidates = []

    # 1. Check local bin directory in project root
    project_bin = Path(__file__).resolve().parent.parent.parent.parent / "bin"
    if (project_bin / "ffmpeg.exe").exists():
        candidates.append((str(project_bin / "ffmpeg.exe"), str(project_bin / "ffprobe.exe")))

    backend_bin = Path(__file__).resolve().parent.parent.parent / "bin"
    if (backend_bin / "ffmpeg.exe").exists():
        candidates.append((str(backend_bin / "ffmpeg.exe"), str(backend_bin / "ffprobe.exe")))

    # 2. Check imageio_ffmpeg
    try:
        import imageio_ffmpeg
        img_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if img_exe and os.path.exists(img_exe):
            candidates.append((img_exe, None))
    except Exception:
        pass

    # 3. Check PATH
    path_ffmpeg = shutil.which("ffmpeg")
    path_ffprobe = shutil.which("ffprobe")
    if path_ffmpeg:
        candidates.append((path_ffmpeg, path_ffprobe))

    # 4. Check common program files
    common_paths = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    ]
    for cp in common_paths:
        if os.path.exists(cp):
            probe_p = cp.replace("ffmpeg.exe", "ffprobe.exe")
            candidates.append((cp, probe_p if os.path.exists(probe_p) else None))

    # Test each candidate for execution permission
    for ffmpeg_cand, probe_cand in candidates:
        if _verify_executable(ffmpeg_cand):
            valid_probe = probe_cand if _verify_executable(probe_cand) else None
            return ffmpeg_cand, valid_probe

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

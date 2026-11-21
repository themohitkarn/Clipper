import os
import re
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from ..config import TEMP_DIR
from ..utils.ffmpeg_helper import get_ffmpeg_path

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or TEMP_DIR

    def _get_ytdlp_cmd(self) -> list[str]:
        """Find yt-dlp executable: local bin, virtualenv, or system PATH."""
        # Check project bin
        bin_exe = Path(__file__).resolve().parent.parent.parent.parent / "bin" / "yt-dlp.exe"
        if bin_exe.exists():
            return [str(bin_exe)]

        # Check venv
        venv_py = Path(__file__).resolve().parent.parent.parent.parent / ".venv" / "Scripts" / "python.exe"
        if venv_py.exists():
            # Check if yt_dlp module is available
            return [str(venv_py), "-m", "yt_dlp"]

        # Check system yt-dlp
        system_ytdlp = shutil.which("yt-dlp")
        if system_ytdlp:
            return [system_ytdlp]

        return ["python", "-m", "yt_dlp"]

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Fetch video metadata quickly without downloading the media payload."""
        cmd = self._get_ytdlp_cmd() + [
            "--dump-json",
            "--no-playlist",
            "--skip-download",
            "--no-warnings",
            url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8", errors="replace")
            info = json.loads(res.stdout)
            return {
                "id": info.get("id"),
                "title": info.get("title", "Untitled Video"),
                "duration": float(info.get("duration", 0.0)),
                "channel": info.get("uploader") or info.get("channel", "Unknown Channel"),
                "thumbnail": info.get("thumbnail") or (info.get("thumbnails", [{}])[-1].get("url") if info.get("thumbnails") else ""),
                "description": info.get("description", "")[:500],
                "url": url
            }
        except Exception as e:
            logger.warning(f"yt-dlp extract_info failed: {e}. Attempting fallback metadata extraction.")
            # Basic fallback for YouTube URL ID
            video_id = self.extract_youtube_id(url)
            return {
                "id": video_id or "unknown",
                "title": f"YouTube Video ({video_id})" if video_id else "Uploaded Video",
                "duration": 0.0,
                "channel": "YouTube",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else "",
                "description": "",
                "url": url
            }

    @staticmethod
    def extract_youtube_id(url: str) -> Optional[str]:
        """Extract 11-character YouTube video ID from various URL formats."""
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"youtu\.be\/([0-9A-Za-z_-]{11})",
            r"shorts\/([0-9A-Za-z_-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def download_section(
        self,
        url: str,
        start_seconds: float,
        end_seconds: float,
        output_path: Path
    ) -> bool:
        """
        Download ONLY the specified time window of the video.
        Essential for 24-hour / multi-hour videos so we don't download tens of gigabytes!
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_exe = get_ffmpeg_path()
        ffmpeg_dir = str(Path(ffmpeg_exe).parent)

        # Format start and end as HH:MM:SS
        def fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        time_range = f"*{fmt_time(start_seconds)}-{fmt_time(end_seconds)}"
        
        cmd = self._get_ytdlp_cmd() + [
            "--download-sections", time_range,
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--ffmpeg-location", ffmpeg_dir,
            "-o", str(output_path),
            "--force-overwrites",
            "--no-playlist",
            url
        ]

        logger.info(f"Downloading clip section {time_range} from {url}...")
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        if output_path.exists() and output_path.stat().st_size > 1000:
            return True
            
        # If specific section download fails, try downloading with direct ffmpeg stream seek
        return self._download_with_ffmpeg_stream(url, start_seconds, end_seconds, output_path)

    def _download_with_ffmpeg_stream(
        self,
        url: str,
        start_seconds: float,
        end_seconds: float,
        output_path: Path
    ) -> bool:
        """Fallback: Get direct media stream URL from yt-dlp and slice with ffmpeg."""
        try:
            cmd = self._get_ytdlp_cmd() + [
                "-g",
                "-f", "best[ext=mp4]/best",
                url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            stream_url = res.stdout.strip().split("\n")[0]
            if not stream_url:
                return False

            duration = end_seconds - start_seconds
            ffmpeg_exe = get_ffmpeg_path()
            ffmpeg_cmd = [
                ffmpeg_exe, "-y",
                "-ss", str(start_seconds),
                "-i", stream_url,
                "-t", str(duration),
                "-c:v", "libx264", "-c:a", "aac",
                "-preset", "veryfast",
                str(output_path)
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=180, check=True)
            return output_path.exists() and output_path.stat().st_size > 1000
        except Exception as e:
            logger.error(f"Stream slicing failed: {e}")
            return False

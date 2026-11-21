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
        """Find yt-dlp executable: virtualenv python module, system PATH, or local bin."""
        import sys
        base_cmd = ["python", "-m", "yt_dlp"]
        # 1. First priority: current python environment running yt_dlp module
        try:
            import yt_dlp
            base_cmd = [sys.executable, "-m", "yt_dlp"]
        except ImportError:
            # 2. Check virtualenv python
            venv_py = Path(__file__).resolve().parent.parent.parent.parent / ".venv" / "Scripts" / "python.exe"
            if venv_py.exists():
                base_cmd = [str(venv_py), "-m", "yt_dlp"]
            else:
                # 3. Check system yt-dlp
                system_ytdlp = shutil.which("yt-dlp")
                if system_ytdlp:
                    base_cmd = [system_ytdlp]
                else:
                    # 4. Check project bin
                    bin_exe = Path(__file__).resolve().parent.parent.parent.parent / "bin" / "yt-dlp.exe"
                    if bin_exe.exists():
                        base_cmd = [str(bin_exe)]

        # Add node JS runtime if available to solve YouTube JS challenges
        if shutil.which("node"):
            base_cmd.extend(["--js-runtimes", "node"])

        # Check for cookies.txt in root to bypass YouTube bot blocks automatically
        cookies_txt = Path(__file__).resolve().parent.parent.parent.parent / "cookies.txt"
        if cookies_txt.exists():
            base_cmd.extend(["--cookies", str(cookies_txt)])

        return base_cmd

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Fetch video metadata quickly without downloading the media payload."""
        local_path = Path(url)
        if local_path.exists() and local_path.is_file():
            from ..utils.ffmpeg_helper import get_media_info
            media_info = get_media_info(url)
            duration = media_info.get("duration", 0.0) if media_info else 0.0
            return {
                "id": local_path.stem,
                "title": local_path.name,
                "duration": duration,
                "channel": "Local Upload",
                "thumbnail": "",
                "description": "Uploaded video file",
                "url": url
            }

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

        # If url is a local file on disk, slice directly via FFmpeg without invoking yt-dlp
        local_path = Path(url)
        if local_path.exists() and local_path.is_file():
            duration = end_seconds - start_seconds
            cmd = [
                ffmpeg_exe, "-y",
                "-ss", str(start_seconds),
                "-i", str(local_path),
                "-t", str(duration),
                "-c:v", "libx264", "-c:a", "aac",
                "-preset", "veryfast",
                str(output_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return output_path.exists() and output_path.stat().st_size > 1000

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
            "-f", "bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "--merge-output-format", "mp4",
            "--downloader-args", "ffmpeg:-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 4",
            "--ffmpeg-location", ffmpeg_dir,
            "-o", str(output_path),
            "--force-overwrites",
            "--no-playlist",
            url
        ]

        logger.info(f"Downloading clip section {time_range} from {url}...")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        except subprocess.TimeoutExpired:
            logger.warning(f"Section download timed out for {time_range}. Trying fast resolution fallback.")
        
        if output_path.exists() and output_path.stat().st_size > 1000:
            return True

        # Fallback 1: Download with 480p/360p (fast payload, finishes in seconds)
        logger.info(f"Trying fast 480p fallback for {time_range}...")
        cmd_fallback = self._get_ytdlp_cmd() + [
            "--download-sections", time_range,
            "-f", "bestvideo[height<=480]+bestaudio/best[height<=480]/best[height<=360]/best",
            "--merge-output-format", "mp4",
            "--downloader-args", "ffmpeg:-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 4",
            "--ffmpeg-location", ffmpeg_dir,
            "-o", str(output_path),
            "--force-overwrites",
            "--no-playlist",
            url
        ]
        try:
            subprocess.run(cmd_fallback, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        except Exception as e:
            logger.warning(f"Fast fallback failed: {e}")

        if output_path.exists() and output_path.stat().st_size > 1000:
            return True
            
        # Fallback 2: Stream slicing via direct ffmpeg seek
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
                "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            urls = [u.strip() for u in res.stdout.strip().split("\n") if u.strip().startswith("http")]
            if not urls:
                return False

            duration = end_seconds - start_seconds
            ffmpeg_exe = get_ffmpeg_path()
            if len(urls) >= 2:
                ffmpeg_cmd = [
                    ffmpeg_exe, "-y",
                    "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "4",
                    "-ss", str(start_seconds),
                    "-i", urls[0],
                    "-ss", str(start_seconds),
                    "-i", urls[1],
                    "-t", str(duration),
                    "-c:v", "libx264", "-c:a", "aac",
                    "-preset", "veryfast",
                    str(output_path)
                ]
            else:
                ffmpeg_cmd = [
                    ffmpeg_exe, "-y",
                    "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "4",
                    "-ss", str(start_seconds),
                    "-i", urls[0],
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

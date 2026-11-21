import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from ..utils.ffmpeg_helper import get_ffmpeg_path, get_media_info

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        pass

    def process_clip(
        self,
        input_video_path: Path,
        output_clip_path: Path,
        aspect_ratio: str = "9:16",
        subtitle_ass_path: Optional[Path] = None,
        subtitle_srt_path: Optional[Path] = None,
        thumbnail_output_path: Optional[Path] = None
    ) -> bool:
        """
        Process a clipped video section:
        1. Reframe to aspect ratio (9:16 vertical blurred, 1:1, or 16:9)
        2. Burn animated subtitles if provided
        3. Export high quality web-optimized MP4
        """
        output_clip_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_exe = get_ffmpeg_path()

        # Build FFmpeg video filter chain
        vf_filters = []

        if aspect_ratio == "9:16":
            # Professional podcast/TikTok look:
            # Blurred zoomed background (1080x1920) + Sharp centered video overlay
            filter_complex = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,gblur=sigma=20[bg];"
                "[0:v]scale=1080:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
            )
        elif aspect_ratio == "1:1":
            filter_complex = (
                "[0:v]scale=1080:1080:force_original_aspect_ratio=increase,"
                "crop=1080:1080[base]"
            )
        else:  # 16:9 or default
            filter_complex = "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[base]"

        # Subtitle burning
        current_stream = "[base]"
        sub_filter = ""
        if subtitle_ass_path and subtitle_ass_path.exists():
            # Escape path for FFmpeg filter on Windows
            clean_ass = str(subtitle_ass_path).replace("\\", "/").replace(":", "\\:")
            sub_filter = f";{current_stream}ass='{clean_ass}'[outv]"
            final_map = "[outv]"
        elif subtitle_srt_path and subtitle_srt_path.exists():
            clean_srt = str(subtitle_srt_path).replace("\\", "/").replace(":", "\\:")
            sub_filter = f";{current_stream}subtitles='{clean_srt}':force_style='FontSize=24,PrimaryColour=&H0000FFFF,Bold=1'[outv]"
            final_map = "[outv]"
        else:
            final_map = "[base]"

        full_filter = filter_complex + sub_filter

        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(input_video_path),
            "-filter_complex", full_filter,
            "-map", final_map,
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_clip_path)
        ]

        logger.info(f"Rendering clip to {aspect_ratio}: {output_clip_path.name}")
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Complex filter failed: {e.stderr[:300]}. Attempting simple crop fallback.")
            self._render_simple_crop(input_video_path, output_clip_path, aspect_ratio)

        # Generate thumbnail
        if thumbnail_output_path and output_clip_path.exists():
            self.generate_thumbnail(output_clip_path, thumbnail_output_path)

        return output_clip_path.exists() and output_clip_path.stat().st_size > 1000

    def _render_simple_crop(
        self,
        input_path: Path,
        output_path: Path,
        aspect_ratio: str
    ):
        """Simple center-crop fallback if complex background blur fails."""
        ffmpeg_exe = get_ffmpeg_path()
        if aspect_ratio == "9:16":
            vf = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920"
        elif aspect_ratio == "1:1":
            vf = "crop=min(iw\\,ih):min(iw\\,ih),scale=1080:1080"
        else:
            vf = "scale=1920:1080"

        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(input_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "faster",
            "-c:a", "aac",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=180)

    def generate_thumbnail(self, video_path: Path, thumb_path: Path, at_seconds: float = 1.5):
        """Extract a crisp preview frame for the clip card."""
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_exe = get_ffmpeg_path()
        cmd = [
            ffmpeg_exe, "-y",
            "-ss", str(at_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path)
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except Exception:
            pass

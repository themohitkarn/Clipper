from __future__ import annotations
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ....utils.ffmpeg_helper import get_ffmpeg_path

logger = logging.getLogger(__name__)

Tuple_Filters = tuple[str, str]

class SmartReframe:
    """
    Intelligent Gaming Video Reframer.
    Supports Facecam-aware Split-Screen (Facecam Top + Gameplay Bottom),
    Dual-layer Blurred Background, 1:1 Square, and 16:9 Landscape.
    """
    def __init__(self):
        pass

    def build_filter_graph(
        self,
        aspect_ratio: str,
        facecam_info: Optional[Dict[str, Any]] = None,
        facecam_layout_mode: str = "auto",
        subtitle_filter: str = ""
    ) -> Tuple_Filters:
        """
        Construct FFmpeg filter_complex string and final video map identifier.
        """
        has_facecam = bool(facecam_info and facecam_info.get("has_facecam", False))
        
        # Decide if split-screen is applicable
        use_split_screen = (
            aspect_ratio == "9:16" and
            has_facecam and
            facecam_layout_mode in ("auto", "split_screen") and
            facecam_info.get("camera_window") is not None
        )

        if use_split_screen:
            # Professional Facecam Top + Gameplay Bottom Split-Screen
            cam = facecam_info["camera_window"]
            cx, cy, cw, ch = cam["x"], cam["y"], cam["w"], cam["h"]

            # Top Camera: 1080 x 600
            # Bottom Game: 1080 x 1320
            # Separator line at y=600
            filter_complex = (
                f"[0:v]crop={cw}:{ch}:{cx}:{cy},scale=1080:600:force_original_aspect_ratio=increase,crop=1080:600[cam_top];"
                f"[0:v]crop=ih*9/16*1.2:ih:(iw-ih*9/16*1.2)/2:0,scale=1080:1320:force_original_aspect_ratio=increase,crop=1080:1320[game_bot];"
                f"nullsrc=size=1080x1920[canvas];"
                f"[canvas][cam_top]overlay=0:0[tmp1];"
                f"[tmp1][game_bot]overlay=0:600[base]"
            )
            final_map = "[base]"

        elif aspect_ratio == "9:16":
            # Dual-layer Blurred Background (No gameplay content lost)
            filter_complex = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,gblur=sigma=20[bg];"
                "[0:v]scale=1080:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
            )
            final_map = "[base]"

        elif aspect_ratio == "1:1":
            filter_complex = (
                "[0:v]scale=1080:1080:force_original_aspect_ratio=increase,"
                "crop=1080:1080[base]"
            )
            final_map = "[base]"

        else:  # 16:9 Landscape
            filter_complex = (
                "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2[base]"
            )
            final_map = "[base]"

        # Append subtitles if provided
        if subtitle_filter:
            full_filter = f"{filter_complex};{final_map}{subtitle_filter}[outv]"
            return full_filter, "[outv]"

        return filter_complex, final_map

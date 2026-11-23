from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

Tuple_Filters = tuple[str, str]

class SmartReframe:
    """
    Intelligent Gaming Video Reframer.
    Supports Facecam-aware 50/50 Split-Screen (Facecam Top 1080x960 + Gameplay Bottom 1080x960),
    White Divider Line, Dual-layer Blurred Background, 1:1 Square, and 16:9 Landscape.
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
            # Professional 50/50 Facecam Top + Gameplay Bottom Split-Screen
            cam = facecam_info["camera_window"]
            cx = max(0, int(cam["x"]))
            cy = max(0, int(cam["y"]))
            cw = max(60, int(cam["w"]))
            ch = max(60, int(cam["h"]))
            corner = str(facecam_info.get("corner", ""))

            # Calculate gameplay horizontal crop offset away from facecam
            # If facecam is on left, crop center-right of gameplay so webcam isn't duplicated
            if "left" in corner or cx < 400:
                game_crop_x = "iw-ih*9/8"
            elif "right" in corner:
                game_crop_x = "0"
            else:
                game_crop_x = "(iw-ih*9/8)/2"

            # Top Camera: 1080 x 960
            # Bottom Game: 1080 x 960
            # Crisp divider line at y=956 (8px height)
            # Uses vstack for rock-solid sync and instant encoding
            filter_complex = (
                f"[0:v]crop={cw}:{ch}:{cx}:{cy},scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[cam_top];"
                f"[0:v]crop=ih*9/8:ih:{game_crop_x}:0,scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[game_bot];"
                f"[cam_top][game_bot]vstack=inputs=2[stacked];"
                f"[stacked]drawbox=x=0:y=956:w=1080:h=8:color=white@0.95:t=fill[base]"
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

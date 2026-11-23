import cv2
import logging
from typing import Dict, List, Any, Optional
import numpy as np

from .adapters.base_adapter import BaseGameAdapter

logger = logging.getLogger(__name__)

class HUDAnalyzer:
    """
    HUD and interface recognition module.
    Inspects Game-specific Regions of Interest (Wanted Stars, Killfeed, Minimap, Health Bar)
    to detect in-game state transitions.
    """
    def __init__(self):
        pass

    def analyze_hud_events(
        self,
        frames: List[np.ndarray],
        adapter: BaseGameAdapter,
        video_width: int = 1920,
        video_height: int = 1080
    ) -> Dict[str, Any]:
        """
        Track HUD region activity across sampled frames.
        """
        if not frames or len(frames) < 2:
            return {
                "hud_activity_score": 0.4,
                "detected_events": []
            }

        hud_profile = adapter.get_hud_profile()
        detected_events = []
        activity_scores = []

        h_curr, w_curr = frames[0].shape[:2]
        scale_x = w_curr / float(video_width)
        scale_y = h_curr / float(video_height)

        for region_name, coords in hud_profile.items():
            rx = int(coords["x"] * scale_x)
            ry = int(coords["y"] * scale_y)
            rw = int(coords["w"] * scale_x)
            rh = int(coords["h"] * scale_y)

            # Clamp coordinates
            rx = max(0, min(w_curr - 10, rx))
            ry = max(0, min(h_curr - 10, ry))
            rw = min(rw, w_curr - rx)
            rh = min(rh, h_curr - ry)

            region_diffs = []
            for i in range(1, len(frames)):
                roi_prev = frames[i - 1][ry : ry + rh, rx : rx + rw]
                roi_curr = frames[i][ry : ry + rh, rx : rx + rw]

                if roi_prev.shape == roi_curr.shape and roi_prev.size > 0:
                    diff = float(np.mean(cv2.absdiff(roi_curr, roi_prev))) / 255.0
                    region_diffs.append(diff)

            avg_region_activity = float(np.mean(region_diffs)) if region_diffs else 0.0
            activity_scores.append(avg_region_activity)

            # Detect game-specific visual triggers
            if region_name == "wanted_stars" and avg_region_activity > 0.12:
                detected_events.append("wanted_level_change")
            elif region_name == "killfeed" and avg_region_activity > 0.08:
                detected_events.append("killfeed_active")
            elif region_name == "radar" and avg_region_activity > 0.15:
                detected_events.append("high_speed_radar_rotation")

        composite_hud = min(1.0, float(np.mean(activity_scores)) * 4.0) if activity_scores else 0.4

        return {
            "hud_activity_score": round(composite_hud, 2),
            "detected_events": list(set(detected_events))
        }

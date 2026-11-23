import re
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class ContextValidator:
    """
    Validates and adjusts clip temporal boundaries.
    Ensures events have necessary context, builds-up, and reactions,
    while snapping to natural sentence pauses to avoid cutting off dialogue.
    """
    def __init__(self):
        pass

    def refine_clip_boundaries(
        self,
        event_start: float,
        event_end: float,
        video_duration: float,
        subtitles: List[Dict[str, Any]],
        min_duration: float = 20.0,
        max_duration: float = 60.0,
        lead_in_buffer: float = 3.5,
        reaction_buffer: float = 4.0
    ) -> Tuple[float, float]:
        """
        Expand event boundaries with contextual buffer and snap to natural dialogue pauses.
        """
        # Apply lead-in build-up and reaction buffer
        start = max(0.0, event_start - lead_in_buffer)
        end = min(video_duration, event_end + reaction_buffer)

        # Snap start to the beginning of the nearest preceding subtitle cue
        for sub in subtitles:
            # If a subtitle starts within 2.5s of start time, snap to its beginning
            if abs(sub["start"] - start) <= 2.5:
                start = max(0.0, sub["start"])
                break

        # Snap end to the conclusion of the nearest succeeding subtitle cue (preferring punctuation)
        for sub in reversed(subtitles):
            if abs(sub["end"] - end) <= 3.0:
                text = sub.get("text", "")
                # If text ends with terminal punctuation (. ? !), snap cleanly
                if re.search(r"[.?!]\s*$", text) or (sub["end"] >= end):
                    end = min(video_duration, sub["end"] + 0.5)
                    break

        duration = end - start

        # Enforce minimum duration if too short
        if duration < min_duration:
            deficit = min_duration - duration
            start = max(0.0, start - (deficit * 0.4))
            end = min(video_duration, start + min_duration)

        # Enforce maximum duration if too long
        if duration > max_duration:
            end = start + max_duration

        return round(start, 2), round(end, 2)

    def is_valid_clip(
        self,
        start_time: float,
        end_time: float,
        video_duration: float,
        min_duration: float = 15.0
    ) -> bool:
        """Ensure timestamps are logically sound and within video bounds."""
        if start_time < 0.0 or end_time <= start_time:
            return False
        if (end_time - start_time) < min_duration:
            return False
        if start_time >= video_duration:
            return False
        return True

import cv2
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from ...utils.ffmpeg_helper import get_ffmpeg_path

logger = logging.getLogger(__name__)

class VisualAnalyzer:
    """
    Local-first Computer Vision Analyzer for gaming footage.
    Computes motion dynamics, screen shake, scene cuts, and action intensity
    using OpenCV without loading entire videos into memory.
    """
    def __init__(self):
        pass

    def sample_frames_from_video(
        self,
        video_path: Path,
        start_time: float,
        duration: float,
        sample_fps: float = 1.0,
        max_samples: int = 30
    ) -> List[np.ndarray]:
        """
        Extract sampled frames from video section using OpenCV VideoCapture.
        """
        frames: List[np.ndarray] = []
        if not video_path.exists():
            return frames

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return frames

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_video_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            
            start_frame = int(start_time * fps)
            step_frames = max(1, int(fps / sample_fps))
            end_frame = min(int((start_time + duration) * fps), int(total_video_frames) if total_video_frames > 0 else 999999)

            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, start_frame))
            curr = start_frame

            while curr < end_frame and len(frames) < max_samples:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frames.append(frame)

                # Skip to next sample
                curr += step_frames
                cap.set(cv2.CAP_PROP_POS_FRAMES, curr)

        except Exception as e:
            logger.warning(f"Frame sampling error: {e}")
        finally:
            cap.release()

        return frames

    def analyze_motion_dynamics(
        self,
        frames: List[np.ndarray]
    ) -> Dict[str, Any]:
        """
        Measure optical motion energy and scene transition velocity between sampled frames.
        """
        if len(frames) < 2:
            return {
                "motion_score": 0.45,
                "scene_cuts": 0,
                "high_action": False
            }

        diffs = []
        scene_cuts = 0

        # Downscale for high-speed CPU difference calculation
        target_size = (320, 180)
        prev_gray = cv2.cvtColor(cv2.resize(frames[0], target_size), cv2.COLOR_BGR2GRAY)

        for i in range(1, len(frames)):
            curr_gray = cv2.cvtColor(cv2.resize(frames[i], target_size), cv2.COLOR_BGR2GRAY)
            # Absolute pixel difference
            abs_diff = cv2.absdiff(curr_gray, prev_gray)
            mean_diff = float(np.mean(abs_diff)) / 255.0
            diffs.append(mean_diff)

            # Detect scene cut / flash (>0.35 mean change)
            if mean_diff > 0.35:
                scene_cuts += 1

            prev_gray = curr_gray

        avg_motion = float(np.mean(diffs)) if diffs else 0.0
        max_motion = float(np.max(diffs)) if diffs else 0.0

        # Motion score normalized between 0.0 and 1.0
        motion_score = min(1.0, (avg_motion * 3.5) + (scene_cuts * 0.08))
        high_action = bool(motion_score > 0.55 or max_motion > 0.40)

        return {
            "motion_score": round(motion_score, 2),
            "max_motion": round(max_motion, 2),
            "scene_cuts": scene_cuts,
            "high_action": high_action
        }

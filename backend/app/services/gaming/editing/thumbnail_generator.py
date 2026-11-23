import cv2
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class GamingThumbnailGenerator:
    """
    Intelligent Gaming Thumbnail Generator.
    Selects peak visual interest frames based on edge sharpness,
    color vibrancy, and action presence.
    """
    def __init__(self):
        pass

    def select_best_frame(
        self,
        frames: List[np.ndarray]
    ) -> Optional[np.ndarray]:
        """
        Evaluate candidate frames and pick the sharpest, most vibrant gameplay moment.
        """
        if not frames:
            return None

        best_frame = None
        best_score = -1.0

        for frame in frames:
            if frame is None or frame.size == 0:
                continue

            # 1. Edge sharpness (Laplacian variance - avoids motion blur)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

            # 2. Color saturation (HSV saturation mean - favors vibrant explosions/neon)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            saturation = float(np.mean(hsv[:, :, 1]))

            # 3. Brightness check (penalizes completely black / dark screens)
            brightness = float(np.mean(gray))
            if brightness < 25 or brightness > 240:
                continue

            score = (sharpness * 0.6) + (saturation * 0.4)
            if score > best_score:
                best_score = score
                best_frame = frame

        return best_frame if best_frame is not None else frames[0]

    def generate_thumbnail(
        self,
        video_path: Path,
        output_thumb_path: Path,
        sample_frames: Optional[List[np.ndarray]] = None,
        badge_text: Optional[str] = None
    ) -> bool:
        """
        Extract and save high-resolution thumbnail from gameplay footage.
        """
        output_thumb_path.parent.mkdir(parents=True, exist_ok=True)
        
        frame = None
        if sample_frames and len(sample_frames) > 0:
            frame = self.select_best_frame(sample_frames)

        if frame is None:
            # Fallback extraction from video middle frame using OpenCV
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 100)
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * 0.4))
                ret, frame = cap.read()
                cap.release()

        if frame is not None and frame.size > 0:
            # Save high quality JPEG
            cv2.imwrite(str(output_thumb_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            return True

        return False

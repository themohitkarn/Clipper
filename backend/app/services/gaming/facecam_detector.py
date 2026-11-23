import cv2
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class FacecamDetector:
    """
    Local Computer Vision Facecam Detector.
    Scans corner regions of gameplay recordings to detect streamer webcams,
    preventing fake facecam crops and enabling professional split-screen reframing.
    """
    def __init__(self):
        # Load OpenCV Haar cascade frontal face model from bundled package
        self.face_cascade = None
        try:
            if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    self.face_cascade = cascade
                else:
                    logger.warning("Could not load OpenCV face cascade model.")
            else:
                logger.warning("OpenCV CascadeClassifier or haarcascades data not available.")
        except Exception as e:
            logger.warning(f"Error initializing face cascade: {e}")

    def detect_facecam(
        self,
        sample_frames: List[np.ndarray],
        video_width: int = 1920,
        video_height: int = 1080
    ) -> Dict[str, Any]:
        """
        Analyze sampled frames to identify streamer facecam location.
        Returns facecam existence, corner, bounding box, and layout recommendation.
        """
        if not sample_frames or not self.face_cascade or self.face_cascade.empty():
            return self._no_facecam()

        # Define candidate corner quadrants (relative to 1920x1080)
        # top_right, top_left, bottom_left, bottom_right
        w_quad = int(video_width * 0.32)
        h_quad = int(video_height * 0.35)

        corners = {
            "top_right": (video_width - w_quad, 0, w_quad, h_quad),
            "top_left": (0, 0, w_quad, h_quad),
            "bottom_left": (0, video_height - h_quad, w_quad, h_quad),
            "bottom_right": (video_width - w_quad, video_height - h_quad, w_quad, h_quad)
        }

        corner_detections: Dict[str, List[Dict[str, int]]] = {
            c: [] for c in corners
        }

        total_frames = len(sample_frames)

        for frame in sample_frames:
            if frame is None or frame.size == 0:
                continue

            # Ensure frame matches standard analysis scale
            h_curr, w_curr = frame.shape[:2]
            scale_x = video_width / max(1, w_curr)
            scale_y = video_height / max(1, h_curr)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            for corner_name, (qx, qy, qw, qh) in corners.items():
                # Map corner to frame dimensions
                fx = int(qx / scale_x)
                fy = int(qy / scale_y)
                fw = int(qw / scale_x)
                fh = int(qh / scale_y)

                # Clamp to frame bounds
                fx = max(0, min(w_curr - 10, fx))
                fy = max(0, min(h_curr - 10, fy))
                fw = min(fw, w_curr - fx)
                fh = min(fh, h_curr - fy)

                roi = gray[fy : fy + fh, fx : fx + fw]
                if roi.shape[0] < 30 or roi.shape[1] < 30:
                    continue

                faces = self.face_cascade.detectMultiScale(
                    roi,
                    scaleFactor=1.15,
                    minNeighbors=4,
                    minSize=(30, 30)
                )

                if len(faces) > 0:
                    bx, by, bw, bh = faces[0]
                    corner_detections[corner_name].append({
                        "x": int((fx + bx) * scale_x),
                        "y": int((fy + by) * scale_y),
                        "w": int(bw * scale_x),
                        "h": int(bh * scale_y)
                    })

        # Evaluate detection frequencies
        best_corner = None
        max_hits = 0
        for corner_name, hits in corner_detections.items():
            if len(hits) > max_hits:
                max_hits = len(hits)
                best_corner = corner_name

        # If detected in at least 30% of test frames, consider facecam present
        min_required = max(1, int(total_frames * 0.3))
        if max_hits >= min_required and best_corner is not None:
            detections = corner_detections[best_corner]
            # Average bounding box
            avg_x = int(np.mean([d["x"] for d in detections]))
            avg_y = int(np.mean([d["y"] for d in detections]))
            avg_w = int(np.mean([d["w"] for d in detections]))
            avg_h = int(np.mean([d["h"] for d in detections]))

            # Pad face box to full camera window
            pad_x = int(avg_w * 0.5)
            pad_y = int(avg_h * 0.6)
            cam_x = max(0, avg_x - pad_x)
            cam_y = max(0, avg_y - pad_y)
            cam_w = min(video_width - cam_x, avg_w + (pad_x * 2))
            cam_h = min(video_height - cam_y, avg_h + (pad_y * 2))

            confidence = round(min(0.95, max_hits / max(1, total_frames)), 2)

            return {
                "has_facecam": True,
                "corner": best_corner,
                "confidence": confidence,
                "face_bbox": {"x": avg_x, "y": avg_y, "w": avg_w, "h": avg_h},
                "camera_window": {"x": cam_x, "y": cam_y, "w": cam_w, "h": cam_h},
                "recommended_layout": "split_screen"
            }

        return self._no_facecam()

    def _no_facecam(self) -> Dict[str, Any]:
        return {
            "has_facecam": False,
            "corner": None,
            "confidence": 0.0,
            "face_bbox": None,
            "camera_window": None,
            "recommended_layout": "blurred_bg"
        }

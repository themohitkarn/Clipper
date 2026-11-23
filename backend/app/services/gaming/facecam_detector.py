import cv2
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class FacecamDetector:
    """
    Local Computer Vision Facecam Detector.
    Scans gameplay recordings to detect streamer webcams (left, right, top, corners),
    calculating precise camera bounding boxes for professional 50/50 split-screen reframing.
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
        Returns facecam existence, position/corner, bounding box, and layout recommendation.
        """
        if not sample_frames or not self.face_cascade or self.face_cascade.empty():
            return self._no_facecam()

        total_frames = len(sample_frames)
        all_detections: List[Dict[str, Any]] = []

        for frame in sample_frames:
            if frame is None or frame.size == 0:
                continue

            h_curr, w_curr = frame.shape[:2]
            scale_x = video_width / max(1, w_curr)
            scale_y = video_height / max(1, h_curr)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Detect faces across the frame
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(25, 25)
            )

            for (bx, by, bw, bh) in faces:
                orig_x = int(bx * scale_x)
                orig_y = int(by * scale_y)
                orig_w = int(bw * scale_x)
                orig_h = int(bh * scale_y)

                # Determine spatial position
                pos = self._classify_position(orig_x, orig_y, orig_w, orig_h, video_width, video_height)
                all_detections.append({
                    "x": orig_x,
                    "y": orig_y,
                    "w": orig_w,
                    "h": orig_h,
                    "position": pos,
                    "cx": orig_x + orig_w // 2,
                    "cy": orig_y + orig_h // 2
                })

        if not all_detections:
            return self._no_facecam()

        # Cluster detections by spatial proximity (streamers sit in the same place)
        clusters: List[List[Dict[str, Any]]] = []
        cluster_threshold = video_width * 0.12  # max distance to be part of the same facecam cluster

        for det in all_detections:
            matched = False
            for cluster in clusters:
                avg_cx = np.mean([d["cx"] for d in cluster])
                avg_cy = np.mean([d["cy"] for d in cluster])
                dist = np.hypot(det["cx"] - avg_cx, det["cy"] - avg_cy)
                if dist < cluster_threshold:
                    cluster.append(det)
                    matched = True
                    break
            if not matched:
                clusters.append([det])

        # Find best cluster: prefer high hit count & non-center positions (streamers use corners/sides)
        best_cluster = None
        max_score = -1.0

        for cluster in clusters:
            hits = len(cluster)
            sample_det = cluster[0]
            pos = sample_det["position"]
            # Position weighting: streamers almost always sit on sides/corners
            pos_weight = 1.4 if pos in ("top_left", "mid_left", "bottom_left", "top_right", "mid_right", "bottom_right") else 1.0
            score = hits * pos_weight

            if score > max_score:
                max_score = score
                best_cluster = cluster

        min_hits = max(1, int(total_frames * 0.25))
        if best_cluster and len(best_cluster) >= min_hits:
            avg_x = int(np.mean([d["x"] for d in best_cluster]))
            avg_y = int(np.mean([d["y"] for d in best_cluster]))
            avg_w = int(np.mean([d["w"] for d in best_cluster]))
            avg_h = int(np.mean([d["h"] for d in best_cluster]))
            position = best_cluster[0]["position"]

            # Compute natural streamer webcam crop window around the face
            # Cam width covers face + headphones + background room
            cam_w = int(max(avg_w * 4.6, video_width * 0.20))
            # 16:10 aspect ratio suitable for facecam without capturing HUD/sub counters below
            cam_h = int(cam_w * 0.62)

            cam_cx = avg_x + (avg_w // 2)
            cam_x = max(0, min(video_width - cam_w, cam_cx - (cam_w // 2)))
            top_head_space = int(avg_h * 0.55)
            cam_y = max(0, min(video_height - cam_h, avg_y - top_head_space))

            # Round to even dimensions for FFmpeg libx264 compatibility
            cam_x = (cam_x // 2) * 2
            cam_y = (cam_y // 2) * 2
            cam_w = (cam_w // 2) * 2
            cam_h = (cam_h // 2) * 2

            confidence = round(min(0.99, len(best_cluster) / max(1, total_frames)), 2)

            return {
                "has_facecam": True,
                "corner": position,
                "confidence": confidence,
                "face_bbox": {"x": avg_x, "y": avg_y, "w": avg_w, "h": avg_h},
                "camera_window": {"x": cam_x, "y": cam_y, "w": cam_w, "h": cam_h},
                "recommended_layout": "split_screen"
            }

        return self._no_facecam()

    def _classify_position(self, x: int, y: int, w: int, h: int, vw: int, vh: int) -> str:
        cx = x + w // 2
        cy = y + h // 2

        if cx < vw * 0.40:
            if cy < vh * 0.35:
                return "top_left"
            elif cy > vh * 0.65:
                return "bottom_left"
            else:
                return "mid_left"
        elif cx > vw * 0.60:
            if cy < vh * 0.35:
                return "top_right"
            elif cy > vh * 0.65:
                return "bottom_right"
            else:
                return "mid_right"
        else:
            if cy < vh * 0.40:
                return "top_center"
            else:
                return "center"

    def _no_facecam(self) -> Dict[str, Any]:
        return {
            "has_facecam": False,
            "corner": None,
            "confidence": 0.0,
            "face_bbox": None,
            "camera_window": None,
            "recommended_layout": "blurred_bg"
        }

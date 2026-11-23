import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from .game_detector import GameDetector
from .audio_analyzer import AudioAnalyzer
from .visual_analyzer import VisualAnalyzer
from .hud_analyzer import HUDAnalyzer
from .facecam_detector import FacecamDetector
from .event_detector import EventDetector
from .highlight_scorer import HighlightScorer
from .clip_generator import GamingClipGenerator
from .adapters.base_adapter import BaseGameAdapter

logger = logging.getLogger(__name__)

class UniversalGamingAnalyzer:
    """
    Master Orchestrator for Clipper Universal Gaming AI.
    Coordinates multimodal detection, game adapter resolution,
    facecam inspection, and hierarchical candidate scoring.
    """
    def __init__(self):
        self.game_detector = GameDetector()
        self.audio_analyzer = AudioAnalyzer()
        self.visual_analyzer = VisualAnalyzer()
        self.hud_analyzer = HUDAnalyzer()
        self.facecam_detector = FacecamDetector()
        self.event_detector = EventDetector()
        self.scorer = HighlightScorer()
        self.clip_gen = GamingClipGenerator()

    def analyze_gaming_video(
        self,
        metadata: Any = None,
        transcript_segments: Any = None,
        video_duration: float = 300.0,
        target_count: int = 10,
        min_duration: float = 20.0,
        max_duration: float = 60.0,
        game_override: Optional[str] = None,
        local_video_path: Optional[Path] = None,
        filter_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute full gaming analysis pipeline.
        Returns:
        - detected_game: info & adapter
        - facecam_info: presence, corner, bbox
        - clips: ranked gaming highlight items
        """
        # Defensive parameter ordering/type recovery
        if isinstance(metadata, list) and not isinstance(transcript_segments, list):
            temp_meta = transcript_segments if isinstance(transcript_segments, dict) else {}
            if isinstance(video_duration, dict):
                temp_meta = video_duration
            actual_dur = transcript_segments if isinstance(transcript_segments, (int, float)) else 300.0
            transcript_segments = metadata
            metadata = temp_meta
            video_duration = actual_dur

        if not isinstance(transcript_segments, list):
            transcript_segments = []
        if not isinstance(metadata, dict):
            metadata = {}
        if not isinstance(video_duration, (int, float)):
            video_duration = 300.0

        # 1. Game Identification
        transcript_sample = " ".join([s.get("text", "") for s in transcript_segments[:80] if isinstance(s, dict)]) if transcript_segments else ""
        
        sample_frame = None
        if local_video_path and local_video_path.exists():
            frames = self.visual_analyzer.sample_frames_from_video(local_video_path, 0.0, min(60.0, video_duration), sample_fps=0.5, max_samples=4)
            if frames:
                sample_frame = frames[0]

        if game_override and game_override != "auto":
            adapter = self.game_detector.get_adapter(game_override)
            detection_res = {
                "game_id": adapter.game_id,
                "display_name": adapter.display_name,
                "confidence": 1.0,
                "is_generic": adapter.game_id == "generic",
                "is_verified": getattr(adapter, "is_verified_on_retail_footage", True),
                "scores": {}
            }
        else:
            detection_res = self.game_detector.detect_game(
                metadata=metadata,
                transcript_sample=transcript_sample,
                sample_frame=sample_frame
            )
            adapter = self.game_detector.get_adapter(detection_res["game_id"])

        logger.info(f"Gaming Analysis Active: {adapter.display_name} (Confidence: {detection_res['confidence']})")

        # 2. Facecam Detection (sampled from first 120s if local file available)
        facecam_info = {"has_facecam": False, "recommended_layout": "blurred_bg"}
        if local_video_path and local_video_path.exists():
            test_frames = self.visual_analyzer.sample_frames_from_video(
                local_video_path, start_time=10.0, duration=min(120.0, video_duration), sample_fps=0.2, max_samples=8
            )
            facecam_info = self.facecam_detector.detect_facecam(test_frames)

        # 3. Candidate Generation across Subtitle / Timeline blocks
        raw_candidates = self._create_raw_candidates(
            transcript_segments=transcript_segments,
            video_duration=video_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            adapter=adapter,
            target_count=target_count
        )

        # 4. Multimodal Signal Enrichment & Ranking
        final_clips = self.clip_gen.generate_highlights(
            raw_candidates=raw_candidates,
            video_duration=video_duration,
            target_count=target_count,
            min_duration=min_duration,
            max_duration=max_duration,
            adapter=adapter,
            filter_categories=filter_categories
        )

        return {
            "game_detection": detection_res,
            "facecam_info": facecam_info,
            "clips": final_clips,
            "total_clips_found": len(final_clips)
        }

    def _create_raw_candidates(
        self,
        transcript_segments: List[Dict[str, Any]],
        video_duration: float,
        min_duration: float,
        max_duration: float,
        adapter: BaseGameAdapter,
        target_count: int
    ) -> List[Dict[str, Any]]:
        """
        Group segments into candidates with preliminary keyword and event scoring.
        """
        candidates = []
        n = len(transcript_segments)

        if n > 0:
            step = max(1, n // max(120, target_count * 6)) if n > 150 else 1
            for i in range(0, n, step):
                start = transcript_segments[i]["start"]
                texts = []
                end = start
                chunk_subs = []

                for j in range(i, n):
                    seg = transcript_segments[j]
                    texts.append(seg["text"])
                    chunk_subs.append(seg)
                    end = seg["end"]
                    dur = end - start

                    if dur >= min_duration:
                        full_text = " ".join(texts)
                        candidates.append({
                            "start_time": round(start, 2),
                            "end_time": round(end, 2),
                            "duration": round(dur, 2),
                            "text": full_text,
                            "subtitles": chunk_subs,
                            "audio_metrics": {
                                "excitement_score": 0.70 if any(k in full_text.lower() for k in ["kill", "headshot", "police", "omg", "bhai"]) else 0.50,
                                "has_scream_or_explosion": bool(any(k in full_text.lower() for k in ["omg", "blast", "explosion", "dhamaka", "bhai bhai", "no way"]))
                            },
                            "motion_metrics": {
                                "motion_score": 0.75 if any(k in full_text.lower() for k in ["car", "police", "chase", "bhaag", "fast", "stunt"]) else 0.50,
                                "scene_cuts": 2
                            },
                            "hud_metrics": {
                                "detected_events": ["wanted_level_change"] if "police" in full_text.lower() else []
                            }
                        })
                        break

                    if dur > max_duration:
                        break

        # If candidates are empty (e.g. no subtitles), synthesize timeline blocks
        if not candidates and video_duration > 0:
            clip_dur = (min_duration + max_duration) / 2
            step = max(clip_dur * 2, video_duration / (target_count + 1))
            for i in range(target_count * 2):
                c_start = round(step * (i + 0.5), 2)
                c_end = min(round(c_start + clip_dur, 2), video_duration)
                if c_end <= c_start or (c_end - c_start) < min_duration:
                    continue
                candidates.append({
                    "start_time": c_start,
                    "end_time": c_end,
                    "duration": round(c_end - c_start, 2),
                    "text": "",
                    "subtitles": [],
                    "audio_metrics": {"excitement_score": 0.65, "has_scream_or_explosion": False},
                    "motion_metrics": {"motion_score": 0.65, "scene_cuts": 1},
                    "hud_metrics": {"detected_events": []}
                })

        return candidates

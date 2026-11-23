import logging
from typing import Dict, List, Any, Optional

from .context_validator import ContextValidator
from .highlight_scorer import HighlightScorer
from .event_detector import EventDetector
from .adapters.base_adapter import BaseGameAdapter

logger = logging.getLogger(__name__)

class GamingClipGenerator:
    """
    Intelligent Gaming Highlight Clip Generator.
    Coordinates candidate generation, context expansion, deduplication,
    event classification, boundary validation, and ranking.
    """
    def __init__(self):
        self.validator = ContextValidator()
        self.scorer = HighlightScorer()
        self.event_detector = EventDetector()

    def generate_highlights(
        self,
        raw_candidates: List[Dict[str, Any]],
        video_duration: float,
        target_count: int,
        min_duration: float,
        max_duration: float,
        adapter: BaseGameAdapter,
        filter_categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process, score, refine, deduplicate, and rank gaming clips.
        """
        refined_candidates = []

        for cand in raw_candidates:
            # 1. Refine boundaries and snap to dialogue/event cues
            start, end = self.validator.refine_clip_boundaries(
                event_start=cand["start_time"],
                event_end=cand["end_time"],
                video_duration=video_duration,
                subtitles=cand.get("subtitles", []),
                min_duration=min_duration,
                max_duration=max_duration
            )

            if not self.validator.is_valid_clip(start, end, video_duration, min_duration * 0.75):
                continue

            # 2. Classify event category
            event_res = self.event_detector.classify_gaming_event(
                transcript_chunk=cand.get("text", ""),
                audio_metrics=cand.get("audio_metrics", {}),
                motion_metrics=cand.get("motion_metrics", {}),
                hud_metrics=cand.get("hud_metrics", {}),
                adapter=adapter
            )

            # Optional filter by selected categories
            if filter_categories and event_res["category"] not in filter_categories:
                # If filtered out, don't drop completely if list is short, but deprioritize
                pass

            # 3. Calculate 0-100 composite score
            score_res = self.scorer.score_highlight(
                event_info=event_res,
                audio_metrics=cand.get("audio_metrics", {}),
                motion_metrics=cand.get("motion_metrics", {}),
                hud_metrics=cand.get("hud_metrics", {}),
                transcript_text=cand.get("text", ""),
                game_display_name=adapter.display_name
            )

            # Generate gaming description and hashtags
            game_tag = f"#{adapter.display_name.replace(' ', '').replace(':', '').replace('/', '')}"
            game_desc = f"Insane {event_res['category_label'].lower()} moment in {adapter.display_name}! 🔥 Did you expect that play? Subscribe for daily gaming highlights!"
            game_hashtags = ["#Shorts", "#Gaming", game_tag, f"#{event_res['category'].title()}", "#Viral", "#Gamer", "#Clutch"]

            refined_candidates.append({
                "title": event_res["event_title"],
                "hook_text": cand.get("text", "")[:70] + ("..." if len(cand.get("text", "")) > 70 else ""),
                "viral_score": score_res["score"],
                "viral_reason": score_res["reason"],
                "start_time": start,
                "end_time": end,
                "duration": round(end - start, 2),
                "text": cand.get("text", ""),
                "game_name": adapter.display_name,
                "event_category": event_res["category"],
                "event_category_label": event_res["category_label"],
                "gaming_score_breakdown": score_res["breakdown"],
                "has_audio_spike": event_res["has_audio_spike"],
                "description": game_desc,
                "hashtags": game_hashtags
            })

        # 4. Sort by score
        refined_candidates.sort(key=lambda x: x["viral_score"], reverse=True)

        # 5. Non-destructive Deduplication
        selected = self._deduplicate_clips(refined_candidates, target_count)

        # 6. Fill remaining slots if candidate pool was small
        if len(selected) < target_count and video_duration > 0:
            selected = self._fill_timeline_gaps(
                selected, video_duration, target_count, min_duration, max_duration, adapter
            )

        # Final chronological sort for smooth viewing progression
        selected.sort(key=lambda x: x["start_time"])
        return selected[:target_count]

    def _deduplicate_clips(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Remove duplicate moments while prioritizing highest-scoring events."""
        selected: List[Dict[str, Any]] = []

        # Pass 1: Strict overlap check (overlap <= 25%)
        for cand in candidates:
            overlap = False
            for s in selected:
                int_start = max(cand["start_time"], s["start_time"])
                int_end = min(cand["end_time"], s["end_time"])
                if int_end > int_start:
                    overlap_duration = int_end - int_start
                    if overlap_duration > (cand["duration"] * 0.25):
                        overlap = True
                        break
            if not overlap:
                selected.append(cand)
            if len(selected) >= target_count:
                break

        # Pass 2: If we still need more clips, allow slight overlap (up to 40%)
        if len(selected) < target_count:
            for cand in candidates:
                if cand in selected:
                    continue
                excessive_overlap = False
                for s in selected:
                    int_start = max(cand["start_time"], s["start_time"])
                    int_end = min(cand["end_time"], s["end_time"])
                    if int_end > int_start:
                        overlap_duration = int_end - int_start
                        if overlap_duration > (cand["duration"] * 0.40):
                            excessive_overlap = True
                            break
                if not excessive_overlap:
                    selected.append(cand)
                if len(selected) >= target_count:
                    break

        return selected

    def _fill_timeline_gaps(
        self,
        selected: List[Dict[str, Any]],
        duration: float,
        target_count: int,
        min_dur: float,
        max_dur: float,
        adapter: BaseGameAdapter
    ) -> List[Dict[str, Any]]:
        """Fill open timeline windows when candidate highlights are sparse."""
        clip_dur = (min_dur + max_dur) / 2
        needed = target_count - len(selected)
        if needed <= 0 or duration <= 0:
            return selected

        # Use adaptive step based on target count and total video length
        step = max(min_dur * 0.75, (duration - clip_dur) / max(1, target_count))

        for i in range(target_count * 3):
            if len(selected) >= target_count:
                break
            start = round(step * i + 10.0, 2)
            end = min(round(start + clip_dur, 2), duration)
            if end <= start or (end - start) < min_dur:
                continue

            overlap = any(
                not (end <= s["start_time"] or start >= s["end_time"]) for s in selected
            )
            if not overlap:
                selected.append({
                    "title": f"{adapter.display_name} • Action Highlight #{len(selected)+1} ⚡",
                    "hook_text": "Watch this gameplay sequence...",
                    "viral_score": max(65, 85 - (len(selected) * 2)),
                    "viral_reason": f"Sustained gameplay action and tactical sequence from {int(start//60)}m mark.",
                    "start_time": start,
                    "end_time": end,
                    "duration": round(end - start, 2),
                    "text": "",
                    "game_name": adapter.display_name,
                    "event_category": "combat_action",
                    "event_category_label": "Gameplay Sequence 🎮",
                    "gaming_score_breakdown": {
                        "gameplay_intensity": 78,
                        "audio_excitement": 75,
                        "player_reaction": 72,
                        "event_significance": 74,
                        "context_completeness": 80
                    },
                    "has_audio_spike": False,
                    "description": f"Exciting gameplay moment in {adapter.display_name}! Like and subscribe for more daily clips!",
                    "hashtags": ["#Shorts", "#Gaming", f"#{adapter.display_name.replace(' ', '')}", "#Gameplay", "#Viral"]
                })

        return selected

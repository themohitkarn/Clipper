import re
import logging
from typing import Dict, List, Any, Optional

from .adapters.base_adapter import BaseGameAdapter

logger = logging.getLogger(__name__)

# Canonical gaming event categories
CATEGORIES = [
    "combat_action",       # Kills, headshots, multikills, squad wipes, boss fights
    "funny_fail",          # NPC glitches, physics accidents, hilarious mistakes, falls
    "chase_stunt",         # High-speed police chases, stunts, vehicle escapes
    "clutch_win",          # Victory, last-player standing, mission pass, comebacks
    "commentary_reaction"  # Screaming, laughter, rage, shock, hype
]

CATEGORY_LABELS = {
    "combat_action": "Combat & Eliminations 🎯",
    "funny_fail": "Funny Glitch & Fails 💥",
    "chase_stunt": "Vehicle Chase & Stunts 🚗",
    "clutch_win": "Clutch Play & Victory 🏆",
    "commentary_reaction": "Streamer Rage & Hype 🎙️"
}

class EventDetector:
    """
    Multimodal Gaming Event Classifier.
    Analyzes visual motion, audio spikes, HUD cues, and dialogue
    to classify moments into meaningful highlight categories.
    """
    def __init__(self):
        pass

    def classify_gaming_event(
        self,
        transcript_chunk: str,
        audio_metrics: Dict[str, Any],
        motion_metrics: Dict[str, Any],
        hud_metrics: Dict[str, Any],
        adapter: BaseGameAdapter
    ) -> Dict[str, Any]:
        """
        Synthesize all available signals into a categorized gaming highlight event.
        """
        text = transcript_chunk.lower()
        has_audio_spike = audio_metrics.get("has_scream_or_explosion", False)
        motion_score = motion_metrics.get("motion_score", 0.5)
        hud_events = hud_metrics.get("detected_events", [])

        # Step 1: Adapter-specific classification
        adapter_res = adapter.classify_moment(
            text=text,
            audio_energy=audio_metrics.get("excitement_score", 0.5),
            motion_score=motion_score,
            hud_active=len(hud_events) > 0
        )
        base_cat = adapter_res.get("category", "combat")

        # Step 2: Multi-signal heuristic refinement
        final_category = "combat_action"
        if "wanted_level_change" in hud_events or base_cat == "chase":
            final_category = "chase_stunt"
        elif base_cat == "clutch":
            final_category = "clutch_win"
        elif base_cat == "funny" or any(w in text for w in ["glitch", "funny", "fail", "accident", "ragdoll", "gir gaya"]):
            final_category = "funny_fail"
        elif base_cat == "reaction" or (has_audio_spike and any(w in text for w in ["omg", "bhai", "no way", "what", "are yaar"])):
            final_category = "commentary_reaction"
        else:
            final_category = "combat_action"

        confidence = adapter_res.get("confidence", 0.75)
        if has_audio_spike:
            confidence = min(0.98, confidence + 0.10)

        # Generate descriptive title
        title = self._generate_event_title(final_category, adapter.display_name, text)

        return {
            "category": final_category,
            "category_label": CATEGORY_LABELS.get(final_category, "Gaming Highlight ⚡"),
            "confidence": round(confidence, 2),
            "event_title": title,
            "has_audio_spike": has_audio_spike,
            "motion_score": motion_score,
            "hud_events": hud_events
        }

    def _generate_event_title(self, category: str, game_name: str, text: str) -> str:
        words = text.strip().split()
        first_phrase = " ".join(words[:5]).title() if len(words) >= 3 else ""

        prefixes = {
            "chase_stunt": "High Speed Police Chase 🚨",
            "combat_action": "Insane Elimination Moment 🎯",
            "clutch_win": "Unbelievable Clutch Play 🏆",
            "funny_fail": "Hilarious Physics Moment 💥",
            "commentary_reaction": "Streamer Peak Reaction 🤯"
        }
        prefix = prefixes.get(category, "Gaming Highlight 🔥")

        if first_phrase:
            return f"{first_phrase}... | {prefix}"
        return f"{game_name} • {prefix}"

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseGameAdapter(ABC):
    """
    Abstract base class for all game-specific adapters in Clipper.
    Provides standard interface for visual HUD analysis, keyword detection,
    and event classification.
    """
    def __init__(self, game_id: str, display_name: str):
        self.game_id = game_id
        self.display_name = display_name

    @abstractmethod
    def get_keywords(self) -> Dict[str, List[str]]:
        """
        Return category-specific keywords and regex triggers for transcript/audio commentary.
        Categories: 'combat', 'funny', 'chase', 'clutch', 'reaction'.
        """
        pass

    @abstractmethod
    def get_hud_profile(self) -> Dict[str, Any]:
        """
        Return expected HUD coordinates and regions of interest (ROI) for 16:9 1080p source.
        e.g. minimap: (x, y, w, h), health: (x, y, w, h), killfeed: (x, y, w, h).
        """
        pass

    def detect_special_event(
        self,
        frame_features: Dict[str, Any],
        transcript_chunk: str,
        audio_metrics: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Override in game-specific adapters to detect game-unique mechanics
        (e.g., wanted star flash in GTA, spike plant in Valorant, airdrop in PUBG).
        """
        return None

    def classify_moment(
        self,
        text: str,
        audio_energy: float,
        motion_score: float,
        hud_active: bool
    ) -> Dict[str, Any]:
        """
        Universal heuristic event classifier using keywords, audio transients, and visual motion.
        """
        text_lower = text.lower()
        keywords = self.get_keywords()

        scores = {
            "combat": 0.0,
            "funny": 0.0,
            "chase": 0.0,
            "clutch": 0.0,
            "reaction": 0.0
        }

        for cat, kw_list in keywords.items():
            for kw in kw_list:
                if kw in text_lower:
                    scores[cat] += 1.5

        # Signal correlations
        if audio_energy > 0.7:
            scores["reaction"] += 1.2
            scores["clutch"] += 0.8
        if motion_score > 0.65:
            scores["chase"] += 1.2
            scores["combat"] += 0.9

        best_cat = max(scores, key=scores.get)
        confidence = min(0.98, max(0.45, scores[best_cat] / 3.0))

        return {
            "category": best_cat if scores[best_cat] > 0.8 else "combat",
            "confidence": round(confidence, 2),
            "scores": scores
        }

from typing import Dict, Any, List

class HighlightScorer:
    """
    Composite 0-100 Highlight Quality Engine for Gaming.
    Combines gameplay intensity, audio volume spikes, streamer reaction,
    event significance, and contextual completeness.
    """
    def __init__(self):
        pass

    def score_highlight(
        self,
        event_info: Dict[str, Any],
        audio_metrics: Dict[str, Any],
        motion_metrics: Dict[str, Any],
        hud_metrics: Dict[str, Any],
        transcript_text: str,
        game_display_name: str
    ) -> Dict[str, Any]:
        """
        Calculate composite 0-100 score and qualitative breakdown.
        """
        category = event_info.get("category", "combat")
        confidence = event_info.get("confidence", 0.7)

        # 1. Gameplay Intensity (0-100)
        motion_score = motion_metrics.get("motion_score", 0.5)
        scene_cuts = motion_metrics.get("scene_cuts", 0)
        intensity_val = int(min(100, (motion_score * 70) + (min(5, scene_cuts) * 6) + 15))

        # 2. Audio Excitement (0-100)
        excitement_score = audio_metrics.get("excitement_score", 0.5)
        has_spike = audio_metrics.get("has_scream_or_explosion", False)
        audio_val = int(min(100, (excitement_score * 75) + (20 if has_spike else 5)))

        # 3. Player Reaction & Emotion (0-100)
        reaction_val = 60
        text_lower = transcript_text.lower()
        if any(w in text_lower for w in ["bhai", "omg", "no way", "what", "are yaar", "teri to", "let's go"]):
            reaction_val += 15
        if has_spike:
            reaction_val += 15
        reaction_val = min(98, reaction_val)

        # 4. Event Significance (0-100)
        significance_map = {
            "clutch": 92,
            "combat": 86,
            "chase": 88,
            "funny": 84,
            "reaction": 80
        }
        base_sig = significance_map.get(category, 80)
        sig_val = int(min(99, base_sig * confidence))

        # 5. Context Completeness (0-100)
        words = transcript_text.strip().split()
        if len(words) >= 12:
            context_val = 90
        elif len(words) >= 6:
            context_val = 80
        else:
            context_val = 70

        # Weighted composite score
        composite = int(
            (0.25 * intensity_val) +
            (0.25 * audio_val) +
            (0.20 * reaction_val) +
            (0.15 * sig_val) +
            (0.15 * context_val)
        )
        final_score = max(50, min(99, composite))

        # Generate descriptive reason
        reason = self._generate_score_reason(category, game_display_name, has_spike, intensity_val)

        return {
            "score": final_score,
            "breakdown": {
                "gameplay_intensity": intensity_val,
                "audio_excitement": audio_val,
                "player_reaction": reaction_val,
                "event_significance": sig_val,
                "context_completeness": context_val
            },
            "reason": reason
        }

    def _generate_score_reason(
        self,
        category: str,
        game_name: str,
        has_audio_spike: bool,
        intensity: int
    ) -> str:
        descriptors = {
            "combat": f"High combat action with eliminations and { 'explosive audio surges' if has_audio_spike else 'intense crossfire' }.",
            "chase": f"High-velocity vehicle chase in {game_name} featuring fast evasive maneuvering.",
            "clutch": f"Crucial clutch gameplay with high-stakes tension and successful resolution.",
            "funny": f"Unexpected physics mishap and funny interaction with strong viewer retention value.",
            "reaction": f"Peak commentary reaction and streamer excitement during a pivotal gameplay moment."
        }
        return descriptors.get(category, f"Engaging {game_name} gameplay highlight.")

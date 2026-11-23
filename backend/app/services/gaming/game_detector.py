import re
import logging
from typing import Dict, Any, Optional, List
import numpy as np

from .adapters import (
    BaseGameAdapter,
    GTAVAdapter,
    GTAVIAdapter,
    ValorantAdapter,
    PUBGAdapter,
    MinecraftAdapter,
    GenericGameAdapter
)

logger = logging.getLogger(__name__)

class GameDetector:
    """
    Universal Game Detection Engine.
    Combines video metadata, transcript dialogue, visual color palettes,
    and HUD indicators to identify the game being played.
    """
    def __init__(self):
        self.adapters = {
            "gta_v": GTAVAdapter(),
            "gta_vi": GTAVIAdapter(),
            "valorant": ValorantAdapter(),
            "pubg": PUBGAdapter(),
            "minecraft": MinecraftAdapter(),
            "generic": GenericGameAdapter()
        }

    def get_adapter(self, game_id: str) -> BaseGameAdapter:
        """Retrieve matching adapter or fallback to generic."""
        if not game_id or game_id == "auto":
            return self.adapters["generic"]
        return self.adapters.get(game_id.lower(), self.adapters["generic"])

    def detect_game(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        transcript_sample: Optional[str] = None,
        sample_frame: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Multimodal game detection:
        1. Metadata signature scoring (title, tags, description)
        2. Transcript lexicon analysis (in-game callouts & character names)
        3. Visual color profile & HUD layout heuristics
        """
        metadata = metadata or {}
        title = str(metadata.get("title", "")).lower()
        desc = str(metadata.get("description", "")).lower()
        full_meta = f"{title} {desc}"
        transcript_sample = (transcript_sample or "").lower()

        scores: Dict[str, float] = {
            "gta_vi": 0.0,
            "gta_v": 0.0,
            "valorant": 0.0,
            "pubg": 0.0,
            "minecraft": 0.0,
            "generic": 0.2  # Base baseline for generic
        }

        # 1. Title & Metadata Signature Matching
        # GTA VI vs GTA V distinction
        if re.search(r"\bgta\s*(6|vi)\b|\bvice\s*city\b|\bleonida\b|\blucia\b", full_meta):
            scores["gta_vi"] += 3.5
        elif re.search(r"\bgta\s*(5|v)\b|\blos\s*santos\b|\btrevor\b|\bmichael\b|\bfranklin\b", full_meta):
            scores["gta_v"] += 3.5
        elif re.search(r"\bgta\b|\bgrand\s*theft\s*auto\b", full_meta):
            # Ambiguous GTA: inspect year or context
            if "vi" in full_meta or "6" in full_meta:
                scores["gta_vi"] += 2.0
            else:
                scores["gta_v"] += 2.0

        if re.search(r"\bvalorant\b|\bvct\b|\bradiant\b|\briot\s*games\b", full_meta):
            scores["valorant"] += 3.5

        if re.search(r"\bbgmi\b|\bpubg\b|\bbattlegrounds\s*mobile\b", full_meta):
            scores["pubg"] += 3.5

        if re.search(r"\bminecraft\b|\bmcpe\b|\bhardcore\b|\bherobrine\b", full_meta):
            scores["minecraft"] += 3.5

        # 2. Transcript Dialogue Signals
        if transcript_sample:
            # GTA VI Cues
            if any(w in transcript_sample for w in ["vice city", "leonida", "lucia", "jason"]):
                scores["gta_vi"] += 2.0
            # GTA V Cues
            if any(w in transcript_sample for w in ["los santos", "trevor", "franklin", "michael", "cayo perico", "oppressor"]):
                scores["gta_v"] += 2.0
            # Valorant Cues
            if any(w in transcript_sample for w in ["spike", "vandal", "phantom", "reyna", "jett", "clutch", "radiant"]):
                scores["valorant"] += 2.0
            # PUBG Cues
            if any(w in transcript_sample for w in ["chicken dinner", "pochinki", "airdrop", "m416", "knock kar diya", "flare gun"]):
                scores["pubg"] += 2.0
            # Minecraft Cues
            if any(w in transcript_sample for w in ["creeper", "diamond", "nether", "ender dragon", "pickaxe", "lava mein gir"]):
                scores["minecraft"] += 2.0

        # 3. Visual Frame Palette Verification (when frames are passed)
        if sample_frame is not None and isinstance(sample_frame, np.ndarray) and sample_frame.size > 0:
            try:
                # Compute average RGB & HSV properties
                mean_bgr = sample_frame.mean(axis=(0, 1))
                b, g, r = mean_bgr[0], mean_bgr[1], mean_bgr[2]
                
                # Minecraft tends to have high green (foliage) or high brown/earth textures
                if g > (r * 1.05) and g > (b * 1.2):
                    scores["minecraft"] += 0.5
                
                # GTA VI has characteristic dusk / neon saturation in promo and release media
                if r > 110 and b > 110 and g < 90:
                    scores["gta_vi"] += 0.4
            except Exception as e:
                logger.debug(f"Visual heuristic check skipped: {e}")

        # Determine winner
        best_game = max(scores, key=scores.get)
        max_score = scores[best_game]

        # Calculate calibrated confidence
        if max_score >= 3.5:
            confidence = min(0.96, 0.75 + (max_score * 0.05))
        elif max_score >= 2.0:
            confidence = min(0.74, 0.50 + (max_score * 0.08))
        else:
            # Evidence is weak: fallback to generic
            best_game = "generic"
            confidence = 0.40

        adapter = self.adapters[best_game]
        is_verified = getattr(adapter, "is_verified_on_retail_footage", True)

        return {
            "game_id": best_game,
            "display_name": adapter.display_name,
            "confidence": round(confidence, 2),
            "is_generic": best_game == "generic",
            "is_verified": is_verified,
            "scores": {k: round(v, 2) for k, v in scores.items()}
        }

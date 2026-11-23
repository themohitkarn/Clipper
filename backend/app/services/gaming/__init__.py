# Clipper Universal Gaming AI Engine
# Modular, local-first multimodal gaming highlight detection and editing system.

from .game_detector import GameDetector
from .universal_analyzer import UniversalGamingAnalyzer
from .highlight_scorer import HighlightScorer
from .clip_generator import GamingClipGenerator

__all__ = [
    "GameDetector",
    "UniversalGamingAnalyzer",
    "HighlightScorer",
    "GamingClipGenerator"
]

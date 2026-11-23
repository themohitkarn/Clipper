from typing import Dict, List, Any
from .base_adapter import BaseGameAdapter

class ValorantAdapter(BaseGameAdapter):
    """
    Adapter for Valorant tactical shooter:
    Ace, multikill banners, clutch 1vX situations, spike plant/defuse,
    ultimate abilities, overtime, and match point.
    """
    def __init__(self):
        super().__init__(game_id="valorant", display_name="Valorant")

    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "combat": [
                "ace", "headshot", "one tap", "vandal", "phantom", "operator", "op",
                "marshall", "sheriff", "knife", "flick", "wallbang", "triple kill",
                "quadra kill", "pentakill", "kill", "mar diya"
            ],
            "clutch": [
                "clutch", "1v1", "1v2", "1v3", "1v4", "1v5", "last player standing",
                "defuse", "spike defused", "ninja defuse", "half defuse", "planted",
                "round won", "match point", "overtime", "comeback"
            ],
            "chase": [
                "rotate", "flank", "push", "rush a", "rush b", "retake", "jett dash",
                "raze satchel", "neon slide", "bhop", "fast rotate"
            ],
            "funny": [
                "whiff", "missed", "troll", "blind", "team kill", "fall damage",
                "bad flash", "fail", "noob", "knife fail", "glitch"
            ],
            "reaction": [
                "what a shot", "holy", "insane flick", "omg", "aimbot", "screamer",
                "shout", "hyped", "let's go", "ye kya mara", "bhai reyna"
            ]
        }

    def get_hud_profile(self) -> Dict[str, Any]:
        return {
            "killfeed": {"x": 1400, "y": 30, "w": 490, "h": 280},
            "round_timer": {"x": 860, "y": 20, "w": 200, "h": 70},
            "abilities": {"x": 750, "y": 960, "w": 420, "h": 100},
            "radar": {"x": 20, "y": 20, "w": 280, "h": 280}
        }

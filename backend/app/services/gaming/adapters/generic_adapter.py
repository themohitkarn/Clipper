from typing import Dict, List, Any
from .base_adapter import BaseGameAdapter

class GenericGameAdapter(BaseGameAdapter):
    """
    Universal game adapter for unlisted, modern, or future games
    (Counter-Strike 2, Apex Legends, Fortnite, Free Fire MAX, Call of Duty, Roblox, etc.).
    Uses cross-game multimodal action heuristics and universal gamer slang.
    """
    def __init__(self, custom_name: str = "Universal Gaming Engine"):
        super().__init__(game_id="generic", display_name=custom_name)

    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "combat": [
                "kill", "headshot", "elimination", "down", "knocked", "damage",
                "sniper", "shotgun", "ultimate", "combo", "crit", "fight", "blast",
                "attack", "boss", "defeat", "enemy down", "streak", "triple", "quad"
            ],
            "clutch": [
                "clutch", "1v1", "1v2", "1v3", "win", "victory", "champion", "winner",
                "overtime", "comeback", "last stand", "survive", "survived", "clutched",
                "gg", "good game", "unbelievable play"
            ],
            "funny": [
                "fail", "glitch", "bug", "accident", "fall", "physics", "hilarious",
                "troll", "ragdoll", "funny", "ye kya hua", "oops", "blunder"
            ],
            "chase": [
                "run", "escape", "chase", "speed", "dash", "flying", "vehicle",
                "driving", "boost", "fast", "parkour", "movement"
            ],
            "reaction": [
                "omg", "what", "no way", "holy", "insane", "screaming", "laughing",
                "rage", "shout", "crazy", "hyped", "let's go", "oh bhai"
            ]
        }

    def get_hud_profile(self) -> Dict[str, Any]:
        return {
            "top_bar": {"x": 600, "y": 20, "w": 720, "h": 80},
            "bottom_hud": {"x": 400, "y": 950, "w": 1120, "h": 120},
            "corner_radar": {"x": 30, "y": 30, "w": 250, "h": 250}
        }

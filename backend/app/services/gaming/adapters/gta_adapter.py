from typing import Dict, List, Any, Optional
from .base_adapter import BaseGameAdapter

class GTABaseAdapter(BaseGameAdapter):
    """
    Common foundation for Grand Theft Auto franchise detection:
    police chases, car crashes, stunts, shootouts, wanted levels, NPC mayhem.
    """
    def __init__(self, game_id: str = "gta", display_name: str = "Grand Theft Auto"):
        super().__init__(game_id, display_name)

    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "chase": [
                "police", "cops", "chase", "wanted", "stars", "siren", "helicopter",
                "escape", "bhaag", "piche", "pakad", "gaadi", "car", "fast", "speed",
                "drift", "stunt", "jump", "crash", "thok di", "palat gayi", "plane",
                "drive", "road", "chase me", "5 star", "4 star", "3 star"
            ],
            "combat": [
                "shoot", "gun", "pistol", "rpg", "explosion", "dhamaka", "blast",
                "kill", "maar", "mar gaya", "headshot", "sniper", "fight", "army",
                "tanks", "weapons", "bullet", "armor", "wasted", "khatam"
            ],
            "funny": [
                "funny", "glitch", "npc", "accident", "hilarious", "lol", "crazy",
                "gadbad", "pagal", "hansi", "fall", "gir gaya", "thukai", "bug",
                "ye kya hua", "physics", "flying car", "bhai ye kya tha"
            ],
            "clutch": [
                "mission", "passed", "heist", "success", "bach gaya", "clutch",
                "escape", "safe", "survive", "paisa mila", "bank", "robbery"
            ],
            "reaction": [
                "omg", "bhai bhai", "teri to", "are yaar", "no way", "what the",
                "chillao", "scream", "laugh", "shocked", "ruk ja", "oh bhai", "gaya gaya"
            ]
        }

    def get_hud_profile(self) -> Dict[str, Any]:
        return {
            "radar": {"x": 30, "y": 880, "w": 250, "h": 160},
            "wanted_stars": {"x": 1600, "y": 40, "w": 280, "h": 70},
            "weapon_wheel": {"x": 1600, "y": 40, "w": 280, "h": 150},
            "subtitles_area": {"x": 400, "y": 920, "w": 1120, "h": 120}
        }

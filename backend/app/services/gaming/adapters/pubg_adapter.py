from typing import Dict, List, Any
from .base_adapter import BaseGameAdapter

class PUBGAdapter(BaseGameAdapter):
    """
    Adapter for BGMI / PUBG Mobile and PUBG PC Battle Royale:
    Winner Winner Chicken Dinner, airdrop crate, red zone, knockouts,
    squad wipe, sniper headshots, vehicle bridge camp.
    """
    def __init__(self):
        super().__init__(game_id="pubg", display_name="BGMI / PUBG Battle Royale")

    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "combat": [
                "chicken dinner", "winner winner", "knock", "knockout", "squad wipe",
                "awm", "m416", "headshot", "kill", "finish", "spray", "recoil",
                "grenade", "nuke", "pan kill", "sniped", "airdrop", "flare gun"
            ],
            "chase": [
                "buggy", "dacia", "uaz", "bike stunt", "bridge camp", "safe zone",
                "blue zone", "rush", "car chase", "chase", "bhaago zone"
            ],
            "funny": [
                "vehicle explosion", "backflip fail", "pan fight", "snake in grass",
                "campers", "troll", "random squad", "fail", "accident"
            ],
            "clutch": [
                "1v4 clutch", "solo vs squad", "last circle", "revive", "heal battle",
                "survival", "rank 1", "last zone"
            ],
            "reaction": [
                "bhai kya mara", "zero recoil", "hack", "pro player", "scream",
                "let's go chicken dinner", "paisa vasool"
            ]
        }

    def get_hud_profile(self) -> Dict[str, Any]:
        return {
            "alive_counter": {"x": 1600, "y": 30, "w": 280, "h": 70},
            "kill_counter": {"x": 1600, "y": 100, "w": 280, "h": 60},
            "radar": {"x": 1600, "y": 20, "w": 300, "h": 300},
            "health_bar": {"x": 760, "y": 1020, "w": 400, "h": 40}
        }

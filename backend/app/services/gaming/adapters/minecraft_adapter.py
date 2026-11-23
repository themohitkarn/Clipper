from typing import Dict, List, Any
from .base_adapter import BaseGameAdapter

class MinecraftAdapter(BaseGameAdapter):
    """
    Adapter for Minecraft (Survival, Hardcore, Speedruns, SMP):
    Creeper jumpscare/explosion, MLG water bucket clutch, diamonds find,
    falling in lava, Nether bastion, Ender Dragon, warden, raid victory.
    """
    def __init__(self):
        super().__init__(game_id="minecraft", display_name="Minecraft")

    def get_keywords(self) -> Dict[str, List[str]]:
        return {
            "funny": [
                "creeper", "hiss", "aw man", "tnt", "boom", "skeleton", "zombie",
                "lava", "fell into lava", "died", "death message", "hardcore lost",
                "void", "suffocation", "iron golem", "accident", "fail"
            ],
            "clutch": [
                "water bucket", "mlg bucket", "clutch", "hay bale", "ender pearl clutch",
                "survived half heart", "totem", "totem of undying", "safe", "diamond",
                "netherite", "speedrun", "portal", "sub 10"
            ],
            "combat": [
                "ender dragon", "wither", "warden", "crit", "axe crit", "shield",
                "bow shot", "raid", "pillager", "pvp", "sharpness"
            ],
            "chase": [
                "elytra", "firework", "boat jump", "speed bridge", "running away",
                "ravine jump", "parkour", "nether escape"
            ],
            "reaction": [
                "no no no", "my diamonds", "half heart", "screaming", "rage",
                "heartbeat", "omg i survived", "holy mlg"
            ]
        }

    def get_hud_profile(self) -> Dict[str, Any]:
        return {
            "hotbar": {"x": 550, "y": 1000, "w": 820, "h": 70},
            "hearts_food": {"x": 550, "y": 950, "w": 820, "h": 50},
            "subtitles": {"x": 1500, "y": 800, "w": 400, "h": 240}
        }

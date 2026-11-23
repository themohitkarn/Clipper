from typing import Dict, List, Any
from .gta_adapter import GTABaseAdapter

class GTAVAdapter(GTABaseAdapter):
    """
    Adapter specifically optimized for GTA V:
    Los Santos setting, 5-star wanted system, Michael/Franklin/Trevor mechanics,
    heists, online roleplay (GTA RP) and story missions.
    """
    def __init__(self):
        super().__init__(game_id="gta_v", display_name="Grand Theft Auto V")

    def get_keywords(self) -> Dict[str, List[str]]:
        base_kw = super().get_keywords()
        gta_v_specific = {
            "chase": base_kw["chase"] + [
                "los santos", "vinewood", "highway chase", "lspd", "swat", "oppressor",
                "supercar", "zentorno", "chase scene", "police barricade"
            ],
            "combat": base_kw["combat"] + [
                "minigun", "homing launcher", "orbital cannon", "sticky bomb", "railgun",
                "bunker", "military base", "zancudo", "cayo perico"
            ],
            "funny": base_kw["funny"] + [
                "trevor rage", "michael", "franklin", "chop", "ragdoll", "bikers",
                "car launch", "trampoline glitch", "gate glitch"
            ],
            "clutch": base_kw["clutch"] + [
                "pacific standard", "diamond casino", "doomsday heist", "setup passed",
                "elite challenge", "cayo heist solo"
            ],
            "reaction": base_kw["reaction"]
        }
        return gta_v_specific

    def get_hud_profile(self) -> Dict[str, Any]:
        return {
            "radar": {"x": 30, "y": 880, "w": 250, "h": 160},
            "wanted_stars": {"x": 1650, "y": 45, "w": 240, "h": 50},
            "health_armor": {"x": 30, "y": 1045, "w": 250, "h": 20},
            "ammo_weapon": {"x": 1700, "y": 40, "w": 180, "h": 70}
        }

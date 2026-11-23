from typing import Dict, List, Any
from .gta_adapter import GTABaseAdapter

class GTAVIAdapter(GTABaseAdapter):
    """
    Dedicated GTA VI game adapter:
    Vice City / State of Leonida setting, dual protagonists (Lucia & Jason),
    next-gen police AI, social media in-game feeds, neon aesthetics.

    VERIFICATION STATUS:
    Experimental / Forward-Compatible. Full heuristic rules are implemented
    based on official Rockstar releases and reveal trailers. Visual HUD patterns
    are extensible and will be calibrated as retail gameplay footage becomes available.
    """
    def __init__(self):
        super().__init__(game_id="gta_vi", display_name="Grand Theft Auto VI (Leonida / Vice City)")
        self.is_verified_on_retail_footage = False

    def get_keywords(self) -> Dict[str, List[str]]:
        base_kw = super().get_keywords()
        gta_vi_specific = {
            "chase": base_kw["chase"] + [
                "vice city", "leonida", "vice dale", "port gellhorn", "airboat",
                "swamp chase", "highway patrol", "ocean drive", "speedboat", "alligator"
            ],
            "combat": base_kw["combat"] + [
                "lucia", "jason", "convenience store robbery", "duo heist", "bodycam",
                "hostage", "dual wield", "cctv"
            ],
            "funny": base_kw["funny"] + [
                "florida man", "leonida man", "gator in pool", "roof twerk", "mud club",
                "weird npc", "social media live", "livestream fail"
            ],
            "clutch": base_kw["clutch"] + [
                "lucia and jason", "trust", "clean getaway", "store heist passed",
                "border crossing", "safe house"
            ],
            "reaction": base_kw["reaction"] + [
                "gta 6 is real", "next gen graphics", "graphics dekho", "unreal physics"
            ]
        }
        return gta_vi_specific

    def get_hud_profile(self) -> Dict[str, Any]:
        """
        GTA VI modernized HUD layout (independent of GTA V).
        Minimalist bottom-right weapon selector and refined navigation.
        """
        return {
            "radar": {"x": 40, "y": 860, "w": 220, "h": 180},
            "status_feed": {"x": 1500, "y": 850, "w": 380, "h": 200},
            "wanted_indicator": {"x": 1600, "y": 50, "w": 280, "h": 80},
            "social_overlay": {"x": 1400, "y": 200, "w": 480, "h": 680}
        }

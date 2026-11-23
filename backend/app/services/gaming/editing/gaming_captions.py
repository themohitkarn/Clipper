import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ....utils.hinglish import to_hinglish

logger = logging.getLogger(__name__)

# Gaming emoji triggers
GAMING_EMOJI_MAP = {
    r"\bkill\b|\bheadshot\b|\bmar diya\b|\belimination\b": "🎯",
    r"\bwin\b|\bvictory\b|\bchicken dinner\b|\bjeet\b": "🏆",
    r"\bpolice\b|\bcops\b|\bpolice aa gayi\b": "🚓",
    r"\bcar\b|\bgaadi\b|\bvehicle\b|\bspeed\b": "🚗",
    r"\bmoney\b|\bpaisa\b|\bpaise\b|\bheist\b": "💰",
    r"\bexplosion\b|\bbomb\b|\bdhamaka\b|\bblast\b": "💥",
    r"\bfire\b|\baag\b": "🔥",
    r"\bcreeper\b|\btnt\b": "💣",
    r"\bclutch\b|\bace\b": "⚡",
    r"\bgame\b|\bgamer\b": "🎮",
    r"\bwtf\b|\bomg\b|\binsane\b|\bhil gaya\b": "🤯"
}

# 7 Canonical Gaming Caption Templates
# Note: In ASS format, colors are BGR: &H<Alpha><Blue><Green><Red>&
GAMING_STYLE_PRESETS = {
    "gaming_neon": {
        "name": "Gaming Neon",
        "font": "Arial Black",
        "primary": "&H0033FF33&",      # Neon Cyber Green
        "secondary": "&H00FFFF00&",    # Cyan secondary
        "outline_color": "&H00000000&",
        "back_color": "&H80000000&",
        "outline": 4,
        "shadow": 2
    },
    "rgb_cyber": {
        "name": "RGB Cyber",
        "font": "Arial Black",
        "primary": "&H00FF33CC&",      # Neon Purple / Magenta
        "secondary": "&H00FFFF33&",    # Electric Cyan
        "outline_color": "&H00110022&",
        "back_color": "&H80000000&",
        "outline": 4,
        "shadow": 3
    },
    "clean_esports": {
        "name": "Clean Esports",
        "font": "Arial Black",
        "primary": "&H0000D7FF&",      # Esports Gold
        "secondary": "&H00FFFFFF&",    # White
        "outline_color": "&H00000000&",
        "back_color": "&H80000000&",
        "outline": 3,
        "shadow": 1
    },
    "bold_yellow": {
        "name": "Bold Yellow",
        "font": "Arial Black",
        "primary": "&H0000FFFF&",      # Bright Yellow
        "secondary": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "back_color": "&H80000000&",
        "outline": 4,
        "shadow": 2
    },
    "minimal_white": {
        "name": "Minimal White",
        "font": "Arial",
        "primary": "&H00FFFFFF&",      # Pure White
        "secondary": "&H00CCCCCC&",
        "outline_color": "&H00111111&",
        "back_color": "&H60000000&",
        "outline": 3,
        "shadow": 1
    },
    "punchy_red": {
        "name": "Punchy Red",
        "font": "Impact",
        "primary": "&H002222FF&",      # Crimson Impact Red
        "secondary": "&H0000FFFF&",
        "outline_color": "&H00000000&",
        "back_color": "&H80000000&",
        "outline": 4,
        "shadow": 2
    },
    "hindi_gaming_pro": {
        "name": "Hindi Gaming Pro",
        "font": "Arial Black",
        "primary": "&H0014F0FF&",      # Electric Orange / Amber Gold
        "secondary": "&H00FFFFFF&",
        "outline_color": "&H00000000&",
        "back_color": "&H90000000&",
        "outline": 4,
        "shadow": 2
    }
}

class GamingCaptionGenerator:
    """
    Gaming subtitle styling and generation engine.
    Produces SRT, VTT, and ASS files with gamer aesthetics and Hinglish support.
    """
    def __init__(self):
        pass

    def add_gaming_emojis(self, text: str) -> str:
        """Inject gaming emojis on matching action words."""
        result = text
        for pat, emoji in GAMING_EMOJI_MAP.items():
            if re.search(pat, result, flags=re.IGNORECASE):
                result = re.sub(pat, lambda m: f"{m.group(0)} {emoji}", result, count=1, flags=re.IGNORECASE)
        return result

    def format_timestamp_ass(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def generate_gaming_ass(
        self,
        subtitles: List[Dict[str, Any]],
        output_path: Path,
        clip_start_offset: float = 0.0,
        style_preset: str = "gaming_neon",
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        """
        Generate ASS subtitle file tailored for gaming highlights.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cfg = GAMING_STYLE_PRESETS.get(style_preset, GAMING_STYLE_PRESETS["gaming_neon"])

        font_size = 56 if video_height >= 1920 else 32
        margin_v = 240 if video_height >= 1920 else 80

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{cfg['font']},{font_size},{cfg['primary']},{cfg['secondary']},{cfg['outline_color']},{cfg['back_color']},1,0,0,0,100,100,0,0,1,{cfg['outline']},{cfg['shadow']},2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for sub in subtitles:
            start = max(0.0, sub["start"] - clip_start_offset)
            end = max(start + 0.5, sub["end"] - clip_start_offset)
            
            # Convert Hindi to natural Hinglish; leaves English 100% intact
            text = to_hinglish(sub.get("text", "").strip())
            text = self.add_gaming_emojis(text.upper())

            # Break long lines (maximum 2 lines)
            words = text.split()
            if len(words) > 7:
                mid = len(words) // 2
                text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])

            t_start = self.format_timestamp_ass(start)
            t_end = self.format_timestamp_ass(end)
            events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{text}")

        output_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
        return output_path

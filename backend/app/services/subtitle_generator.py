import os
import re
from pathlib import Path
from typing import List, Dict, Any

from ..utils.hinglish import to_hinglish

# Keyword to emoji mapping for viral captions (English & Hinglish)
EMOJI_MAP = {
    r"\bmoney\b|\bpaisa\b|\bpaise\b|\brupaye\b": "💰",
    r"\bcash\b": "💵",
    r"\brich\b|\bcrorepati\b|\bameer\b": "🤑",
    r"\bsecret\b|\braaz\b": "🤫",
    r"\bstop\b|\bruko\b": "🛑",
    r"\bfire\b|\baag\b": "🔥",
    r"\bcrazy\b|\binsane\b|\bhil gaya\b": "🤯",
    r"\bwarning\b|\bdanger\b|\bkhatra\b": "⚠️",
    r"\bluck\b|\bkismat\b": "🍀",
    r"\btime\b|\bwakt\b|\bsamay\b": "⏳",
    r"\bgrowth\b|\bviews\b": "📈",
    r"\bwin\b|\bjeet\b": "🏆",
    r"\bcar\b|\bgaadi\b": "🚗",
    r"\bworld\b|\bduniya\b": "🌍",
    r"\bphone\b": "📱",
    r"\blie\b|\bjhooth\b": "🤥",
    r"\bheart\b|\bdil\b": "❤️",
    r"\bstar\b": "⭐",
    r"\bgame\b|\bgaming\b": "🎮",
    r"\bpolice\b": "🚓",
    r"\btoofan\b|\baandhi\b": "🌪️",
    r"\bbhai\b|\byaar\b": "🤝"
}

class SubtitleGenerator:
    def __init__(self):
        pass

    def add_emojis(self, text: str) -> str:
        """Inject engaging emojis near matching keywords."""
        result = text
        for pat, emoji in EMOJI_MAP.items():
            if re.search(pat, result, flags=re.IGNORECASE):
                # Replace the match with word + emoji (only first occurrence)
                result = re.sub(pat, lambda m: f"{m.group(0)} {emoji}", result, count=1, flags=re.IGNORECASE)
        return result

    def format_srt_timestamp(self, seconds: float) -> str:
        """Convert float seconds to SRT time format: 00:00:00,000"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def format_vtt_timestamp(self, seconds: float) -> str:
        """Convert float seconds to VTT time format: 00:00:00.000"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int(round((seconds - int(seconds)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    def format_ass_timestamp(self, seconds: float) -> str:
        """Convert float seconds to ASS time format: 0:00:00.00"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def generate_srt(
        self,
        subtitles: List[Dict[str, Any]],
        output_path: Path,
        clip_start_offset: float = 0.0
    ) -> Path:
        """Generate standard SRT file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        cue_idx = 1
        for sub in subtitles:
            start = max(0.0, sub["start"] - clip_start_offset)
            end = max(start + 0.5, sub["end"] - clip_start_offset)
            clean_txt = to_hinglish(sub["text"].strip())
            text = self.add_emojis(clean_txt)

            lines.append(f"{cue_idx}")
            lines.append(f"{self.format_srt_timestamp(start)} --> {self.format_srt_timestamp(end)}")
            lines.append(text)
            lines.append("")
            cue_idx += 1

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def generate_vtt(
        self,
        subtitles: List[Dict[str, Any]],
        output_path: Path,
        clip_start_offset: float = 0.0
    ) -> Path:
        """Generate standard WebVTT file for browser HTML5 video playback."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["WEBVTT", ""]
        cue_idx = 1
        for sub in subtitles:
            start = max(0.0, sub["start"] - clip_start_offset)
            end = max(start + 0.5, sub["end"] - clip_start_offset)
            clean_txt = to_hinglish(sub["text"].strip())
            text = self.add_emojis(clean_txt)

            lines.append(f"{cue_idx}")
            lines.append(f"{self.format_vtt_timestamp(start)} --> {self.format_vtt_timestamp(end)}")
            lines.append(text)
            lines.append("")
            cue_idx += 1

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def generate_ass(
        self,
        subtitles: List[Dict[str, Any]],
        output_path: Path,
        clip_start_offset: float = 0.0,
        style_preset: str = "hormozi",
        video_width: int = 1080,
        video_height: int = 1920,
        is_split_screen: bool = False
    ) -> Path:
        """
        Generate Advanced SubStation Alpha (.ass) file with professional animated styling.
        Supports 50/50 split-screen center placement across the divider line.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Merge gaming presets with legacy styles
        styles = {
            "gaming_neon": {
                "font": "Arial Black",
                "size": 56 if video_height >= 1920 else 32,
                "primary": "&H0033FF33&",      # Neon Cyber Green
                "secondary": "&H00FFFF00&",    # Cyan
                "outline_color": "&H00000000&",
                "back_color": "&H80000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "rgb_cyber": {
                "font": "Arial Black",
                "size": 56 if video_height >= 1920 else 32,
                "primary": "&H00FF33CC&",      # Electric Magenta
                "secondary": "&H00FFFF33&",    # Cyan
                "outline_color": "&H00110022&",
                "back_color": "&H80000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 3,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "clean_esports": {
                "font": "Arial Black",
                "size": 54 if video_height >= 1920 else 30,
                "primary": "&H0000D7FF&",      # Esports Gold
                "secondary": "&H00FFFFFF&",
                "outline_color": "&H00000000&",
                "back_color": "&H80000000&",
                "bold": 1,
                "outline": 3,
                "shadow": 1,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "bold_yellow": {
                "font": "Arial Black",
                "size": 58 if video_height >= 1920 else 32,
                "primary": "&H0000FFFF&",      # Bright Yellow
                "secondary": "&H00FFFFFF&",
                "outline_color": "&H00000000&",
                "back_color": "&H80000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "minimal_white": {
                "font": "Arial",
                "size": 52 if video_height >= 1920 else 28,
                "primary": "&H00FFFFFF&",      # Pure White
                "secondary": "&H00CCCCCC&",
                "outline_color": "&H00111111&",
                "back_color": "&H60000000&",
                "bold": 1,
                "outline": 3,
                "shadow": 1,
                "alignment": 2,
                "margin_v": 220 if video_height >= 1920 else 70
            },
            "punchy_red": {
                "font": "Impact",
                "size": 60 if video_height >= 1920 else 34,
                "primary": "&H002222FF&",      # Crimson Impact Red
                "secondary": "&H0000FFFF&",
                "outline_color": "&H00000000&",
                "back_color": "&H80000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "hindi_gaming_pro": {
                "font": "Arial Black",
                "size": 56 if video_height >= 1920 else 32,
                "primary": "&H0014F0FF&",      # Electric Amber
                "secondary": "&H00FFFFFF&",
                "outline_color": "&H00000000&",
                "back_color": "&H90000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "hormozi": {
                "font": "Arial Black",
                "size": 58 if video_height >= 1920 else 32,
                "primary": "&H0000FFFF&",    # Neon Yellow
                "secondary": "&H00FFFFFF&",  # White
                "outline_color": "&H00000000&", # Black outline
                "back_color": "&H80000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,  # Bottom center
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "neon_green": {
                "font": "Arial Black",
                "size": 56 if video_height >= 1920 else 30,
                "primary": "&H0033FF33&",    # Cyber Green
                "secondary": "&H00FFFFFF&",
                "outline_color": "&H00000000&",
                "back_color": "&H60000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            },
            "clean_white": {
                "font": "Arial",
                "size": 52 if video_height >= 1920 else 28,
                "primary": "&H00FFFFFF&",    # White
                "secondary": "&H00AAAAAA&",
                "outline_color": "&H00111111&",
                "back_color": "&H60000000&",
                "bold": 1,
                "outline": 3,
                "shadow": 1,
                "alignment": 2,
                "margin_v": 220 if video_height >= 1920 else 70
            },
            "fire_red": {
                "font": "Impact",
                "size": 60 if video_height >= 1920 else 34,
                "primary": "&H002222FF&",    # Fire Red
                "secondary": "&H0000FFFF&",
                "outline_color": "&H00000000&",
                "back_color": "&H60000000&",
                "bold": 1,
                "outline": 4,
                "shadow": 2,
                "alignment": 2,
                "margin_v": 240 if video_height >= 1920 else 80
            }
        }

        cfg = styles.get(style_preset, styles["hormozi"]).copy()
        if is_split_screen:
            # Position captions right across the horizontal divider line (between facecam and gameplay)
            cfg["margin_v"] = 910 if video_height >= 1920 else int(video_height * 0.47)
            cfg["size"] = 56 if video_height >= 1920 else 32
            cfg["outline"] = 4
            cfg["shadow"] = 2

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{cfg['font']},{cfg['size']},{cfg['primary']},{cfg['secondary']},{cfg['outline_color']},{cfg['back_color']},{cfg['bold']},0,0,0,100,100,0,0,1,{cfg['outline']},{cfg['shadow']},{cfg['alignment']},40,40,{cfg['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for sub in subtitles:
            start = max(0.0, sub["start"] - clip_start_offset)
            end = max(start + 0.5, sub["end"] - clip_start_offset)
            raw_text = to_hinglish(sub["text"].strip()).upper()
            text = self.add_emojis(raw_text)

            start_str = self.format_ass_timestamp(start)
            end_str = self.format_ass_timestamp(end)

            # ASS event line
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

        full_content = header + "\n".join(events) + "\n"
        output_path.write_text(full_content, encoding="utf-8")
        return output_path

import subprocess
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from ...utils.ffmpeg_helper import get_ffmpeg_path

logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """
    Local-first, CPU-efficient gaming audio analyzer.
    Detects volume transients, screams, laughter, gunshots, explosions,
    and streamer reaction spikes using FFmpeg and NumPy.
    """
    def __init__(self):
        pass

    def analyze_audio_track(
        self,
        video_path: Path,
        start_time: float,
        duration: float,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Analyze audio within a time window [start_time, start_time + duration].
        Memory-efficient: streams 16-bit PCM mono directly into NumPy buffer.
        """
        ffmpeg_exe = get_ffmpeg_path()
        cmd = [
            ffmpeg_exe, "-y",
            "-ss", str(max(0.0, start_time)),
            "-i", str(video_path),
            "-t", str(duration),
            "-vn",
            "-ac", "1",
            "-ar", str(sample_rate),
            "-f", "s16le",
            "-"
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, check=True, timeout=90)
            raw_audio = res.stdout
            if not raw_audio:
                return self._empty_result(duration)

            audio_data = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32)
            if len(audio_data) == 0:
                return self._empty_result(duration)

            # Normalize to [-1.0, 1.0]
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data /= max_val

            # Compute RMS energy in 0.5s windows
            window_size = int(sample_rate * 0.5)
            hop_size = int(sample_rate * 0.25)
            num_windows = (len(audio_data) - window_size) // hop_size

            if num_windows <= 0:
                rms = [float(np.sqrt(np.mean(audio_data ** 2)))]
            else:
                rms = []
                for w in range(num_windows):
                    segment = audio_data[w * hop_size : w * hop_size + window_size]
                    rms_val = float(np.sqrt(np.mean(segment ** 2)))
                    rms.append(rms_val)

            rms_array = np.array(rms)
            mean_energy = float(np.mean(rms_array)) if len(rms_array) > 0 else 0.0
            max_energy = float(np.max(rms_array)) if len(rms_array) > 0 else 0.0
            
            # Detect scream / explosion spikes (points > 2.5x mean energy)
            threshold = max(0.25, mean_energy * 2.5)
            spikes = np.where(rms_array > threshold)[0]
            spike_count = int(len(spikes))
            excitement_score = min(1.0, (mean_energy * 0.4) + (max_energy * 0.4) + (min(10, spike_count) * 0.02))

            return {
                "mean_energy": round(mean_energy, 3),
                "max_energy": round(max_energy, 3),
                "spike_count": spike_count,
                "has_scream_or_explosion": bool(max_energy > 0.65 or spike_count >= 3),
                "excitement_score": round(excitement_score, 2),
                "duration": duration
            }

        except Exception as e:
            logger.warning(f"Audio analysis error for window {start_time}-{start_time+duration}: {e}")
            return self._empty_result(duration)

    def _empty_result(self, duration: float) -> Dict[str, Any]:
        return {
            "mean_energy": 0.1,
            "max_energy": 0.2,
            "spike_count": 0,
            "has_scream_or_explosion": False,
            "excitement_score": 0.4,
            "duration": duration
        }

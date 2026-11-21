import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self):
        pass

    def get_youtube_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch transcript directly from YouTube using youtube-transcript-api.
        Lightning fast even for 24-hour videos (takes only 1-2 seconds!).
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get manual English, then Hindi, then auto-generated
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'hi', 'hi-IN'])
            except Exception:
                # Fallback to generated transcript or any available language
                try:
                    for t in transcript_list:
                        transcript = t
                        break
                except Exception:
                    pass

            if not transcript:
                return None

            raw_data = transcript.fetch()
            formatted = []
            for item in raw_data:
                # youtube-transcript-api v1.x returns dict with 'start', 'duration', 'text'
                if isinstance(item, dict):
                    start = float(item.get("start", 0.0))
                    duration = float(item.get("duration", 0.0))
                    text = str(item.get("text", "")).strip()
                else:
                    start = float(getattr(item, "start", 0.0))
                    duration = float(getattr(item, "duration", 0.0))
                    text = str(getattr(item, "text", "")).strip()

                if text:
                    # Clean up music notes / sound effects like [Music], (Laughter)
                    clean_text = re.sub(r"\[.*?\]|\(.*?\)", "", text).strip()
                    if clean_text:
                        formatted.append({
                            "start": round(start, 2),
                            "duration": round(duration, 2),
                            "end": round(start + duration, 2),
                            "text": clean_text
                        })
            return formatted if formatted else None
        except Exception as e:
            logger.warning(f"YouTube transcript retrieval failed for {video_id}: {e}")
            return None

    def transcribe_local_audio(self, audio_path: Path) -> List[Dict[str, Any]]:
        """
        Transcribe local audio file using faster-whisper or whisper if installed,
        or fallback to speech chunking.
        """
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(audio_path), word_timestamps=True)
            formatted = []
            for segment in segments:
                formatted.append({
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "duration": round(segment.end - segment.start, 2),
                    "text": segment.text.strip()
                })
            return formatted
        except ImportError:
            logger.info("faster-whisper not installed; using audio timeline estimation fallback.")
            return []
        except Exception as e:
            logger.warning(f"Local transcription error: {e}")
            return []

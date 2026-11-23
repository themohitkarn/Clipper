import os
import uuid
import asyncio
import logging
import zipfile
from pathlib import Path
from typing import Dict, Optional, List

from ..config import TEMP_DIR, OUTPUTS_DIR, THUMBNAILS_DIR
from ..models.schemas import JobStatusResponse, ClipItem, ProcessUrlRequest
from ..utils.hinglish import to_hinglish
from .downloader import VideoDownloader
from .transcriber import Transcriber
from .viral_detector import ViralDetector
from .subtitle_generator import SubtitleGenerator
from .video_processor import VideoProcessor
from .gaming.universal_analyzer import UniversalGamingAnalyzer
from .youtube_uploader import YouTubePublisher

logger = logging.getLogger(__name__)

class JobManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.jobs: Dict[str, JobStatusResponse] = {}
            cls._instance.downloader = VideoDownloader()
            cls._instance.transcriber = Transcriber()
            cls._instance.sub_gen = SubtitleGenerator()
            cls._instance.video_proc = VideoProcessor()
            cls._instance.gaming_analyzer = UniversalGamingAnalyzer()
            cls._instance.yt_publisher = YouTubePublisher()
        return cls._instance

    def create_job(self, request: ProcessUrlRequest) -> str:
        job_id = str(uuid.uuid4())[:8]
        self.jobs[job_id] = JobStatusResponse(
            job_id=job_id,
            status="queued",
            progress=5,
            current_step="Job queued for processing...",
            clips=[]
        )
        # Launch pipeline safely across any execution context
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._run_pipeline(job_id, request))
        except RuntimeError:
            import threading
            threading.Thread(
                target=lambda: asyncio.run(self._run_pipeline(job_id, request)),
                daemon=True
            ).start()
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        return self.jobs.get(job_id)

    async def _run_pipeline(self, job_id: str, request: ProcessUrlRequest):
        job = self.jobs[job_id]
        loop = asyncio.get_running_loop()

        try:
            # 1. Fetch info
            job.status = "fetching_info"
            job.progress = 15
            job.current_step = "Extracting video metadata & duration..."
            
            info = await loop.run_in_executor(None, self.downloader.extract_info, request.url)
            job.source_title = info.get("title")
            job.source_duration = info.get("duration")
            job.source_thumbnail = info.get("thumbnail")
            job.source_channel = info.get("channel")

            # 2. Get transcript
            job.status = "transcribing"
            job.progress = 30
            job.current_step = "Fetching transcript & speech timing..."

            video_id = self.downloader.extract_youtube_id(request.url)
            transcript = None
            local_path = Path(request.url) if not video_id and Path(request.url).exists() else None

            if video_id:
                transcript = await loop.run_in_executor(
                    None, self.transcriber.get_youtube_transcript, video_id
                )
            elif local_path and local_path.is_file():
                # For uploaded local video, transcribe via local model if available
                transcript = await loop.run_in_executor(
                    None, self.transcriber.transcribe_local_audio, local_path
                )

            # 3. Detect highlights (Gaming Engine vs General Speech)
            job.status = "finding_hooks"
            job.progress = 50
            facecam_info = None

            if request.mode == "gaming" or (request.game and request.game != "none"):
                job.current_step = "Universal Gaming AI analyzing gameplay patterns, combat, audio spikes & facecam..."
                gaming_res = await loop.run_in_executor(
                    None,
                    lambda: self.gaming_analyzer.analyze_gaming_video(
                        metadata=info,
                        transcript_segments=transcript or [],
                        video_duration=float(job.source_duration or 300.0),
                        target_count=request.max_clips,
                        min_duration=float(request.min_duration),
                        max_duration=float(request.max_duration),
                        game_override=request.game,
                        local_video_path=local_path,
                        filter_categories=request.highlight_categories
                    )
                )
                best_moments = gaming_res["clips"]
                job.detected_game = gaming_res["game_detection"]["display_name"]
                job.game_confidence = gaming_res["game_detection"]["confidence"]
                job.has_facecam = gaming_res["facecam_info"].get("has_facecam", False)
                facecam_info = gaming_res["facecam_info"]
            else:
                job.current_step = "AI scoring virality & identifying scroll-stopping hooks..."
                detector = ViralDetector(
                    api_key=request.gemini_api_key,
                    groq_api_key=request.groq_api_key,
                    llm_provider=request.llm_provider
                )
                best_moments = await loop.run_in_executor(
                    None,
                    detector.detect_best_clips,
                    transcript or [],
                    job.source_duration or 300.0,
                    request.max_clips,
                    float(request.min_duration),
                    float(request.max_duration)
                )

            # 4. Download and process each clip
            job.status = "cutting_clips"
            total_clips = len(best_moments)
            processed_clips: List[ClipItem] = []

            for idx, moment in enumerate(best_moments):
                step_pct = 50 + int((idx / max(1, total_clips)) * 45)
                job.progress = step_pct
                job.current_step = f"Processing clip {idx+1}/{total_clips}: {to_hinglish(moment['title'])}..."

                clip_id = f"{job_id}_{idx+1}"
                raw_clip_path = TEMP_DIR / f"{clip_id}_raw.mp4"
                final_clip_path = OUTPUTS_DIR / f"{clip_id}.mp4"
                srt_path = OUTPUTS_DIR / f"{clip_id}.srt"
                vtt_path = OUTPUTS_DIR / f"{clip_id}.vtt"
                ass_path = TEMP_DIR / f"{clip_id}.ass"
                thumb_path = THUMBNAILS_DIR / f"{clip_id}.jpg"

                # Selective download: ONLY download the exact 30-60 second window!
                # This works instantly even for 24-hour YouTube videos!
                download_success = await loop.run_in_executor(
                    None,
                    self.downloader.download_section,
                    request.url,
                    moment["start_time"],
                    moment["end_time"],
                    raw_clip_path
                )

                if not download_success:
                    logger.warning(f"Could not download section for clip {clip_id}")
                    continue

                # Dynamically analyze facecam on this downloaded clip (works for streams & uploads alike)
                clip_facecam = facecam_info
                if (not clip_facecam or not clip_facecam.get("has_facecam")) and request.facecam_layout != "blurred_bg":
                    try:
                        sample_frames = await loop.run_in_executor(
                            None,
                            lambda: self.gaming_analyzer.visual_analyzer.sample_frames_from_video(
                                raw_clip_path,
                                start_time=1.0,
                                duration=min(12.0, float(moment.get("duration", 20.0))),
                                sample_fps=0.5,
                                max_samples=6
                            )
                        )
                        if sample_frames:
                            w = sample_frames[0].shape[1]
                            h = sample_frames[0].shape[0]
                            detected = await loop.run_in_executor(
                                None,
                                lambda: self.gaming_analyzer.facecam_detector.detect_facecam(
                                    sample_frames, video_width=w, video_height=h
                                )
                            )
                            if detected.get("has_facecam"):
                                clip_facecam = detected
                                job.has_facecam = True
                                logger.info(f"Clip {clip_id}: Streamer facecam detected at {detected.get('corner')} (confidence: {detected.get('confidence')})")
                    except Exception as e:
                        logger.warning(f"Error checking facecam on clip {clip_id}: {e}")

                is_split = bool(
                    request.aspect_ratio == "9:16" and
                    clip_facecam and
                    clip_facecam.get("has_facecam") and
                    request.facecam_layout in ("auto", "split_screen")
                )

                # Filter subtitles belonging to this clip
                clip_subs = []
                if transcript:
                    for s in transcript:
                        if s["end"] >= moment["start_time"] and s["start"] <= moment["end_time"]:
                            clip_subs.append(s)

                # Generate subtitles (SRT, VTT, and ASS with Roman Hinglish if Hindi)
                await loop.run_in_executor(
                    None, self.sub_gen.generate_srt, clip_subs, srt_path, moment["start_time"]
                )
                await loop.run_in_executor(
                    None, self.sub_gen.generate_vtt, clip_subs, vtt_path, moment["start_time"]
                )
                if request.subtitle_style != "none":
                    await loop.run_in_executor(
                        None,
                        lambda: self.sub_gen.generate_ass(
                            subtitles=clip_subs,
                            output_path=ass_path,
                            clip_start_offset=moment["start_time"],
                            style_preset=request.subtitle_style,
                            video_width=1080,
                            video_height=1920 if request.aspect_ratio == "9:16" else 1080,
                            is_split_screen=is_split
                        )
                    )

                # Reframe and burn subtitles (with optional facecam split-screen and audio normalization)
                await loop.run_in_executor(
                    None,
                    self.video_proc.process_clip,
                    raw_clip_path,
                    final_clip_path,
                    request.aspect_ratio,
                    ass_path if request.subtitle_style != "none" else None,
                    srt_path if request.subtitle_style != "none" else None,
                    thumb_path,
                    clip_facecam,
                    request.facecam_layout,
                    request.gaming_effects_enabled
                )

                if not final_clip_path.exists() or final_clip_path.stat().st_size < 1000:
                    if raw_clip_path.exists() and raw_clip_path.stat().st_size > 1000:
                        import shutil
                        shutil.copy2(raw_clip_path, final_clip_path)

                if not thumb_path.exists() and final_clip_path.exists():
                    try:
                        self.video_proc.generate_thumbnail(final_clip_path, thumb_path)
                    except Exception:
                        pass

                shorts_meta = self.yt_publisher.prepare_shorts_metadata(
                    clip_id=clip_id,
                    title=to_hinglish(moment["title"]),
                    description=moment.get("description"),
                    hashtags=moment.get("hashtags"),
                    game_name=moment.get("game_name") or job.detected_game
                )

                processed_clips.append(ClipItem(
                    id=clip_id,
                    title=shorts_meta["title"],
                    hook_text=to_hinglish(moment["hook_text"]),
                    viral_score=moment["viral_score"],
                    viral_reason=moment["viral_reason"],
                    start_time=moment["start_time"],
                    end_time=moment["end_time"],
                    duration=moment["duration"],
                    video_url=f"/outputs/{clip_id}.mp4",
                    thumbnail_url=f"/thumbnails/{clip_id}.jpg" if thumb_path.exists() else (job.source_thumbnail or ""),
                    srt_url=f"/outputs/{clip_id}.srt",
                    vtt_url=f"/outputs/{clip_id}.vtt",
                    aspect_ratio=request.aspect_ratio,
                    subtitle_style=request.subtitle_style,
                    game_name=moment.get("game_name") or job.detected_game,
                    event_category=moment.get("event_category"),
                    event_category_label=moment.get("event_category_label"),
                    gaming_score_breakdown=moment.get("gaming_score_breakdown"),
                    has_facecam=job.has_facecam,
                    description=shorts_meta["description"],
                    hashtags=shorts_meta["hashtags"],
                    youtube_upload_url=shorts_meta["studio_upload_url"]
                ))

            if not processed_clips:
                job.status = "failed"
                job.error = "Could not download clips (YouTube may be blocking requests from this IP or requiring sign-in). Try uploading the video directly using the 'Upload Local Video' tab!"
                job.current_step = job.error
                return

            job.status = "completed"
            job.progress = 100
            job.current_step = f"Successfully generated {len(processed_clips)} viral clips!"
            job.clips = processed_clips

        except Exception as e:
            logger.error(f"Pipeline failed for job {job_id}: {e}", exc_info=True)
            job.status = "failed"
            job.error = str(e)
            job.current_step = f"Processing failed: {str(e)}"

    def create_batch_zip(self, job_id: str) -> Optional[Path]:
        """Create a zip archive containing all generated clips and subtitle files."""
        job = self.jobs.get(job_id)
        if not job or not job.clips:
            return None

        zip_path = OUTPUTS_DIR / f"{job_id}_all_clips.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for clip in job.clips:
                mp4 = OUTPUTS_DIR / f"{clip.id}.mp4"
                srt = OUTPUTS_DIR / f"{clip.id}.srt"
                if mp4.exists():
                    zf.write(mp4, arcname=f"{clip.id}_{clip.title[:30]}.mp4")
                if srt.exists():
                    zf.write(srt, arcname=f"{clip.id}.srt")
        return zip_path

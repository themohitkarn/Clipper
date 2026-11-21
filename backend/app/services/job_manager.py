import os
import uuid
import asyncio
import logging
import zipfile
from pathlib import Path
from typing import Dict, Optional, List

from ..config import TEMP_DIR, OUTPUTS_DIR, THUMBNAILS_DIR
from ..models.schemas import JobStatusResponse, ClipItem, ProcessUrlRequest
from .downloader import VideoDownloader
from .transcriber import Transcriber
from .viral_detector import ViralDetector
from .subtitle_generator import SubtitleGenerator
from .video_processor import VideoProcessor

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
        # Launch pipeline in background asyncio task
        asyncio.create_task(self._run_pipeline(job_id, request))
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
            if video_id:
                transcript = await loop.run_in_executor(
                    None, self.transcriber.get_youtube_transcript, video_id
                )

            # 3. Detect viral clips
            job.status = "finding_hooks"
            job.progress = 50
            job.current_step = "AI scoring virality & identifying scroll-stopping hooks..."

            detector = ViralDetector(api_key=request.gemini_api_key)
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
                job.current_step = f"Processing clip {idx+1}/{total_clips}: {moment['title']}..."

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

                # Filter subtitles belonging to this clip
                clip_subs = []
                if transcript:
                    for s in transcript:
                        if s["end"] >= moment["start_time"] and s["start"] <= moment["end_time"]:
                            clip_subs.append(s)

                # Generate subtitles
                await loop.run_in_executor(
                    None, self.sub_gen.generate_srt, clip_subs, srt_path, moment["start_time"]
                )
                await loop.run_in_executor(
                    None, self.sub_gen.generate_vtt, clip_subs, vtt_path, moment["start_time"]
                )
                if request.subtitle_style != "none":
                    await loop.run_in_executor(
                        None,
                        self.sub_gen.generate_ass,
                        clip_subs,
                        ass_path,
                        moment["start_time"],
                        request.subtitle_style,
                        1080,
                        1920 if request.aspect_ratio == "9:16" else 1080
                    )

                # Reframe and burn subtitles
                await loop.run_in_executor(
                    None,
                    self.video_proc.process_clip,
                    raw_clip_path,
                    final_clip_path,
                    request.aspect_ratio,
                    ass_path if request.subtitle_style != "none" else None,
                    srt_path if request.subtitle_style != "none" else None,
                    thumb_path
                )

                processed_clips.append(ClipItem(
                    id=clip_id,
                    title=moment["title"],
                    hook_text=moment["hook_text"],
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
                    subtitle_style=request.subtitle_style
                ))

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

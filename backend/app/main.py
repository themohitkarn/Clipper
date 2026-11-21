import os
import shutil
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional

from .config import OUTPUTS_DIR, THUMBNAILS_DIR, TEMP_DIR, HOST, PORT
from .models.schemas import ProcessUrlRequest, JobStatusResponse
from .services.job_manager import JobManager
from .utils.ffmpeg_helper import find_system_ffmpeg, get_media_info

app = FastAPI(
    title="Clipper AI API",
    description="Automated AI Video Highlights and Clipping Platform",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directories for generated video clips and thumbnails
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/thumbnails", StaticFiles(directory=str(THUMBNAILS_DIR)), name="thumbnails")

job_manager = JobManager()

@app.get("/api/health")
def health_check():
    ffmpeg, ffprobe = find_system_ffmpeg()
    return {
        "status": "healthy",
        "ffmpeg_available": bool(ffmpeg),
        "ffmpeg_path": ffmpeg,
        "ffprobe_path": ffprobe
    }

@app.get("/api/system")
def system_status():
    ffmpeg, _ = find_system_ffmpeg()
    return {
        "ready": bool(ffmpeg),
        "ffmpeg_installed": bool(ffmpeg),
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "features": [
            "Smart 24-Hour Video Selective Clipping",
            "Auto Hook & Virality Scoring (0-100)",
            "Dynamic Alex Hormozi & Neon Captions",
            "Aspect Ratio Reframe (9:16 Vertical, 1:1, 16:9)",
            "One-Click Batch ZIP Export",
            "100% Free / No Subscription Required"
        ]
    }

@app.post("/api/process", response_model=dict)
def process_url(request: ProcessUrlRequest):
    """Start clipping job from YouTube URL."""
    if not request.url or ("youtube.com" not in request.url and "youtu.be" not in request.url):
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube video URL.")

    job_id = job_manager.create_job(request)
    return {"job_id": job_id, "status": "queued", "message": "Processing started"}

@app.post("/api/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    aspect_ratio: str = Form("9:16"),
    subtitle_style: str = Form("hormozi"),
    min_duration: int = Form(20),
    max_duration: int = Form(60),
    max_clips: int = Form(5),
    gemini_api_key: Optional[str] = Form(None)
):
    """Upload local video file and process clips."""
    upload_id = str(uuid.uuid4())[:8]
    save_path = TEMP_DIR / f"{upload_id}_{file.filename}"
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    request = ProcessUrlRequest(
        url=str(save_path),
        aspect_ratio=aspect_ratio,
        subtitle_style=subtitle_style,
        min_duration=min_duration,
        max_duration=max_duration,
        max_clips=max_clips,
        gemini_api_key=gemini_api_key
    )
    job_id = job_manager.create_job(request)
    return {"job_id": job_id, "status": "queued", "message": "File uploaded and processing"}

@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """Server-Sent Events (SSE) for real-time progress updates."""
    async def event_generator():
        while True:
            job = job_manager.get_job(job_id)
            if not job:
                yield "data: {\"error\": \"Job not found\"}\n\n"
                break

            data = job.model_dump_json()
            yield f"data: {data}\n\n"

            if job.status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/jobs/{job_id}/download-zip")
def download_all_zip(job_id: str):
    zip_path = job_manager.create_batch_zip(job_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip file could not be created or no clips exist.")
    return FileResponse(
        path=str(zip_path),
        filename=f"clipper_clips_{job_id}.zip",
        media_type="application/zip"
    )

# Serve built frontend if dist exists
dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

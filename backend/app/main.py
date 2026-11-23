import os
import uuid
import shutil
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional

from .config import OUTPUTS_DIR, THUMBNAILS_DIR, TEMP_DIR, HOST, PORT, GROQ_API_KEY, GEMINI_API_KEY, OLLAMA_BASE_URL
from .models.schemas import (
    ProcessUrlRequest, JobStatusResponse, GameDetectRequest, GameDetectResponse,
    YouTubeUploadRequest, YouTubeUploadResponse
)
from .services.job_manager import JobManager
from .services.youtube_uploader import YouTubePublisher
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
youtube_publisher = YouTubePublisher()

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
    import shutil
    total, used, free = shutil.disk_usage(TEMP_DIR)
    free_gb = round(free / (1024 ** 3), 1)
    
    # Check yt-dlp availability
    from .services.downloader import VideoDownloader
    dl = VideoDownloader()
    cmd = dl._get_ytdlp_cmd()

    # Check Ollama availability
    import requests
    ollama_ready = False
    try:
        res = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=0.5)
        ollama_ready = (res.status_code == 200)
    except Exception:
        pass
    
    return {
        "ready": bool(ffmpeg),
        "ffmpeg_installed": bool(ffmpeg),
        "ffmpeg_available": bool(ffmpeg),
        "ffmpeg_path": ffmpeg,
        "ytdlp_available": bool(cmd),
        "temp_disk_free_gb": free_gb,
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "groq_api_configured": bool(os.getenv("GROQ_API_KEY")),
        "ollama_available": ollama_ready,
        "youtube_api_configured": youtube_publisher.is_api_configured(),
        "features": [
            "Smart 24-Hour Video Selective Clipping",
            "Auto Hook & Virality Scoring (0-100)",
            "Groq (Llama 3.3) & Gemini Free LLMs",
            "1-Click YouTube Shorts Publisher",
            "Dynamic Alex Hormozi & Neon Captions",
            "Aspect Ratio Reframe (9:16 Vertical, 1:1, 16:9)",
            "One-Click Batch ZIP Export",
            "100% Free / No Subscription Required"
        ]
    }

@app.post("/api/process", response_model=dict)
@app.post("/api/process-url", response_model=dict)
async def process_url(request: ProcessUrlRequest):
    """Start clipping job from YouTube URL."""
    if not request.url or ("youtube.com" not in request.url and "youtu.be" not in request.url):
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube video URL.")

    job_id = job_manager.create_job(request)
    return {"job_id": job_id, "status": "queued", "message": "Processing started"}

@app.post("/api/upload", response_model=dict)
async def upload_video(
    file: UploadFile = File(...),
    mode: str = Form("gaming"),
    game: str = Form("auto"),
    aspect_ratio: str = Form("9:16"),
    subtitle_style: str = Form("gaming_neon"),
    min_duration: int = Form(20),
    max_duration: int = Form(60),
    max_clips: int = Form(10),
    facecam_layout: str = Form("auto"),
    gaming_effects_enabled: bool = Form(True),
    highlight_categories: Optional[str] = Form(None),
    gemini_api_key: Optional[str] = Form(None),
    groq_api_key: Optional[str] = Form(None),
    llm_provider: str = Form("auto")
):
    """Upload local video file and process clips."""
    upload_id = str(uuid.uuid4())[:8]
    save_path = TEMP_DIR / f"{upload_id}_{file.filename}"
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    categories_list = [c.strip() for c in highlight_categories.split(",")] if highlight_categories else None

    request = ProcessUrlRequest(
        url=str(save_path),
        mode=mode,
        game=game,
        aspect_ratio=aspect_ratio,
        subtitle_style=subtitle_style,
        min_duration=min_duration,
        max_duration=max_duration,
        max_clips=max_clips,
        highlight_categories=categories_list,
        facecam_layout=facecam_layout,
        gaming_effects_enabled=gaming_effects_enabled,
        gemini_api_key=gemini_api_key,
        groq_api_key=groq_api_key,
        llm_provider=llm_provider
    )
    job_id = job_manager.create_job(request)
    return {"job_id": job_id, "status": "queued", "message": "File uploaded and processing"}

@app.post("/api/gaming/detect-game", response_model=GameDetectResponse)
async def detect_game_endpoint(req: GameDetectRequest):
    """Quickly probe and detect the video game before full clipping."""
    try:
        from .services.downloader import VideoDownloader
        from .services.transcriber import Transcriber
        from .services.gaming.game_detector import GameDetector

        dl = VideoDownloader()
        meta = dl.extract_info(req.url)
        vid_id = dl.extract_youtube_id(req.url)
        transcript_sample = ""
        if vid_id:
            subs = Transcriber().get_youtube_transcript(vid_id)
            if subs:
                transcript_sample = " ".join([s["text"] for s in subs[:60]])

        detector = GameDetector()
        res = detector.detect_game(metadata=meta, transcript_sample=transcript_sample)
        return GameDetectResponse(**res)
    except Exception as e:
        return GameDetectResponse(
            game_id="generic",
            display_name="Universal Gameplay Engine",
            confidence=0.50,
            is_generic=True,
            is_verified=True,
            scores={"generic": 0.50}
        )

@app.get("/api/gaming/supported-games")
def get_supported_games():
    """List supported game adapters and verification status."""
    return [
        {"id": "auto", "name": "Auto Detect Game (AI Vision + HUD)", "verified": True},
        {"id": "gta_v", "name": "Grand Theft Auto V", "verified": True},
        {"id": "gta_vi", "name": "Grand Theft Auto VI (Leonida / Vice City)", "verified": False, "note": "Experimental heuristics until retail launch"},
        {"id": "valorant", "name": "Valorant (Tactical FPS)", "verified": True},
        {"id": "pubg", "name": "BGMI / PUBG Mobile & PC", "verified": True},
        {"id": "minecraft", "name": "Minecraft (Survival & Creative)", "verified": True},
        {"id": "generic", "name": "Universal Gameplay Engine (CS2, Apex, Fortnite, Free Fire, Roblox, etc.)", "verified": True}
    ]

@app.get("/api/gaming/subtitle-presets")
def get_subtitle_presets():
    """List 7 high-retention gaming subtitle presets."""
    return [
        {"id": "gaming_neon", "name": "Gaming Neon Green", "color": "#33FF33", "recommended_for": "General Gaming & GTA"},
        {"id": "rgb_cyber", "name": "RGB Cyber Magenta", "color": "#FF33CC", "recommended_for": "Cyberpunk & Streamers"},
        {"id": "clean_esports", "name": "Clean Esports Gold", "color": "#00D7FF", "recommended_for": "Valorant & CS2"},
        {"id": "bold_yellow", "name": "Bold Yellow Hormozi", "color": "#00FFFF", "recommended_for": "High Retention Shorts"},
        {"id": "minimal_white", "name": "Minimal Clean White", "color": "#FFFFFF", "recommended_for": "Story & Longplay"},
        {"id": "punchy_red", "name": "Punchy Red Impact 🔥", "color": "#FF2222", "recommended_for": "Rage & Close Calls"},
        {"id": "hindi_gaming_pro", "name": "Hindi Gaming Pro (Hinglish)", "color": "#33CCFF", "recommended_for": "Indian Gaming Creators"}
    ]

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

@app.get("/api/youtube/status")
def get_youtube_status():
    """Check YouTube API integration status."""
    return {
        "api_configured": youtube_publisher.is_api_configured(),
        "studio_upload_url": "https://studio.youtube.com/channel/UC/videos/upload?d=hd",
        "web_upload_url": "https://www.youtube.com/upload",
        "instructions": "Place your Google Cloud client_secret.json in data/ directory for direct automated uploading, or use 1-Click Studio Upload!"
    }

@app.post("/api/youtube/prepare-upload")
def prepare_youtube_upload(clip_id: str, title: Optional[str] = None, description: Optional[str] = None):
    """Generate YouTube Shorts metadata and Studio upload intent for a clip."""
    meta = youtube_publisher.prepare_shorts_metadata(
        clip_id=clip_id,
        title=title or "Viral Highlight Clip",
        description=description
    )
    return meta

@app.post("/api/youtube/upload", response_model=YouTubeUploadResponse)
def upload_clip_to_youtube(req: YouTubeUploadRequest):
    """Directly upload a generated MP4 clip to YouTube Shorts."""
    clip_file = OUTPUTS_DIR / f"{req.clip_id}.mp4"
    if not clip_file.exists():
        raise HTTPException(status_code=404, detail=f"Clip {req.clip_id} MP4 file not found.")

    res = youtube_publisher.upload_via_api(
        video_path=clip_file,
        title=req.title or f"Viral Clip #{req.clip_id}",
        description=req.description or "Watch till the end! #Shorts",
        tags=req.tags or ["Shorts", "Gaming", "Viral"],
        privacy_status=req.privacy_status
    )
    return YouTubeUploadResponse(**res)

# Serve built frontend if dist exists
dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

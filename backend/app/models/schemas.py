from pydantic import BaseModel, Field
from typing import List, Optional

class ProcessUrlRequest(BaseModel):
    url: str
    aspect_ratio: str = Field(default="9:16", description="Target aspect ratio: 9:16, 1:1, or 16:9")
    subtitle_style: str = Field(default="hormozi", description="hormozi, neon_green, clean_white, fire_red, or none")
    min_duration: int = Field(default=20, ge=10, le=120)
    max_duration: int = Field(default=60, ge=15, le=180)
    max_clips: int = Field(default=5, ge=1, le=20)
    gemini_api_key: Optional[str] = None

class ClipItem(BaseModel):
    id: str
    title: str
    hook_text: str
    viral_score: int
    viral_reason: str
    start_time: float
    end_time: float
    duration: float
    video_url: str
    thumbnail_url: str
    srt_url: str
    vtt_url: str
    aspect_ratio: str
    subtitle_style: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "fetching_info", "transcribing", "finding_hooks", "cutting_clips", "generating_subtitles", "completed", "failed"
    progress: int  # 0 to 100
    current_step: str
    source_title: Optional[str] = None
    source_duration: Optional[float] = None
    source_thumbnail: Optional[str] = None
    source_channel: Optional[str] = None
    clips: List[ClipItem] = []
    error: Optional[str] = None

class ReRenderClipRequest(BaseModel):
    aspect_ratio: Optional[str] = None
    subtitle_style: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

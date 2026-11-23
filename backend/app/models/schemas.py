from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProcessUrlRequest(BaseModel):
    url: str
    mode: str = Field(default="gaming", description="'gaming' or 'general'")
    game: str = Field(default="auto", description="Game selector: auto, gta_v, gta_vi, valorant, pubg, minecraft, generic")
    aspect_ratio: str = Field(default="9:16", description="Target aspect ratio: 9:16, 1:1, or 16:9")
    subtitle_style: str = Field(default="gaming_neon", description="gaming_neon, rgb_cyber, clean_esports, bold_yellow, minimal_white, punchy_red, hindi_gaming_pro, hormozi, none")
    min_duration: int = Field(default=20, ge=10, le=180)
    max_duration: int = Field(default=60, ge=15, le=300)
    max_clips: int = Field(default=10, ge=1, le=100)
    highlight_categories: Optional[List[str]] = Field(default=None, description="e.g. ['combat_action', 'chase_stunt', 'clutch_win', 'funny_fail', 'commentary_reaction']")
    facecam_layout: str = Field(default="auto", description="auto, split_screen, gameplay_only")
    gaming_effects_enabled: bool = Field(default=True)
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    llm_provider: Optional[str] = Field(default="auto", description="auto, groq, gemini, ollama, heuristic")

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
    game_name: Optional[str] = None
    event_category: Optional[str] = None
    event_category_label: Optional[str] = None
    gaming_score_breakdown: Optional[Dict[str, int]] = None
    has_facecam: Optional[bool] = None
    description: Optional[str] = None
    hashtags: Optional[List[str]] = None
    youtube_upload_url: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "fetching_info", "transcribing", "finding_hooks", "cutting_clips", "generating_subtitles", "completed", "failed"
    progress: int  # 0 to 100
    current_step: str
    source_title: Optional[str] = None
    source_duration: Optional[float] = None
    source_thumbnail: Optional[str] = None
    source_channel: Optional[str] = None
    mode: Optional[str] = "gaming"
    detected_game: Optional[str] = None
    game_confidence: Optional[float] = None
    has_facecam: Optional[bool] = None
    clips: List[ClipItem] = []
    error: Optional[str] = None

class ReRenderClipRequest(BaseModel):
    aspect_ratio: Optional[str] = None
    subtitle_style: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class GameDetectRequest(BaseModel):
    url: str

class GameDetectResponse(BaseModel):
    game_id: str
    display_name: str
    confidence: float
    is_generic: bool
    is_verified: bool
    scores: Dict[str, float]

class YouTubeUploadRequest(BaseModel):
    clip_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy_status: str = Field(default="unlisted", description="private, unlisted, public")

class YouTubeUploadResponse(BaseModel):
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    studio_url: Optional[str] = None
    message: str

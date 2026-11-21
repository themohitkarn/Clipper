import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = DATA_DIR / "temp"
OUTPUTS_DIR = DATA_DIR / "outputs"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

# Ensure all directories exist
for directory in [DATA_DIR, TEMP_DIR, OUTPUTS_DIR, THUMBNAILS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Processing Defaults
DEFAULT_MAX_CLIPS = 5
DEFAULT_MIN_CLIP_DURATION = 20  # seconds
DEFAULT_MAX_CLIP_DURATION = 60  # seconds
DEFAULT_ASPECT_RATIO = "9:16"  # "9:16" (vertical), "1:1" (square), "16:9" (horizontal)
DEFAULT_SUBTITLE_STYLE = "hormozi"  # "hormozi", "neon_green", "clean_white", "fire_red", "none"

# ⚡ Clipper AI — Free Automated Viral Video Clipper

**Open-source, 100% free alternative to Opus Clip, Munch, Klap & Vizard.**  
Turn **10-minute clips or 24-hour long livestreams** into ranked, caption-burned, vertical 9:16 viral shorts, reels, and TikToks with zero subscription fees and no watermarks.

---

## 🚀 Key Features

- **⚡ 24+ Hour Video Support Without Gigabyte Downloads**:
  Naively downloading a 24-hour YouTube video takes 30-50 GB of storage and hours of time. **Clipper AI solves this with Selective Range Streaming**:
  1. Instantly fetches the video transcript and metadata in seconds via `youtube-transcript-api`.
  2. Ranks all viral moments across the full 24-hour timeline.
  3. Uses `yt-dlp` selective streaming (`--download-sections "*start-end"`) to download **only the exact 45-60 second clips**!
  4. Saves 99% bandwidth and disk space, turning a multi-hour headache into a 30-second operation.
- **🔥 AI Hook & Virality Scoring (0 to 100)**:
  - Detects curiosity gaps, emotional triggers, storytelling arcs, questions, and punchlines in the opening 3-5 seconds.
  - Automatically generates catchy, click-worthy titles with emojis (e.g., *"The Secret Nobody Talks About 🤫"*).
  - Provides a strategy breakdown explaining *"Why this clip works"* on algorithms.
  - Works **100% Free and Offline** via built-in Natural Language Heuristics, or with free-tier **Google Gemini 2.5 Flash**!
- **📱 9:16 Vertical Video Reframe (Podcast & Stream Standard)**:
  - Transforms standard 16:9 landscape videos into sleek 9:16 vertical shorts.
  - Dynamic blurred background + centered crisp video overlay (the exact professional look used by top podcasters like Joe Rogan, Lex Fridman, Alex Hormozi).
  - Also supports **1:1 Square** (Instagram Feed/LinkedIn) and **16:9 Landscape** formats.
- **💬 Alex Hormozi Style Animated Subtitles**:
  - Word-level synchronized captions with bright yellow/neon highlights on active words.
  - Automatic contextual emoji injection (e.g. 💰 money, 🛑 stop, 🔥 fire, 🤯 crazy, 🚗 car).
  - Multiple aesthetic presets: *Alex Hormozi Yellow*, *Neon Cyber Green*, *Clean Minimalist White*, and *Fire Red Punchy*.
  - Burned directly into the MP4 and also exported as clean `.srt` and `.vtt` files.
- **📦 One-Click Batch ZIP Export**:
  - Download individual clips or download all generated clips with subtitles as a single `.zip` file.
  - One-click "Copy Caption & Hashtags" for rapid publishing to YouTube Shorts, TikTok, and Instagram Reels.
- **💸 100% Free Forever**:
  - No monthly credits, no watermarks, no sign-up gates, no paid API requirement.

---

## 🛠️ Architecture & How It Works

```
┌────────────────────────────────────────────────────────┐
│                      CLIPPER AI                        │
└────────────────────────────────────────────────────────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
  YouTube URL                              File Upload
(10m to 24+ Hours)                     (MP4, MOV, MKV, WebM)
       │                                       │
       ▼                                       ▼
1. Metadata & Subtitles Extraction        1. Probing & Audio Extract
   (youtube-transcript-api in 2s)            (FFmpeg 16kHz Stream)
       │                                       │
       └───────────────────┬───────────────────┘
                           │
                           ▼
          2. Topic Chunking & Hook Detection
        (Cohere into 20s - 60s narrative blocks)
                           │
                           ▼
          3. AI Virality Scoring Engine (0-100)
             ├─ Mode A: Gemini Flash API (Free Tier)
             └─ Mode B: Smart Heuristic (100% Offline Free)
                           │
                           ▼
          4. Selective Download & Slicing
       (Downloads ONLY the 60s windows via yt-dlp)
                           │
                           ▼
          5. Animated Subtitle Generation
             ├─ .ass (Alex Hormozi / Neon style)
             ├─ .srt (SubRip)
             └─ .vtt (WebVTT for HTML5 player)
                           │
                           ▼
          6. FFmpeg Reframe & Burn
        (9:16 Blurred Background + Overlay)
                           │
                           ▼
          7. Interactive Web Dashboard
    (Preview Player, Trimmer, MP4 & Batch ZIP Download)
```

---

## 💻 Installation & Running

### Prerequisites
- **Python**: 3.10 or 3.11
- **FFmpeg**: Full build with `libass` and `libx264`

#### Installing FFmpeg:
- **Windows**:
  ```powershell
  winget install Gyan.FFmpeg
  ```
  *(Or place `ffmpeg.exe` and `ffprobe.exe` directly into the `bin/` directory)*
- **macOS**:
  ```bash
  brew install ffmpeg
  ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```

---

### Quick Start (1-Click Run)

1. **Clone this repository**:
   ```bash
   git clone https://github.com/themohitkarn/Clipper.git
   cd Clipper
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Clipper**:
   - On Windows: Double-click `start.bat` or run:
     ```bash
     python run.py
     ```
   - On Mac / Linux:
     ```bash
     python run.py
     ```

4. Open your browser at **`http://localhost:8000`** — paste any YouTube link or upload a video and enjoy free automated clips!

---

## 🔑 Optional: Free Google AI Studio API Key
Clipper AI works **100% free and offline without any API key** using its built-in Natural Language Heuristic engine.

If you want extra deep LLM scoring, you can get a 100% free API key from [Google AI Studio](https://aistudio.google.com/apikey) (free tier includes 15 RPM / 1M TPM) and set it in your environment:
```bash
set GEMINI_API_KEY=your_free_key_here
```
Or simply paste it in the **Settings** drawer in the web dashboard!

---

## 📁 Repository Structure

```
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI server & endpoints
│       ├── config.py                # System paths & configuration
│       ├── models/
│       │   └── schemas.py           # Pydantic data schemas
│       ├── services/
│       │   ├── downloader.py        # 24-hr selective range streamer (yt-dlp)
│       │   ├── transcriber.py       # Instant YouTube & local transcript engine
│       │   ├── viral_detector.py    # Virality scorer (Gemini + Offline Heuristic)
│       │   ├── subtitle_generator.py# Hormozi animated ASS/SRT/VTT generator
│       │   ├── video_processor.py   # FFmpeg 9:16 blurred reframe & burn
│       │   └── job_manager.py       # Async background queue & SSE progress
│       └── utils/
│           └── ffmpeg_helper.py     # FFmpeg/FFprobe locator & wrappers
├── frontend/
│   └── dist/
│       └── index.html               # Complete modern React 18 + Tailwind SPA
├── data/
│   ├── temp/                        # Temporary clip working files
│   ├── outputs/                     # Rendered MP4s and subtitle files
│   └── thumbnails/                  # Clip preview card posters
├── bin/                             # Portable binaries directory (optional)
├── run.py                           # Single Python runner script
├── start.bat                        # Windows 1-click launcher
├── requirements.txt                 # Python dependencies
└── README.md                        # Documentation
```

---

## 📄 License

MIT License — free for personal, commercial, and open-source use.
Created for **[themohitkarn/Clipper](https://github.com/themohitkarn/Clipper)**.

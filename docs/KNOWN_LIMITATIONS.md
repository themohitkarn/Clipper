# Clipper AI — Known Technical Limitations & Constraints

This document outlines the real-world operational constraints, external dependencies, and technical boundaries of Clipper AI.

---

## 1. YouTube Bot Detection & Rate Limiting (HTTP 429)

### The Challenge
YouTube continuously tightens bot detection algorithms. When issuing repeated requests for video streams or metadata, YouTube servers may respond with `HTTP 429: Too Many Requests`, `Sign in to confirm you're not a bot`, or temporarily throttle the host IP address.

### Current Mitigation in Clipper
- Metadata extraction is deferred until user request and executed via `--skip-download` to avoid triggering heavy traffic flags.
- Section downloading requests only specific byte ranges rather than full video payloads.
- If automated section downloading is throttled, Clipper falls back to direct media stream slicing via FFmpeg.

### Recommended Production Workaround
- Users encountering persistent bot challenges can supply their browser session cookies to `yt-dlp` using `--cookies-from-browser chrome` or by exporting a `cookies.txt` file to the Clipper root folder.

---

## 2. Heuristic Scoring vs. Actual Viral Probability

### Important Distinction
Clipper incorporates a Natural Language Heuristic Engine that scores potential clips between 50 and 99. These scores reflect the presence of established high-retention conversational patterns:
- First-5-words scroll-stopping hook words (`why`, `how to`, `secret`, `mistake`, `never`, `don't`).
- Curiosity question openers (`what if`, `have you ever`, `did you know`).
- High-intensity emotional trigger words (`money`, `rich`, `fail`, `insane`, `exposed`).
- Pacing and duration sweet spot (25–50 seconds).

### What Heuristic Scoring Cannot Guarantee
- **A score of 95/100 does not guarantee algorithmic virality or millions of views.**
- Real social media performance depends heavily on external factors outside the text transcript:
  1. Creator visual charisma, energy, and facial expressions.
  2. Audio mixing, background music, and sound design.
  3. Video thumbnail and post title.
  4. Platform algorithm changes and audience interest.

---

## 3. Videos with Disabled or Missing Captions

### The Challenge
When a YouTube video creator explicitly disables captions and YouTube has not generated automated subtitles, `youtube-transcript-api` cannot extract timestamped text.

### Current Mitigation in Clipper
- The pipeline detects the missing transcript within 3.0 seconds and smoothly transitions to **Timeline Spacing Fallback Mode**.
- In fallback mode, Clipper spaces candidate highlights evenly across the video duration (e.g. at 20%, 40%, 60%, 80% mark), allowing the user to preview and export clips even without text.

### CPU Speech-to-Text Constraints
- While local Whisper models (`faster-whisper`) can transcribe local audio files, transcribing a full **24-hour video** on a consumer CPU would require **4 to 8 hours** of continuous CPU computation.
- For multi-hour streams without captions, timeline fallback remains the recommended instantaneous zero-cost approach.

---

## 4. Host Security Policies & Windows AppLocker

### The Challenge
Corporate and restricted Windows operating systems enforce Windows Application Control (AppLocker) policies. These policies:
- Block unsigned standalone `.exe` binaries placed in user folders (e.g., `bin/yt-dlp.exe`).
- Block native C++ Node binaries (such as `rollup-win32-x64-msvc.node` when attempting local Vite build bundling).

### How Clipper Solves This
- **Python Module Execution:** Rather than running standalone `.exe` binaries, Clipper queries `[sys.executable, "-m", "yt_dlp"]` using the approved system Python interpreter.
- **Standalone ESM Architecture:** The frontend production build (`frontend/dist/index.html`) runs directly in modern browsers via native ES Modules (React 18, Tailwind, Lucide), completely eliminating the need for local Node native build steps during deployment.

---

## 5. Temporary Disk Space Management

- Each clipped 30–60 second video requires approximately 2 MB to 5 MB of temporary storage during processing.
- The `data/temp` directory stores intermediate raw cuts and `.ass` scripts.
- To prevent storage exhaustion on high-volume servers, a periodic cleanup job or manual clearing of `data/temp` is recommended after batch exports.

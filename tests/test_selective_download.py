import os
import sys
import time
import json
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.transcriber import Transcriber
from backend.app.services.downloader import VideoDownloader
from backend.app.config import TEMP_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_selective_download_audit():
    print("=" * 60)
    print("AUDIT SECTION 3: SELECTIVE DOWNLOADING BENCHMARKS")
    print("=" * 60)

    transcriber = Transcriber()
    downloader = VideoDownloader()

    results = {
        "transcripts": {},
        "section_downloads": {},
        "summary": {}
    }

    # 1. Transcript Retrieval Tests
    test_videos = [
        {"id": "dQw4w9WgXcQ", "type": "English (Music/Pop)", "lang": "en"},
        {"id": "jNQXAC9IVRw", "type": "First YouTube Video (Short/Eng)", "lang": "en"},
        {"id": "kxouC8EC5zg", "type": "Hindi / Hinglish Tech Video", "lang": "hi/en"},
        {"id": "INVALID_ID_999", "type": "Non-existent Video (Error Test)", "lang": "none"},
    ]

    print("\n[1] Testing YouTube Transcript Retrieval:")
    for tv in test_videos:
        vid = tv["id"]
        start_t = time.perf_counter()
        data = transcriber.get_youtube_transcript(vid)
        elapsed = time.perf_counter() - start_t

        success = data is not None and len(data) > 0
        seg_count = len(data) if data else 0
        total_words = sum(len(s.get("text", "").split()) for s in (data or []))
        total_duration = max((s.get("end", 0.0) for s in (data or [])), default=0.0)

        results["transcripts"][vid] = {
            "type": tv["type"],
            "success": success,
            "elapsed_seconds": round(elapsed, 3),
            "segments_count": seg_count,
            "word_count": total_words,
            "detected_duration_sec": round(total_duration, 1)
        }
        print(f"  - Video '{vid}' ({tv['type']}):")
        print(f"      Success: {success} | Segments: {seg_count} | Words: {total_words} | Time: {elapsed:.3f}s")

    # 2. Section Download Benchmark
    # We download a 15-second snippet (00:00:10 - 00:00:25) from a real video: jNQXAC9IVRw
    print("\n[2] Testing yt-dlp Section Download (Time & Bytes):")
    section_test_vid = "jNQXAC9IVRw"
    target_url = f"https://www.youtube.com/watch?v={section_test_vid}"
    out_file = TEMP_DIR / "audit_section_test_1.mp4"
    if out_file.exists():
        out_file.unlink()

    start_sec = 5.0
    end_sec = 15.0

    dl_start = time.perf_counter()
    dl_ok = downloader.download_section(target_url, start_sec, end_sec, out_file)
    dl_elapsed = time.perf_counter() - dl_start

    file_size_bytes = out_file.stat().st_size if out_file.exists() else 0
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    # Get full video metadata to compare size
    info = downloader.extract_info(target_url)

    results["section_downloads"]["single_section"] = {
        "video_id": section_test_vid,
        "section": f"{start_sec}s - {end_sec}s (Duration: {end_sec - start_sec}s)",
        "download_success": dl_ok,
        "elapsed_seconds": round(dl_elapsed, 2),
        "downloaded_bytes": file_size_bytes,
        "downloaded_mb": file_size_mb,
        "full_video_duration": info.get("duration", 0.0)
    }

    print(f"  - Download Status: {'SUCCESS' if dl_ok else 'FAILED'}")
    print(f"  - Download Elapsed: {dl_elapsed:.2f} seconds")
    print(f"  - Downloaded Payload: {file_size_mb} MB ({file_size_bytes:,} bytes)")
    print(f"  - Full Video Duration: {info.get('duration')}s")

    # 3. Failed Section Recovery Test
    print("\n[3] Testing Failed Section Recovery & Error Resilience:")
    bad_url = "https://www.youtube.com/watch?v=NON_EXISTENT_XYZ123"
    bad_out = TEMP_DIR / "audit_failed_section.mp4"
    bad_start = time.perf_counter()
    recovery_result = downloader.download_section(bad_url, 0.0, 10.0, bad_out)
    bad_elapsed = time.perf_counter() - bad_start

    results["section_downloads"]["recovery_resilience"] = {
        "handled_gracefully": recovery_result is False,
        "elapsed_seconds": round(bad_elapsed, 2),
        "file_created": bad_out.exists()
    }
    print(f"  - Handled cleanly without crash: {recovery_result is False}")
    print(f"  - Recovery check elapsed: {bad_elapsed:.2f}s")

    # Output JSON report
    report_path = Path(__file__).parent / "selective_download_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Detailed benchmark saved to {report_path}")
    return results

if __name__ == "__main__":
    run_selective_download_audit()

import os
import sys
import time
import json
import tracemalloc
import subprocess
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import TEMP_DIR, OUTPUTS_DIR, THUMBNAILS_DIR
from backend.app.services.viral_detector import ViralDetector
from backend.app.services.subtitle_generator import SubtitleGenerator
from backend.app.services.video_processor import VideoProcessor
from backend.app.utils.ffmpeg_helper import get_ffmpeg_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_synthetic_24hr_transcript():
    """Generate a realistic 24-hour transcript (86,400 seconds) with ~10,000 conversational lines."""
    phrases = [
        "Welcome to this massive 24-hour marathon stream today.",
        "Why do most creators fail in their first year? Here is the secret truth.",
        "Never make this mistake when investing in crypto or stocks.",
        "We are continuing our discussion on software architecture and systems.",
        "The problem with modern web frameworks is memory overhead and latency.",
        "Wait, did you see that crazy move? That was unbelievable!",
        "Stop doing tutorials and start building real products immediately.",
        "Let us take a quick break and answer questions from the community chat.",
        "This simple rule made my business over a million dollars in revenue.",
        "Always focus on customer retention before spending money on advertising."
    ]

    segments = []
    current_time = 0.0
    idx = 0
    # Simulate up to 24 hours (86,400s)
    target_duration = 86400.0  # 24 hours
    line_duration = 8.5  # average line duration in seconds

    while current_time < target_duration:
        phrase = phrases[idx % len(phrases)]
        dur = line_duration + ((idx % 5) * 0.5)
        segments.append({
            "start": round(current_time, 2),
            "end": round(current_time + dur, 2),
            "duration": round(dur, 2),
            "text": f"{phrase} (Segment #{idx})"
        })
        current_time += dur + 0.5  # small pause
        idx += 1

    return segments, target_duration

def create_synthetic_test_video(duration_sec: int, output_file: Path):
    """Use FFmpeg testsrc and sine audio to generate synthetic test media."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", f"testsrc=duration={duration_sec}:size=1280x720:rate=30",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration_sec}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "64k",
        str(output_file)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def run_long_video_benchmark():
    print("=" * 60)
    print("AUDIT SECTION 4: LONG-VIDEO PROCESSING & RESOURCE BENCHMARK")
    print("=" * 60)

    tracemalloc.start()
    t_cpu_start = time.process_time()

    results = {
        "dataset": {},
        "chunking": {},
        "scoring": {},
        "deduplication": {},
        "rendering": {},
        "system_resources": {}
    }

    # 1. Generate 24-Hour Transcript
    print("\n[1] Generating 24-Hour Synthetic Transcript (86,400 seconds)...")
    gen_start = time.perf_counter()
    segments, total_duration = generate_synthetic_24hr_transcript()
    gen_elapsed = time.perf_counter() - gen_start

    results["dataset"] = {
        "simulated_duration_hours": round(total_duration / 3600, 1),
        "total_segments": len(segments),
        "transcript_memory_kb": round(sys.getsizeof(segments) / 1024, 2),
        "generation_time_sec": round(gen_elapsed, 3)
    }
    print(f"  - Generated {len(segments):,} segments spanning {total_duration/3600:.1f} hours in {gen_elapsed:.3f}s")

    # 2. Benchmark Candidate Block Chunking
    print("\n[2] Benchmarking Candidate Block Creation on 24-Hour Transcript...")
    detector = ViralDetector()
    chunk_start = time.perf_counter()
    candidates = detector._create_candidate_blocks(segments, min_duration=25.0, max_duration=55.0)
    chunk_elapsed = time.perf_counter() - chunk_start

    results["chunking"] = {
        "candidates_generated": len(candidates),
        "chunking_time_sec": round(chunk_elapsed, 4),
        "min_duration_found": min((c["duration"] for c in candidates), default=0),
        "max_duration_found": max((c["duration"] for c in candidates), default=0)
    }
    print(f"  - Generated {len(candidates)} candidate blocks in {chunk_elapsed:.4f}s")
    print(f"  - Duration bounds: {results['chunking']['min_duration_found']}s to {results['chunking']['max_duration_found']}s")

    # 3. Benchmark Scoring & Virality Ranking
    print("\n[3] Benchmarking Natural Language Heuristic Scoring...")
    score_start = time.perf_counter()
    scored = detector._score_with_heuristics(candidates, target_count=5)
    score_elapsed = time.perf_counter() - score_start

    top_scores = [s["viral_score"] for s in scored[:5]]
    results["scoring"] = {
        "scored_candidates_count": len(scored),
        "scoring_time_sec": round(score_elapsed, 4),
        "top_viral_scores": top_scores,
        "average_score": round(sum(s["viral_score"] for s in scored) / max(1, len(scored)), 1)
    }
    print(f"  - Scored {len(scored)} blocks in {score_elapsed:.4f}s | Top 5 scores: {top_scores}")

    # 4. Benchmark Deduplication & Overlap Removal
    print("\n[4] Benchmarking Overlap Removal & Non-overlapping Selection...")
    dedup_start = time.perf_counter()
    top_clips = detector._deduplicate_and_sort(scored, target_count=5)
    dedup_elapsed = time.perf_counter() - dedup_start

    # Verify no overlaps
    has_overlap = False
    for i in range(len(top_clips)):
        for j in range(i + 1, len(top_clips)):
            c1, c2 = top_clips[i], top_clips[j]
            if not (c1["end_time"] <= c2["start_time"] or c1["start_time"] >= c2["end_time"]):
                has_overlap = True

    results["deduplication"] = {
        "final_clips_count": len(top_clips),
        "dedup_time_sec": round(dedup_elapsed, 5),
        "overlap_detected": has_overlap,
        "selected_intervals": [{"start": c["start_time"], "end": c["end_time"]} for c in top_clips]
    }
    print(f"  - Selected {len(top_clips)} distinct clips (Overlap detected: {has_overlap}) in {dedup_elapsed:.5f}s")

    # 5. Synthetic Video Generation & Full Clip Pipeline Export
    print("\n[5] Rendering Synthetic Test Clip with Subtitles & 9:16 Reframe...")
    sub_gen = SubtitleGenerator()
    vid_proc = VideoProcessor()

    # Create 30s synthetic source video
    test_src = TEMP_DIR / "audit_synth_30s_source.mp4"
    if not test_src.exists():
        print("  - Generating 30-second synthetic source media using FFmpeg...")
        create_synthetic_test_video(30, test_src)

    # Subtitles for 30s
    sample_subs = [
        {"start": 1.0, "end": 4.5, "text": "Why do most creators fail with money?"},
        {"start": 5.0, "end": 9.0, "text": "Stop making this secret mistake right now."},
        {"start": 9.5, "end": 14.0, "text": "This rule generated over a million dollars."},
        {"start": 14.5, "end": 20.0, "text": "Focus on high retention viral hooks every time."},
        {"start": 20.5, "end": 28.0, "text": "Subscribe for more free clipping automation tutorials!"}
    ]

    ass_out = TEMP_DIR / "audit_synth.ass"
    srt_out = OUTPUTS_DIR / "audit_synth.srt"
    vtt_out = OUTPUTS_DIR / "audit_synth.vtt"
    clip_out = OUTPUTS_DIR / "audit_synth_final_9x16.mp4"
    thumb_out = THUMBNAILS_DIR / "audit_synth_thumb.jpg"

    sub_gen.generate_ass(sample_subs, ass_out, clip_start_offset=0.0, style_preset="hormozi", video_width=1080, video_height=1920)
    sub_gen.generate_srt(sample_subs, srt_out)
    sub_gen.generate_vtt(sample_subs, vtt_out)

    render_start = time.perf_counter()
    render_ok = vid_proc.process_clip(
        input_video_path=test_src,
        output_clip_path=clip_out,
        aspect_ratio="9:16",
        subtitle_ass_path=ass_out,
        subtitle_srt_path=srt_out,
        thumbnail_output_path=thumb_out
    )
    render_elapsed = time.perf_counter() - render_start

    clip_size_mb = round(clip_out.stat().st_size / (1024 * 1024), 2) if clip_out.exists() else 0
    thumb_size_kb = round(thumb_out.stat().st_size / 1024, 2) if thumb_out.exists() else 0

    results["rendering"] = {
        "success": render_ok,
        "render_time_sec": round(render_elapsed, 2),
        "source_duration_sec": 30.0,
        "realtime_factor": round(30.0 / max(0.1, render_elapsed), 2),
        "clip_file_size_mb": clip_size_mb,
        "thumbnail_file_size_kb": thumb_size_kb
    }
    print(f"  - Render Status: {'SUCCESS' if render_ok else 'FAILED'} in {render_elapsed:.2f}s")
    print(f"  - Real-time Factor: {results['rendering']['realtime_factor']}x (30s processed in {render_elapsed:.2f}s)")
    print(f"  - Output Size: {clip_size_mb} MB | Thumbnail: {thumb_size_kb} KB")

    # 6. Memory & CPU Profile
    cpu_time_used = round(time.process_time() - t_cpu_start, 2)
    current_traced, peak_traced = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results["system_resources"] = {
        "current_traced_mb": round(current_traced / (1024 * 1024), 2),
        "peak_traced_mb": round(peak_traced / (1024 * 1024), 2),
        "cpu_process_time_sec": cpu_time_used
    }
    print(f"\n[6] Resource Metrics:")
    print(f"  - Peak Python Traced Heap: {results['system_resources']['peak_traced_mb']} MB")
    print(f"  - CPU Process Time: {cpu_time_used}s")

    # Save benchmark
    report_path = Path(__file__).parent / "long_video_benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Long-video benchmark report saved to {report_path}")
    return results

if __name__ == "__main__":
    run_long_video_benchmark()

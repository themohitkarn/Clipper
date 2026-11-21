import os
import sys
import json
import logging
from pathlib import Path

# Force utf-8 for Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.viral_detector import ViralDetector, VIRAL_HOOK_TRIGGERS
from backend.app.services.subtitle_generator import SubtitleGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_ai_quality_audit():
    print("=" * 60)
    print("AUDIT SECTION 6: AI VIRAL DETECTION QUALITY & MULTILINGUAL AUDIT")
    print("=" * 60)

    detector = ViralDetector()
    sub_gen = SubtitleGenerator()

    # Multilingual Test Cases: English, Hindi, and Hinglish
    test_datasets = {
        "english": [
            {"start": 0.0, "end": 6.0, "text": "Why do 99 percent of businesses fail in their first year?"},
            {"start": 6.5, "end": 12.0, "text": "The secret reason is they run out of cash before finding product market fit."},
            {"start": 12.5, "end": 18.0, "text": "Never hire an agency before you understand the numbers yourself."},
            {"start": 18.5, "end": 25.0, "text": "This mistake cost me over half a million dollars early on."},
            {"start": 25.5, "end": 32.0, "text": "When you focus on customer retention, growth compounds automatically."}
        ],
        "hindi": [
            {"start": 0.0, "end": 5.0, "text": "Dosto aaj hum baat karenge YouTube se paise kaise kamaye."},
            {"start": 5.5, "end": 11.0, "text": "Ye secret formula koi nahi batayega jisse views 10 guna badh jaye."},
            {"start": 11.5, "end": 17.0, "text": "Sabse badi mistake log ye karte hain ki consistency break kar dete hain."},
            {"start": 17.5, "end": 24.0, "text": "Agar aap daily 1 quality video upload karte ho to growth guaranteed hai."},
            {"start": 24.5, "end": 30.0, "text": "Comment karke batao aapka favorite niche kaunsa hai."}
        ],
        "hinglish": [
            {"start": 0.0, "end": 6.0, "text": "Stop scrolling! What if I told you AI can do all video editing in seconds?"},
            {"start": 6.5, "end": 13.0, "text": "Most creators spend 5 hours cutting clips, which is crazy waste of time."},
            {"start": 13.5, "end": 20.0, "text": "Yeh free open-source clipper automated hooks identify karke export karta hai."},
            {"start": 20.5, "end": 27.0, "text": "Try karo and see the unbelievable difference in your channel views."},
            {"start": 27.5, "end": 33.0, "text": "Follow for more daily coding and automation hacks."}
        ]
    }

    results = {
        "languages": {},
        "boundary_quality": {},
        "subtitle_sync": {},
        "heuristic_vs_true_virality_analysis": {}
    }

    print("\n[1] Testing Viral Hook Detection & Scoring Across Languages:")
    for lang, segments in test_datasets.items():
        candidates = detector._create_candidate_blocks(segments, min_duration=15.0, max_duration=35.0)
        scored = detector._score_with_heuristics(candidates, target_count=3)
        top = scored[0] if scored else None

        results["languages"][lang] = {
            "segments_count": len(segments),
            "candidates_count": len(candidates),
            "top_candidate": {
                "title": top["title"] if top else None,
                "hook_text": top["hook_text"] if top else None,
                "score": top["viral_score"] if top else 0,
                "reason": top["viral_reason"] if top else None,
                "duration": top["duration"] if top else 0
            } if top else None
        }

        print(f"\n  Language: {lang.upper()}")
        if top:
            print(f"    - Title: {top['title']}")
            print(f"    - Hook: {top['hook_text']}")
            print(f"    - Viral Score: {top['viral_score']}/100")
            print(f"    - Reason: {top['viral_reason']}")
            print(f"    - Duration: {top['duration']}s")
        else:
            print("    - No candidates generated")

    # 2. Test Clip Boundary Quality & Context Completeness
    print("\n[2] Testing Clip Boundary & Context Completeness:")
    long_segments = [
        {"start": 0.0, "end": 5.0, "text": "In the beginning of our journey we started with zero capital."},
        {"start": 5.2, "end": 10.0, "text": "Why did people doubt us? Because nobody believed in the product."},
        {"start": 10.2, "end": 16.0, "text": "Then we discovered the secret to organic viral distribution on TikTok."},
        {"start": 16.2, "end": 22.0, "text": "Sales doubled every single week without spending money on ads."},
        {"start": 22.2, "end": 27.0, "text": "And that is how we reached profitability in three months."},
        {"start": 27.2, "end": 35.0, "text": "The end."}
    ]
    candidates = detector._create_candidate_blocks(long_segments, min_duration=18.0, max_duration=30.0)
    boundary_metrics = []
    for c in candidates:
        text = c["text"]
        ends_with_period = text.endswith((".", "!", "?"))
        starts_clean = text[0].isupper()
        boundary_metrics.append({
            "duration": c["duration"],
            "ends_with_punctuation": ends_with_period,
            "starts_clean": starts_clean,
            "char_count": len(text)
        })

    results["boundary_quality"] = {
        "candidate_count": len(candidates),
        "metrics": boundary_metrics,
        "complete_sentences_pct": round(sum(1 for m in boundary_metrics if m["ends_with_punctuation"]) / max(1, len(boundary_metrics)) * 100, 1)
    }
    print(f"  - Complete sentence boundary preservation: {results['boundary_quality']['complete_sentences_pct']}%")

    # 3. Subtitle Synchronization & Time Offset Validation
    print("\n[3] Testing Subtitle Synchronization (SRT / ASS Offset Calculation):")
    offset_test_subs = [
        {"start": 120.0, "end": 125.0, "text": "This is at two minutes in original video."},
        {"start": 125.5, "end": 130.0, "text": "And this is five seconds later."}
    ]
    clip_offset = 120.0
    out_srt = Path(__file__).parent / "test_offset.srt"
    sub_gen.generate_srt(offset_test_subs, out_srt, clip_start_offset=clip_offset)
    srt_text = out_srt.read_text(encoding="utf-8")
    
    # Check that timestamps in SRT start at 00:00:00,000
    starts_at_zero = "00:00:00,000 --> 00:00:05,000" in srt_text
    results["subtitle_sync"] = {
        "clip_offset": clip_offset,
        "starts_at_zero": starts_at_zero,
        "raw_srt_snippet": srt_text.strip()
    }
    print(f"  - Subtitle offset transformation verified: {starts_at_zero}")
    if out_srt.exists():
        out_srt.unlink()

    # 4. Objective Classification: Heuristic vs Viral Probability
    results["heuristic_vs_true_virality_analysis"] = {
        "distinction_note": (
            "Viral scores produced by the heuristic engine (50-99) reflect the presence of engagement patterns "
            "(hook density, curiosity questions, emotional power words, pacing, and 30-45s duration sweet spots). "
            "They MUST NOT be marketed as an empirical guarantee of algorithmic view count on social media, "
            "as true virality depends on external market factors including creator authority, topic saturation, "
            "thumbnail CTR, and audience demographics."
        )
    }
    print(f"\n[4] Virality Metric Integrity Note:")
    print(f"  - {results['heuristic_vs_true_virality_analysis']['distinction_note']}")

    report_path = Path(__file__).parent / "ai_quality_audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] AI quality audit report saved to {report_path}")
    return results

if __name__ == "__main__":
    run_ai_quality_audit()

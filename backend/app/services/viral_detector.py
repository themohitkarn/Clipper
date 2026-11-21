import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Emotional, curiosity, and high-engagement power words
VIRAL_HOOK_TRIGGERS = [
    r"\bwhy\b", r"\bhow to\b", r"\bsecret\b", r"\bmistake\b", r"\bnever\b",
    r"\balways\b", r"\bdon't\b", r"\bstop\b", r"\bthe truth\b", r"\bwarning\b",
    r"\bshocking\b", r"\binsane\b", r"\bcrazy\b", r"\bunbelievable\b", r"\bworst\b",
    r"\bbest\b", r"\bhate\b", r"\blove\b", r"\bmoney\b", r"\brich\b", r"\bmillion\b",
    r"\bbillion\b", r"\bfail\b", r"\bsuccess\b", r"\brule\b", r"\blie\b", r"\bexposed\b",
    r"\breason\b", r"\bproblem\b", r"\bfix\b", r"\bproven\b", r"\bhack\b"
]

class ViralDetector:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def detect_best_clips(
        self,
        transcript_segments: List[Dict[str, Any]],
        video_duration: float,
        target_count: int = 5,
        min_duration: float = 20.0,
        max_duration: float = 60.0
    ) -> List[Dict[str, Any]]:
        """
        Group transcript into topic blocks and score them for virality.
        Works across 10-minute videos to 24+ hour long streams.
        """
        if not transcript_segments:
            # Fallback if no transcript is available: synthesize evenly spaced highlights
            return self._generate_timeline_fallback(video_duration, target_count, min_duration, max_duration)

        # 1. Group individual subtitle lines into candidate blocks
        candidates = self._create_candidate_blocks(transcript_segments, min_duration, max_duration)
        if not candidates:
            return self._generate_timeline_fallback(video_duration, target_count, min_duration, max_duration)

        # 2. Score candidates: Try Gemini API if key is present, else use Smart Heuristic
        scored_clips = []
        if self.api_key:
            try:
                scored_clips = self._score_with_gemini(candidates, target_count)
            except Exception as e:
                logger.warning(f"Gemini API scoring failed: {e}. Falling back to Smart Heuristic.")
                scored_clips = []

        if not scored_clips:
            scored_clips = self._score_with_heuristics(candidates, target_count)

        # Ensure no overlap and sort by virality score
        return self._deduplicate_and_sort(scored_clips, target_count)

    def _create_candidate_blocks(
        self,
        segments: List[Dict[str, Any]],
        min_duration: float,
        max_duration: float
    ) -> List[Dict[str, Any]]:
        """Combine subtitle lines into smooth, cohesive chunks between min_duration and max_duration."""
        candidates = []
        n = len(segments)
        step = max(1, n // 80) if n > 100 else 1  # For 24-hr transcripts, stride dynamically

        for i in range(0, n, step):
            start_time = segments[i]["start"]
            current_text = []
            end_time = start_time

            for j in range(i, n):
                seg = segments[j]
                current_text.append(seg["text"])
                end_time = seg["end"]
                dur = end_time - start_time

                if dur >= min_duration:
                    full_text = " ".join(current_text)
                    # Prefer ending on punctuation (. ? ! or pause)
                    if dur >= (min_duration + max_duration) / 2 or re.search(r"[.?!]\s*$", full_text) or dur >= max_duration:
                        candidates.append({
                            "start_time": round(start_time, 2),
                            "end_time": round(end_time, 2),
                            "duration": round(dur, 2),
                            "text": full_text
                        })
                        break
                if dur > max_duration:
                    break

        return candidates

    def _score_with_heuristics(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """
        Smart 100% Free natural language heuristic engine.
        Evaluates scroll-stopping hooks, curiosity gaps, questions, and emotional intensity.
        """
        results = []
        for cand in candidates:
            text = cand["text"].strip()
            text_lower = text.lower()
            words = text.split()
            word_count = len(words)
            if word_count < 8:
                continue

            score = 65  # Base score

            # 1. First 5 words hook test (the scroll stopper)
            first_words = " ".join(words[:6]).lower()
            if any(re.search(pat, first_words) for pat in VIRAL_HOOK_TRIGGERS):
                score += 15

            # 2. Question / Curiosity Hook
            if "?" in first_words or first_words.startswith(("did you know", "why do", "how does", "what if", "have you ever")):
                score += 12

            # 3. Overall viral triggers in the chunk
            trigger_hits = sum(1 for pat in VIRAL_HOOK_TRIGGERS if re.search(pat, text_lower))
            score += min(15, trigger_hits * 3)

            # 4. Exclamation & excitement
            if "!" in text:
                score += 4

            # 5. Ideal duration bonus (30-45s is the sweet spot for TikTok / Shorts)
            dur = cand["duration"]
            if 25 <= dur <= 50:
                score += 6

            final_score = min(99, max(50, score))

            # Generate punchy viral title
            title = self._generate_heuristic_title(text, first_words)
            reason = self._generate_heuristic_reason(first_words, trigger_hits)

            results.append({
                "title": title,
                "hook_text": " ".join(words[:10]) + "...",
                "viral_score": final_score,
                "viral_reason": reason,
                "start_time": cand["start_time"],
                "end_time": cand["end_time"],
                "duration": cand["duration"],
                "text": cand["text"]
            })

        results.sort(key=lambda x: x["viral_score"], reverse=True)
        return results

    def _generate_heuristic_title(self, text: str, first_words: str) -> str:
        clean = re.sub(r"[^\w\s]", "", text)
        words = clean.split()
        if len(words) >= 6:
            candidate = " ".join(words[:6]).title()
            return f"{candidate}... 🤯"
        return f"{text[:40].title()} 🔥"

    def _generate_heuristic_reason(self, first_words: str, hits: int) -> str:
        if "?" in first_words:
            return "Opens with a curiosity question that hooks the viewer within the first 3 seconds."
        if hits >= 2:
            return "High density of emotional trigger words and fast-paced conversational payoff."
        return "Cohesive conversational highlight with high viewer retention potential."

    def _score_with_gemini(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Call Google Gemini 2.5/1.5 Flash (Free Tier) to find peak viral clips."""
        from google import genai
        client = genai.Client(api_key=self.api_key)

        # Select a representative sample of up to 25 candidates across the video
        stride = max(1, len(candidates) // 25)
        sampled = candidates[::stride][:25]

        prompt = f"""
You are an expert viral content strategist for TikTok, YouTube Shorts, and Instagram Reels.
Analyze these video transcript segments and select the top {target_count} most engaging clips.

CRITERIA FOR VIRALITY:
1. High Hook Score: Does the first sentence immediately create a curiosity gap?
2. Emotional Payoff / Insight: Does it provide a surprising revelation, debate, humor, or lesson?
3. Self-contained: Can a viewer understand it without watching the entire video?

Segments to analyze:
{json.dumps([{ 'id': idx, 'start': c['start_time'], 'end': c['end_time'], 'text': c['text']} for idx, c in enumerate(sampled)], indent=2)}

Respond ONLY with a valid JSON array of objects with keys:
- "id": int (id from input)
- "title": string (punchy, click-worthy title with 1 emoji)
- "hook_text": string (the opening hook phrase)
- "viral_score": integer (0 to 100)
- "viral_reason": string (1-sentence explanation of why it will perform well)
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        results = []
        for item in data:
            idx = item.get("id")
            if idx is not None and 0 <= idx < len(sampled):
                orig = sampled[idx]
                results.append({
                    "title": item.get("title", "Viral Highlight 🔥"),
                    "hook_text": item.get("hook_text", orig["text"][:50]),
                    "viral_score": int(item.get("viral_score", 85)),
                    "viral_reason": item.get("viral_reason", "High audience retention and strong hook."),
                    "start_time": orig["start_time"],
                    "end_time": orig["end_time"],
                    "duration": orig["duration"],
                    "text": orig["text"]
                })
        return results

    def _deduplicate_and_sort(
        self,
        clips: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Remove overlapping clips and pick the highest scoring unique moments."""
        selected: List[Dict[str, Any]] = []
        for clip in clips:
            overlap = False
            for s in selected:
                # Check if there is an overlap > 10 seconds
                if not (clip["end_time"] <= s["start_time"] or clip["start_time"] >= s["end_time"]):
                    overlap = True
                    break
            if not overlap:
                selected.append(clip)
            if len(selected) >= target_count:
                break
        return selected

    def _generate_timeline_fallback(
        self,
        duration: float,
        target_count: int,
        min_dur: float,
        max_dur: float
    ) -> List[Dict[str, Any]]:
        """Fallback when no transcript is available: space out clips across video timeline."""
        if duration <= 0:
            duration = 300.0
        clip_dur = (min_dur + max_dur) / 2
        step = max(clip_dur * 2, duration / (target_count + 1))
        clips = []
        for i in range(target_count):
            start = round(step * (i + 0.5), 2)
            end = min(round(start + clip_dur, 2), duration)
            if end <= start:
                break
            clips.append({
                "title": f"Highlight Clip #{i+1} ⚡",
                "hook_text": "Watch this key moment...",
                "viral_score": 88 - (i * 3),
                "viral_reason": f"Top highlight segment selected from timeline position {int(start//60)}m.",
                "start_time": start,
                "end_time": end,
                "duration": round(end - start, 2),
                "text": ""
            })
        return clips

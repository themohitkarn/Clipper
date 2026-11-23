import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Emotional, curiosity, and high-engagement power words (English & Hinglish)
VIRAL_HOOK_TRIGGERS = [
    r"\bwhy\b", r"\bhow to\b", r"\bsecret\b", r"\bmistake\b", r"\bnever\b",
    r"\balways\b", r"\bdon't\b", r"\bstop\b", r"\bthe truth\b", r"\bwarning\b",
    r"\bshocking\b", r"\binsane\b", r"\bcrazy\b", r"\bunbelievable\b", r"\bworst\b",
    r"\bbest\b", r"\bhate\b", r"\blove\b", r"\bmoney\b", r"\brich\b", r"\bmillion\b",
    r"\bbillion\b", r"\bfail\b", r"\bsuccess\b", r"\brule\b", r"\blie\b", r"\bexposed\b",
    r"\breason\b", r"\bproblem\b", r"\bfix\b", r"\bproven\b", r"\bhack\b",
    # Hinglish viral triggers
    r"\bpaisa\b", r"\bpaise\b", r"\brupaye\b", r"\bkya\b", r"\bkyun\b", r"\bkaise\b",
    r"\braaz\b", r"\bgalti\b", r"\bmat karo\b", r"\bkabhi nahi\b", r"\bsach\b",
    r"\bsuno\b", r"\bdekho\b", r"\bviral\b", r"\bviews\b", r"\btoofan\b"
]

class ViralDetector:
    def __init__(
        self,
        api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        llm_provider: str = "auto"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.llm_provider = llm_provider.lower() if llm_provider else "auto"
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

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
        Supports Groq (Llama 3.3), Google Gemini, Ollama, and Free Heuristics.
        """
        if not transcript_segments:
            # Fallback if no transcript is available: synthesize evenly spaced highlights
            return self._generate_timeline_fallback(video_duration, target_count, min_duration, max_duration)

        # 1. Group individual subtitle lines into candidate blocks
        candidates = self._create_candidate_blocks(transcript_segments, min_duration, max_duration, target_count)
        if not candidates:
            return self._generate_timeline_fallback(video_duration, target_count, min_duration, max_duration)

        # 2. Score candidates using preferred / available LLM
        scored_clips = []
        
        # Try Groq (Llama 3.3 70B - fastest and free)
        if (self.llm_provider in ["auto", "groq"]) and self.groq_api_key:
            try:
                scored_clips = self._score_with_groq(candidates, target_count)
                if scored_clips:
                    logger.info("Successfully scored clips using Groq Llama 3.3")
            except Exception as e:
                logger.warning(f"Groq scoring failed: {e}")

        # Try Google Gemini (Free Tier 2.0 / 1.5 Flash)
        if not scored_clips and (self.llm_provider in ["auto", "gemini"]) and self.api_key:
            try:
                scored_clips = self._score_with_gemini(candidates, target_count)
                if scored_clips:
                    logger.info("Successfully scored clips using Google Gemini")
            except Exception as e:
                logger.warning(f"Gemini API scoring failed: {e}")

        # Try Local Ollama (100% Free & Local)
        if not scored_clips and (self.llm_provider in ["auto", "ollama"]) and self._is_ollama_available():
            try:
                scored_clips = self._score_with_ollama(candidates, target_count)
                if scored_clips:
                    logger.info("Successfully scored clips using local Ollama")
            except Exception as e:
                logger.warning(f"Ollama scoring failed: {e}")

        # Fallback to Smart Heuristic Engine (100% Free, Instant, No key needed)
        if not scored_clips:
            scored_clips = self._score_with_heuristics(candidates, target_count)

        # Ensure no overlap and fill up to target_count
        return self._deduplicate_and_sort(scored_clips, target_count, video_duration, min_duration, max_duration)

    def _create_candidate_blocks(
        self,
        segments: List[Dict[str, Any]],
        min_duration: float,
        max_duration: float,
        target_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Combine subtitle lines into smooth, cohesive chunks between min_duration and max_duration."""
        candidates = []
        n = len(segments)
        step = max(1, n // max(120, target_count * 6)) if n > 150 else 1

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
        Generates viral SEO titles, descriptions, and hashtags.
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

            # Generate punchy viral title, description and hashtags
            title = self._generate_heuristic_title(text, first_words)
            reason = self._generate_heuristic_reason(first_words, trigger_hits)
            desc = self._generate_heuristic_description(text, title)
            hashtags = self._generate_heuristic_hashtags(text)

            results.append({
                "title": title,
                "hook_text": " ".join(words[:10]) + "...",
                "viral_score": final_score,
                "viral_reason": reason,
                "start_time": cand["start_time"],
                "end_time": cand["end_time"],
                "duration": cand["duration"],
                "text": cand["text"],
                "description": desc,
                "hashtags": hashtags
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

    def _generate_heuristic_description(self, text: str, title: str) -> str:
        first_sentence = text.split(".")[0].strip()
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:97] + "..."
        return f"{first_sentence} 👀 Watch till the end and follow for more viral moments!"

    def _generate_heuristic_hashtags(self, text: str) -> List[str]:
        tags = ["#Shorts", "#Viral", "#Trending", "#Clips", "#FYP"]
        text_lower = text.lower()
        if any(w in text_lower for w in ["game", "kill", "clutch", "headshot", "gta", "pubg", "bgmi", "valorant"]):
            tags.insert(1, "#Gaming")
            tags.insert(2, "#Gamer")
        if any(w in text_lower for w in ["paisa", "money", "rich", "crore", "business"]):
            tags.insert(1, "#Business")
            tags.insert(2, "#Motivation")
        return tags[:6]

    def _score_with_groq(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Call Groq Cloud API (Free & Blazingly Fast) using Llama 3.3 70B."""
        import requests

        sample_size = min(len(candidates), max(50, target_count * 3))
        stride = max(1, len(candidates) // sample_size)
        sampled = candidates[::stride][:sample_size]

        prompt = f"""
You are an expert viral content strategist for TikTok, YouTube Shorts, and Instagram Reels.
Analyze these video transcript segments and select the top {target_count} most engaging clips.

CRITERIA FOR VIRALITY:
1. High Hook Score: Does the first sentence immediately stop scrolling?
2. Emotional Payoff / Insight: Surprising revelation, drama, debate, humor, or lesson.
3. Self-contained: Viewer understands without whole context.

Segments to analyze:
{json.dumps([{ 'id': idx, 'start': c['start_time'], 'end': c['end_time'], 'text': c['text']} for idx, c in enumerate(sampled)], indent=2)}

Respond with a JSON object with a "clips" key containing a list of objects with:
- "id": int (id from input)
- "title": string (punchy, click-worthy title under 50 chars with 1 emoji)
- "hook_text": string (opening hook phrase)
- "viral_score": integer (0 to 100)
- "viral_reason": string (1-sentence explanation)
- "description": string (engaging 2-sentence caption + CTA for Shorts)
- "hashtags": array of 5 strings (e.g. ["#Shorts", "#Viral", "#Gaming", "#Trending", "#FYP"])
"""
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        for model in models:
            try:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a viral social media strategist. Always output valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3
                    },
                    timeout=25
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    raw_clips = parsed.get("clips") or parsed.get("data") or (parsed if isinstance(parsed, list) else [])
                    return self._map_llm_results(raw_clips, sampled)
            except Exception as e:
                logger.warning(f"Groq model {model} attempt failed: {e}")
        return []

    def _score_with_gemini(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Call Google Gemini 2.0/1.5 Flash (Free Tier) via REST to find peak viral clips."""
        import requests
        
        sample_size = min(len(candidates), max(50, target_count * 3))
        stride = max(1, len(candidates) // sample_size)
        sampled = candidates[::stride][:sample_size]

        prompt = f"""
You are an expert viral content strategist for TikTok, YouTube Shorts, and Instagram Reels.
Analyze these video transcript segments and select the top {target_count} most engaging clips.

CRITERIA FOR VIRALITY:
1. High Hook Score: Does the first sentence immediately create curiosity?
2. Emotional Payoff: Humor, insight, shock, debate, or high energy.
3. Self-contained: Can be understood independently.

Segments to analyze:
{json.dumps([{ 'id': idx, 'start': c['start_time'], 'end': c['end_time'], 'text': c['text']} for idx, c in enumerate(sampled)], indent=2)}

Respond ONLY with a valid JSON array of objects with keys:
- "id": int (id from input)
- "title": string (punchy, click-worthy title under 50 chars with 1 emoji)
- "hook_text": string (opening hook phrase)
- "viral_score": integer (0 to 100)
- "viral_reason": string (1-sentence explanation)
- "description": string (engaging caption + CTA for Shorts)
- "hashtags": array of 5 strings (e.g. ["#Shorts", "#Viral", "#FYP", "#Trending"])
"""
        models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data_json = resp.json()
                    raw_text = data_json["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(raw_text)
                    if isinstance(data, dict):
                        data = data.get("clips") or data.get("data") or []
                    return self._map_llm_results(data, sampled)
            except Exception as e:
                logger.warning(f"Gemini {model} attempt failed: {e}")
        return []

    def _is_ollama_available(self) -> bool:
        """Check if local Ollama server is running."""
        try:
            import requests
            res = requests.get(f"{self.ollama_base_url}/api/tags", timeout=1.0)
            return res.status_code == 200
        except Exception:
            return False

    def _score_with_ollama(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Call local Ollama instance (100% Free & Offline)."""
        import requests

        sample_size = min(len(candidates), max(40, target_count * 3))
        stride = max(1, len(candidates) // sample_size)
        sampled = candidates[::stride][:sample_size]

        prompt = f"""
You are a viral shorts strategist. Select top {target_count} clips from these segments:
{json.dumps([{ 'id': idx, 'start': c['start_time'], 'end': c['end_time'], 'text': c['text']} for idx, c in enumerate(sampled)], indent=2)}

Output JSON array of objects with keys: "id", "title", "hook_text", "viral_score", "viral_reason", "description", "hashtags".
"""
        resp = requests.post(
            f"{self.ollama_base_url}/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=40
        )
        if resp.status_code == 200:
            raw = json.loads(resp.json().get("response", "[]"))
            if isinstance(raw, dict):
                raw = raw.get("clips") or raw.get("data") or []
            return self._map_llm_results(raw, sampled)
        return []

    def _map_llm_results(
        self,
        raw_items: List[Dict[str, Any]],
        sampled: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        results = []
        for item in raw_items:
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
                    "text": orig["text"],
                    "description": item.get("description", self._generate_heuristic_description(orig["text"], item.get("title", ""))),
                    "hashtags": item.get("hashtags", self._generate_heuristic_hashtags(orig["text"]))
                })
        return results

    def _deduplicate_and_sort(
        self,
        clips: List[Dict[str, Any]],
        target_count: int,
        video_duration: float = 300.0,
        min_duration: float = 20.0,
        max_duration: float = 60.0
    ) -> List[Dict[str, Any]]:
        """Remove overlapping clips and pick the highest scoring unique moments."""
        selected: List[Dict[str, Any]] = []

        # 1. Pass 1: Strict non-overlapping moments
        for clip in clips:
            overlap = False
            for s in selected:
                if not (clip["end_time"] <= s["start_time"] or clip["start_time"] >= s["end_time"]):
                    overlap = True
                    break
            if not overlap:
                selected.append(clip)
            if len(selected) >= target_count:
                break

        # 2. Pass 2: If we still need more clips, allow slight overlap (< 25% overlap)
        if len(selected) < target_count:
            for clip in clips:
                if clip in selected:
                    continue
                excessive_overlap = False
                for s in selected:
                    overlap_start = max(clip["start_time"], s["start_time"])
                    overlap_end = min(clip["end_time"], s["end_time"])
                    if overlap_end > overlap_start:
                        overlap_sec = overlap_end - overlap_start
                        if overlap_sec > (clip["duration"] * 0.25):
                            excessive_overlap = True
                            break
                if not excessive_overlap:
                    selected.append(clip)
                if len(selected) >= target_count:
                    break

        # 3. Pass 3: If target_count still not met, fill open timeline slots
        if len(selected) < target_count and video_duration > 0:
            timeline_clips = self._generate_timeline_fallback(video_duration, target_count, min_duration, max_duration)
            for tc in timeline_clips:
                overlap = False
                for s in selected:
                    if not (tc["end_time"] <= s["start_time"] or tc["start_time"] >= s["end_time"]):
                        overlap = True
                        break
                if not overlap:
                    selected.append(tc)
                if len(selected) >= target_count:
                    break

        # Sort chronologically by start_time so the clips follow the video timeline
        selected.sort(key=lambda x: x["start_time"])
        return selected[:target_count]

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
        step = max(min_dur * 0.75, (duration - clip_dur) / max(1, target_count))
        clips = []
        for i in range(target_count):
            start = round(step * i + 5.0, 2)
            end = min(round(start + clip_dur, 2), duration)
            if end <= start or (end - start) < min_dur:
                break
            clips.append({
                "title": f"Highlight Clip #{i+1} ⚡",
                "hook_text": "Watch this key moment...",
                "viral_score": max(65, 88 - (i * 2)),
                "viral_reason": f"Top highlight segment selected from timeline position {int(start//60)}m.",
                "start_time": start,
                "end_time": end,
                "duration": round(end - start, 2),
                "text": "",
                "description": f"Highlight moment #{i+1}! Don't forget to like and subscribe for more.",
                "hashtags": ["#Shorts", "#Viral", "#Trending", "#Highlights", "#FYP"]
            })
        return clips

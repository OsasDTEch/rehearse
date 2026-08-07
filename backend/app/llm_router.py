"""Post-session feedback generation. Ollama cloud primary, Groq fallback.

Both are OpenAI-compatible chat endpoints, so one client function serves both.
"""
import json
import os

import httpx

from .logger import log_event

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")

GROQ_BASE = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

FEEDBACK_SYSTEM = (
    "You give feedback on a practice conversation to a neurodivergent young person. "
    "Your entire output must be a single JSON object, nothing else, with keys: "
    '"went_well" (a list of exactly 2 short strings), "try_next" (a list with exactly 1 short string). '
    "Rules: be specific to what they actually said. Be warm and plain. No scores, no grades, no criticism. "
    "The try_next item is a gentle invitation, phrased as 'next time you could try...', never a correction. "
    "Each string under 25 words. No idioms, no sarcasm."
)


async def _chat(base: str, key: str, model: str, messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": messages, "temperature": 0.4},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _parse_feedback(raw: str) -> dict:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    return {
        "went_well": [str(x) for x in data.get("went_well", [])][:2],
        "try_next": [str(x) for x in data.get("try_next", [])][:1],
    }


async def generate_feedback(transcript: list[dict], scenario_title: str) -> dict:
    convo = "\n".join(f"{t['speaker']}: {t['text']}" for t in transcript if t.get("text"))
    messages = [
        {"role": "system", "content": FEEDBACK_SYSTEM},
        {
            "role": "user",
            "content": f"Scenario practiced: {scenario_title}\n\nTranscript:\n{convo}\n\nGive the feedback JSON now.",
        },
    ]
    providers = [
        ("ollama", OLLAMA_BASE, OLLAMA_KEY, OLLAMA_MODEL),
        ("groq", GROQ_BASE, GROQ_KEY, GROQ_MODEL),
    ]
    for name, base, key, model in providers:
        if not key:
            log_event("feedback_provider_skipped", provider=name, reason="no api key set")
            continue
        try:
            raw = await _chat(base, key, model, messages)
            log_event("feedback_generated", provider=name)
            return _parse_feedback(raw)
        except Exception as e:
            log_event("feedback_provider_failed", provider=name, error=str(e)[:200])

    # Static, honest fallback so the user never sees an error wall.
    return {
        "went_well": [
            "You showed up and practiced out loud, which is the hardest part.",
            "You stayed with the conversation from start to finish.",
        ],
        "try_next": ["Next time you could try this same scenario once more, at any pace you like."],
    }

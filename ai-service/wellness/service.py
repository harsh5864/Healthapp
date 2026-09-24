"""Wellness trend and journal analysis service powered by OpenRouter LLM.

Provides empathetic, pattern-based observations for mood, stress, energy and sleep,
integrating journal entries with strict non-diagnostic clinical boundaries.
"""

from __future__ import annotations

import logging
from typing import Any

from services.openrouter_client import openrouter_client
from services.settings import settings

logger = logging.getLogger(__name__)

WELLNESS_DISCLAIMER = (
    "These observations reflect self-reported trends and are for personal reflection only, "
    "not a clinical diagnosis. If changes persist or affect daily functioning, consider speaking "
    "with a qualified professional."
)


def analyze_wellness(
    entries: list[dict[str, Any]],
    avg_mood: float,
    avg_stress: float,
    avg_energy: float,
    avg_sleep: float,
) -> dict[str, Any]:
    """Generate empathetic trend insights and journal reflections via OpenRouter."""
    # 1. Fallback / mock mode
    if settings.ai_mode.lower() == "mock" or not openrouter_client.is_available:
        mood_str = "Stable / positive" if avg_mood >= 6.0 else "Lower recently"
        stress_str = "Lower recently" if avg_stress <= 4.0 else "Higher recently"
        sleep_str = "Steady" if avg_sleep >= 7.0 else "Slightly reduced"
        rule_analysis = (
            f"Your recent self-reported entries show mood at {avg_mood:.1f}/10, stress at {avg_stress:.1f}/10 "
            f"and average sleep of {avg_sleep:.1f} hours. {WELLNESS_DISCLAIMER}"
        )
        return {
            "moodTrend": mood_str,
            "stressTrend": stress_str,
            "sleepTrend": sleep_str,
            "analysis": rule_analysis,
            "provider": "wellness-rule-engine",
        }

    # 2. OpenRouter LLM Analysis
    try:
        journal_snippets = []
        for e in entries[:5]:
            j = (e.get("journalText") or "").strip()
            date = e.get("createdAt") or e.get("date") or "Recently"
            if j:
                journal_snippets.append(f"- [{date}] (Mood: {e.get('mood')}/10, Sleep: {e.get('sleepHours')}h): \"{j}\"")

        journal_context = "\n".join(journal_snippets) if journal_snippets else "No recent journal reflections provided."

        prompt = (
            "You are a supportive, mindful wellness companion for an everyday health app.\n"
            "Review the user's recent self-reported check-ins:\n"
            f"- Average Mood: {avg_mood:.1f}/10\n"
            f"- Average Stress: {avg_stress:.1f}/10\n"
            f"- Average Energy: {avg_energy:.1f}/10\n"
            f"- Average Sleep: {avg_sleep:.1f} hours/night\n"
            f"- Recent Journal Reflections:\n{journal_context}\n\n"
            "Analyze these patterns thoughtfully and return ONLY a valid JSON object matching:\n"
            "{\n"
            '  "moodTrend": "concise trend label (e.g. Positive & Stable, Rebounding, Variable) under 35 chars",\n'
            '  "stressTrend": "concise trend label (e.g. Low & Manageable, Mildly Elevated) under 35 chars",\n'
            '  "sleepTrend": "concise trend label (e.g. Restful & Consistent, Mild Sleep Deficit) under 35 chars",\n'
            '  "analysis": "2 concise paragraphs of warm, empathetic reflection highlighting patterns between sleep, stress, and mood, acknowledging journal thoughts, offering gentle mindfulness/lifestyle thoughts. Conclude with a reminder that these are personal reflections, not a clinical diagnosis."\n'
            "}\n"
            "Guardrail: NEVER provide psychiatric diagnoses (such as depression, anxiety disorder, insomnia). Always remain supportive and non-clinical."
        )

        messages = [
            {"role": "system", "content": "You are an empathetic, non-diagnostic wellness pattern companion."},
            {"role": "user", "content": prompt},
        ]

        raw_response = openrouter_client.chat_completion(messages, max_tokens=600, temperature=0.3)
        parsed = openrouter_client.parse_json_response(raw_response)

        mood_trend = str(parsed.get("moodTrend") or "Stable / Positive")[:40]
        stress_trend = str(parsed.get("stressTrend") or "Manageable")[:40]
        sleep_trend = str(parsed.get("sleepTrend") or "Steady")[:40]
        analysis_text = str(parsed.get("analysis") or "").strip()

        if "diagnosis" not in analysis_text.lower():
            analysis_text = f"{analysis_text}\n\n{WELLNESS_DISCLAIMER}"

        return {
            "moodTrend": mood_trend,
            "stressTrend": stress_trend,
            "sleepTrend": sleep_trend,
            "analysis": analysis_text,
            "provider": f"openrouter/{openrouter_client.model}",
        }
    except Exception as exc:
        logger.warning("OpenRouter wellness analysis failed: %s; falling back to rule engine", exc)
        mood_str = "Stable / positive" if avg_mood >= 6.0 else "Lower recently"
        stress_str = "Lower recently" if avg_stress <= 4.0 else "Higher recently"
        sleep_str = "Steady" if avg_sleep >= 7.0 else "Slightly reduced"
        return {
            "moodTrend": mood_str,
            "stressTrend": stress_str,
            "sleepTrend": sleep_str,
            "analysis": f"Your recent self-reported entries show mood at {avg_mood:.1f}/10, stress at {avg_stress:.1f}/10 and average sleep of {avg_sleep:.1f} hours. {WELLNESS_DISCLAIMER}",
            "provider": "wellness-rule-engine",
        }

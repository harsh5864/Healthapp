"""Menta API Service: Holistic Mind, Energy, Activity & Stress Intelligence Engine.

Provides deep multi-dimensional synthesis across the four key vitality pillars:
Mood, Energy, Physical Activity, and Stress resilience, powered by OpenRouter LLM.
"""

from __future__ import annotations

import logging
from typing import Any

from services.openrouter_client import openrouter_client
from services.settings import settings

logger = logging.getLogger(__name__)

MENTA_DISCLAIMER = (
    "Menta observations represent holistic wellness patterns across mood, energy, activity, and stress. "
    "They are designed for mindful self-reflection and do not substitute for professional psychiatric or psychological care."
)


def calculate_menta_metrics(
    avg_mood: float,
    avg_stress: float,
    avg_energy: float,
    avg_activity: float,
) -> dict[str, Any]:
    """Calculate rule-based holistic mind-body indicators and wellness index."""
    # Composite Wellness Score (0 - 100)
    # Higher mood (+), higher energy (+), higher activity (+), lower stress (-)
    mood_norm = (avg_mood / 10.0) * 35.0          # up to 35 pts
    energy_norm = (avg_energy / 10.0) * 25.0      # up to 25 pts
    activity_norm = (avg_activity / 10.0) * 20.0  # up to 20 pts
    stress_norm = ((10.0 - avg_stress) / 10.0) * 20.0  # up to 20 pts
    composite_score = int(round(mood_norm + energy_norm + activity_norm + stress_norm))
    wellness_score = max(35, min(99, composite_score))

    # Mood State
    if avg_mood >= 7.5:
        mood_state = "Uplifted & Harmonious"
    elif avg_mood >= 5.5:
        mood_state = "Balanced & Grounded"
    else:
        mood_state = "Vulnerable / Low Mood"

    # Energy Level
    if avg_energy >= 7.5:
        energy_level = "High Sustained Vitality"
    elif avg_energy >= 5.5:
        energy_level = "Steady & Moderate"
    else:
        energy_level = "Depleted / Sluggish"

    # Stress Level
    if avg_stress <= 3.5:
        stress_level = "Low & Well Regulated"
    elif avg_stress <= 6.5:
        stress_level = "Moderate & Manageable"
    else:
        stress_level = "Elevated Stress Load"

    # Activity Impact
    if avg_activity >= 7.0:
        activity_impact = "High movement providing a potent neurological buffer against daily stress."
    elif avg_activity >= 4.5:
        activity_impact = "Moderate regular activity supporting steady neurochemical balance."
    else:
        activity_impact = "Gentle activity levels; increasing daily movement could significantly lift energy and mood."

    return {
        "wellnessScore": wellness_score,
        "moodState": mood_state,
        "energyLevel": energy_level,
        "stressLevel": stress_level,
        "activityImpact": activity_impact,
    }


def analyze_menta(
    entries: list[dict[str, Any]],
    avg_mood: float,
    avg_stress: float,
    avg_energy: float,
    avg_activity: float,
) -> dict[str, Any]:
    """Generate specialized Menta multi-pillar synthesis across mood, energy, activity, and stress."""
    metrics = calculate_menta_metrics(avg_mood, avg_stress, avg_energy, avg_activity)

    # 1. Mock mode or OpenRouter unavailable fallback
    if settings.ai_mode.lower() == "mock" or not openrouter_client.is_available:
        summary_text = (
            f"Menta holistic index assesses your mind-body equilibrium at {metrics['wellnessScore']}/100. "
            f"Your current state reflects {metrics['moodState'].lower()} with {metrics['energyLevel'].lower()} "
            f"and a {metrics['stressLevel'].lower()} (Stress: {avg_stress:.1f}/10). "
            f"{metrics['activityImpact']} "
            f"Balancing active pacing with restorative mental space sustains emotional longevity.\n\n{MENTA_DISCLAIMER}"
        )
        return {
            "mentaSummary": summary_text,
            "wellnessScore": metrics["wellnessScore"],
            "moodState": metrics["moodState"],
            "energyLevel": metrics["energyLevel"],
            "stressLevel": metrics["stressLevel"],
            "activityImpact": metrics["activityImpact"],
            "mindfulnessAction": "Take a 5-minute pause for physiologic sigh breathing (two quick inhales through the nose, one long exhale through the mouth).",
            "provider": "Menta-Engine (Local)",
        }

    # 2. OpenRouter LLM Menta Synthesis
    try:
        entry_summaries = []
        for i, e in enumerate(entries[:5]):
            m = e.get("mood", avg_mood)
            st = e.get("stress", avg_stress)
            en = e.get("energy", avg_energy)
            act = e.get("activity", avg_activity)
            j = (e.get("journalText") or "").strip()
            date = e.get("createdAt") or f"Entry {i+1}"
            entry_summaries.append(
                f"- [{date}] Mood: {m}/10, Energy: {en}/10, Activity: {act}/10, Stress: {st}/10"
                + (f" | Journal: \"{j}\"" if j else "")
            )

        entries_str = "\n".join(entry_summaries) if entry_summaries else "Baseline metrics provided."

        prompt = (
            "You are Menta, an empathetic, cutting-edge AI specializing in mental wellness, cognitive stamina, "
            "physical movement feedback, and stress resilience.\n"
            "Review the user's recent mind-body check-ins:\n"
            f"- Average Mood: {avg_mood:.1f}/10\n"
            f"- Average Energy: {avg_energy:.1f}/10\n"
            f"- Average Physical Activity: {avg_activity:.1f}/10\n"
            f"- Average Stress: {avg_stress:.1f}/10\n"
            f"- Menta Baseline Score: {metrics['wellnessScore']}/100\n"
            f"- Recent Check-in Stream:\n{entries_str}\n\n"
            "Synthesize these four interconnected pillars (Mood, Energy, Activity, Stress) thoughtfully. "
            "Return ONLY a valid JSON object matching:\n"
            "{\n"
            '  "mentaSummary": "2 rich, empathetic paragraphs exploring the feedback loops between physical activity, mental fatigue, mood regulation, and stress loads. Highlight strengths and suggest mindful reflections.",\n'
            '  "wellnessScore": int between 40 and 99,\n'
            '  "moodState": "concise mood label (e.g. Uplifted & Grounded, Centered, Sluggish / Low, Variable)",\n'
            '  "energyLevel": "concise energy label (e.g. High Vitality, Balanced, Afternoon Fatigue)",\n'
            '  "stressLevel": "concise stress label (e.g. Low & Regulated, Manageable Load, Heightened Tension)",\n'
            '  "activityImpact": "1 clear sentence explaining how their activity level directly impacts their stress and mood",\n'
            '  "mindfulnessAction": "1 concrete, actionable 5-minute somatic or mindfulness exercise (e.g. sensory grounding, box breathing, posture reset, mindful walk)"\n'
            "}\n"
            "Guardrail: NEVER offer psychiatric diagnostic labels (e.g., major depressive disorder, clinical anxiety, PTSD). Remain strictly supportive, observational, and preventive."
        )

        messages = [
            {"role": "system", "content": "You are Menta, a personalized mind, energy, activity, and stress wellness intelligence AI."},
            {"role": "user", "content": prompt},
        ]

        raw_resp = openrouter_client.chat_completion(messages, max_tokens=750, temperature=0.3)
        parsed = openrouter_client.parse_json_response(raw_resp)

        summary_out = str(parsed.get("mentaSummary") or "").strip()
        if "diagnosis" not in summary_out.lower():
            summary_out = f"{summary_out}\n\n{MENTA_DISCLAIMER}"

        action = str(parsed.get("mindfulnessAction") or "").strip()
        if not action:
            action = "Practice 3 minutes of 4-7-8 breathing to downregulate sympathetic nervous system arousal."

        return {
            "mentaSummary": summary_out,
            "wellnessScore": int(parsed.get("wellnessScore", metrics["wellnessScore"])),
            "moodState": str(parsed.get("moodState", metrics["moodState"])),
            "energyLevel": str(parsed.get("energyLevel", metrics["energyLevel"])),
            "stressLevel": str(parsed.get("stressLevel", metrics["stressLevel"])),
            "activityImpact": str(parsed.get("activityImpact", metrics["activityImpact"])),
            "mindfulnessAction": action,
            "provider": f"Menta via OpenRouter ({openrouter_client.model})",
        }

    except Exception as exc:
        logger.warning("Menta LLM generation failed: %s; using rule engine", exc)
        return {
            "mentaSummary": (
                f"Menta holistic assessment places your vitality index at {metrics['wellnessScore']}/100. "
                f"Your patterns reveal {metrics['moodState'].lower()}, {metrics['energyLevel'].lower()}, and {metrics['stressLevel'].lower()}. "
                f"{metrics['activityImpact']} "
                f"Small moments of conscious recovery compound into lasting emotional resilience.\n\n{MENTA_DISCLAIMER}"
            ),
            "wellnessScore": metrics["wellnessScore"],
            "moodState": metrics["moodState"],
            "energyLevel": metrics["energyLevel"],
            "stressLevel": metrics["stressLevel"],
            "activityImpact": metrics["activityImpact"],
            "mindfulnessAction": "Dedicate 5 minutes to progressive shoulder and neck relaxation paired with slow nasal breaths.",
            "provider": "Menta-Engine (Local)",
        }

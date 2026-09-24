"""SleepLM API Service: Clinical-grade sleep architecture and circadian rhythm intelligence.

Analyzes self-reported sleep duration, night-to-night variance, sleep debt, and restorative
recovery patterns using OpenRouter LLM with empathetic non-diagnostic sleep hygiene insights.
"""

from __future__ import annotations

import logging
from typing import Any

from services.openrouter_client import openrouter_client
from services.settings import settings

logger = logging.getLogger(__name__)

SLEEP_TARGET_HOURS = 8.0

SLEEPLM_DISCLAIMER = (
    "SleepLM observations reflect self-reported sleep logs and circadian habits. "
    "They are for personal lifestyle reflection and do not constitute clinical diagnosis of insomnia, sleep apnea, or other sleep disorders."
)


def calculate_sleep_metrics(entries: list[dict[str, Any]], avg_sleep: float) -> dict[str, Any]:
    """Calculate rule-based sleep metrics like debt, variance, and recovery score."""
    sleep_values = []
    for e in entries:
        s = e.get("sleepHours")
        if s is not None:
            try:
                sleep_values.append(float(s))
            except (ValueError, TypeError):
                pass

    if not sleep_values:
        sleep_values = [avg_sleep] if avg_sleep > 0 else [7.0]

    # Sleep debt relative to 8h/day baseline
    latest_days = min(len(sleep_values), 7)
    recent_values = sleep_values[:latest_days]
    total_recent = sum(recent_values)
    expected_recent = latest_days * SLEEP_TARGET_HOURS
    debt_diff = total_recent - expected_recent  # negative is deficit

    if debt_diff >= 0.5:
        sleep_debt = f"+{debt_diff:.1f}h (Surplus / Rested)"
    elif debt_diff >= -1.0:
        sleep_debt = "Optimal (Balanced)"
    else:
        sleep_debt = f"{debt_diff:.1f}h (Deficit)"

    # Sleep consistency (variance)
    if len(recent_values) >= 2:
        variance = sum((x - avg_sleep) ** 2 for x in recent_values) / len(recent_values)
        if variance < 0.8:
            consistency = "High Consistency"
        elif variance < 2.5:
            consistency = "Moderate Variability"
        else:
            consistency = "Irregular Schedule"
    else:
        consistency = "Consistent Baseline"

    # Sleep Score (0-100)
    # 7-9 hours ideal = high score; penalize extreme variance and severe deficits
    base_score = 85
    duration_delta = abs(avg_sleep - SLEEP_TARGET_HOURS)
    duration_penalty = min(35, duration_delta * 12)
    debt_penalty = min(20, abs(min(0, debt_diff)) * 3)
    sleep_score = max(40, min(98, int(base_score - duration_penalty - debt_penalty + 10)))

    if avg_sleep >= 7.5:
        restorative = "Deep & Restorative"
    elif avg_sleep >= 6.5:
        restorative = "Adequate Recovery"
    else:
        restorative = "Fragmented / Reduced Rest"

    return {
        "sleepScore": sleep_score,
        "sleepDebt": sleep_debt,
        "sleepConsistency": consistency,
        "restorativeQuality": restorative,
    }


def analyze_sleeplm(
    entries: list[dict[str, Any]],
    avg_sleep: float,
) -> dict[str, Any]:
    """Generate specialized SleepLM sleep summaries and restorative recommendations."""
    metrics = calculate_sleep_metrics(entries, avg_sleep)

    # 1. Mock mode or OpenRouter unavailable fallback
    if settings.ai_mode.lower() == "mock" or not openrouter_client.is_available:
        summary_text = (
            f"Over your recent check-ins, your sleep duration averaged {avg_sleep:.1f} hours per night with a {metrics['sleepDebt']} debt status. "
            f"Your circadian rhythm indicates {metrics['sleepConsistency'].lower()} and {metrics['restorativeQuality'].lower()}. "
            f"Maintaining consistent sleep and wake timing reinforces slow-wave restorative sleep.\n\n{SLEEPLM_DISCLAIMER}"
        )
        return {
            "sleepSummary": summary_text,
            "sleepScore": metrics["sleepScore"],
            "sleepDebt": metrics["sleepDebt"],
            "sleepConsistency": metrics["sleepConsistency"],
            "restorativeQuality": metrics["restorativeQuality"],
            "recommendations": [
                "Keep bed and wake times within a 30-minute window, even on weekends.",
                "Dim ambient overhead lights 60 minutes before bedtime to encourage natural melatonin release.",
                "Get 10-15 minutes of natural sunlight within 1 hour of waking to anchor your circadian clock."
            ],
            "provider": "SleepLM-Engine (Local)",
        }

    # 2. OpenRouter LLM SleepLM Synthesis
    try:
        sleep_history_snippets = []
        for i, e in enumerate(entries[:7]):
            s = e.get("sleepHours", avg_sleep)
            m = e.get("mood", "-")
            stress = e.get("stress", "-")
            date = e.get("createdAt") or f"Day {i+1}"
            sleep_history_snippets.append(f"- {date}: {s}h sleep (Mood: {m}/10, Stress: {stress}/10)")

        history_str = "\n".join(sleep_history_snippets) if sleep_history_snippets else f"Average {avg_sleep:.1f} hours."

        prompt = (
            "You are SleepLM, an advanced AI sleep medicine and circadian rhythm intelligence engine.\n"
            "Review the user's recent sleep patterns:\n"
            f"- Average Sleep: {avg_sleep:.1f} hours/night\n"
            f"- Sleep Score Benchmark: {metrics['sleepScore']}/100\n"
            f"- Sleep Debt Status: {metrics['sleepDebt']}\n"
            f"- Schedule Consistency: {metrics['sleepConsistency']}\n"
            f"- Recent Night Logs:\n{history_str}\n\n"
            "Produce an insightful, highly engaging SleepLM intelligence brief. Return ONLY valid JSON in this exact structure:\n"
            "{\n"
            '  "sleepSummary": "2 concise, articulate paragraphs evaluating circadian rhythm alignment, restorative sleep architecture, and how recent sleep length influences daily cognitive energy. Conclude with a warm supportive observation.",\n'
            '  "sleepScore": int between 40 and 99,\n'
            '  "sleepDebt": "concise label (e.g. Optimal, -1.5h Deficit, +0.5h Rested)",\n'
            '  "sleepConsistency": "concise label (e.g. Highly Consistent, Slight Schedule Drift, Irregular)",\n'
            '  "restorativeQuality": "concise label (e.g. Deep & Restorative, Adequate Recovery, Fragmented)",\n'
            '  "recommendations": [\n'
            '    "Actionable, science-backed sleep hygiene recommendation 1",\n'
            '    "Actionable, science-backed sleep hygiene recommendation 2",\n'
            '    "Actionable, science-backed sleep hygiene recommendation 3"\n'
            '  ]\n'
            "}\n"
            "Guardrail: NEVER diagnose medical conditions like clinical insomnia, narcolepsy, or sleep apnea."
        )

        messages = [
            {"role": "system", "content": "You are SleepLM, a specialized sleep architecture and circadian wellness AI."},
            {"role": "user", "content": prompt},
        ]

        raw_resp = openrouter_client.chat_completion(messages, max_tokens=700, temperature=0.3)
        parsed = openrouter_client.parse_json_response(raw_resp)

        summary_out = str(parsed.get("sleepSummary") or "").strip()
        if "diagnosis" not in summary_out.lower():
            summary_out = f"{summary_out}\n\n{SLEEPLM_DISCLAIMER}"

        recs = parsed.get("recommendations")
        if not isinstance(recs, list) or not recs:
            recs = [
                "Establish a consistent 30-minute wind-down routine without screen exposure.",
                "Ensure your sleeping space is cool (around 65°F / 18°C) and completely dark.",
                "Limit caffeine and heavy meals within 6 hours of bedtime."
            ]
        else:
            recs = [str(r) for r in recs[:4]]

        return {
            "sleepSummary": summary_out,
            "sleepScore": int(parsed.get("sleepScore", metrics["sleepScore"])),
            "sleepDebt": str(parsed.get("sleepDebt", metrics["sleepDebt"])),
            "sleepConsistency": str(parsed.get("sleepConsistency", metrics["sleepConsistency"])),
            "restorativeQuality": str(parsed.get("restorativeQuality", metrics["restorativeQuality"])),
            "recommendations": recs,
            "provider": f"SleepLM via OpenRouter ({openrouter_client.model})",
        }

    except Exception as exc:
        logger.warning("SleepLM LLM generation failed: %s; using rule engine", exc)
        return {
            "sleepSummary": (
                f"SleepLM analysis shows an average sleep duration of {avg_sleep:.1f} hours with {metrics['sleepConsistency'].lower()} "
                f"and {metrics['restorativeQuality'].lower()}. Your sleep debt sits at {metrics['sleepDebt']}. "
                f"Focusing on regular bedtime anchors will stabilize circadian rhythm and energy levels.\n\n{SLEEPLM_DISCLAIMER}"
            ),
            "sleepScore": metrics["sleepScore"],
            "sleepDebt": metrics["sleepDebt"],
            "sleepConsistency": metrics["sleepConsistency"],
            "restorativeQuality": metrics["restorativeQuality"],
            "recommendations": [
                "Maintain steady sleep and wake windows across consecutive days.",
                "Create a dark, cool sleeping environment to support deep restorative phases.",
                "Engage in light stretching or progressive muscle relaxation before bed."
            ],
            "provider": "SleepLM-Engine (Local)",
        }

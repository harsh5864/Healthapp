"""Health chat assistant and safety reasoning engine for AI Health Companion.

Strictly follows non-diagnostic medical safety standards:
- Immediate emergency escalation for red-flag symptoms.
- Non-diagnostic educational explanations ("can be associated with").
- Structured symptom breakdown (Possibilities, Questions, General Care, When to seek care).
- Mandatory medical disclaimers on all outputs.
- Support for Gemini / OpenAI LLM APIs when keys are configured in environment.
- High-grade deterministic safety engine when in mock/development mode.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import re
from typing import Any
from dotenv import load_dotenv
import requests
from services.openrouter_client import openrouter_client

# Load root environment variables if available
root_env = Path(__file__).resolve().parents[2] / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
load_dotenv()

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER = (
    "Medical disclaimer: This information is for general educational purposes only and "
    "does not constitute medical advice, diagnosis, or treatment. Always consult a qualified "
    "healthcare provider for any personal medical concerns."
)

EMERGENCY_DISCLAIMER = (
    "URGENT NOTICE: These symptoms may indicate a potentially life-threatening medical emergency. "
    "Please contact your local emergency services (e.g. 911/112/999) or proceed immediately to the nearest "
    "emergency room. Do not wait for an online response or attempt to drive yourself if you are feeling unwell."
)

# Red-flag symptom patterns that warrant immediate emergency referral
RED_FLAG_PATTERNS = [
    (r"\b(chest\s+pain|chest\s+pressure|crushing\s+chest|tightness\s+in\s+chest)\b", "Severe chest pain or chest pressure"),
    (r"\b(can'?t\s+breathe|cannot\s+breathe|severe\s+difficulty\s+breathing|choking|gasping\s+for\s+air|shortness\s+of\s+breath\s+at\s+rest)\b", "Severe difficulty breathing"),
    (r"\b(passed\s+out|lost\s+consciousness|blacked\s+out|fainted\s+and\s+unresponsive|loss\s+of\s+consciousness)\b", "Loss of consciousness or fainting"),
    (r"\b(face\s+droop(ing)?|facial\s+droop|slurred\s+speech|slurring\s+words|one-sided\s+weakness|arm\s+weakness\s+sudden|stroke\s+symptoms)\b", "Potential signs of acute stroke"),
    (r"\b(anaphylaxis|throat\s+swelling|tongue\s+swollen|lips\s+swollen\s+and\s+breathing|allergic\s+reaction\s+breathing)\b", "Severe allergic reaction / anaphylaxis"),
    (r"\b(uncontrolled\s+bleeding|coughing\s+up\s+large\s+blood|vomiting\s+large\s+blood|spurting\s+blood)\b", "Uncontrolled or severe bleeding"),
    (r"\b(worst\s+headache\s+of\s+(my\s+)?life|thunderclap\s+headache|sudden\s+paralysis|sudden\s+loss\s+of\s+vision)\b", "Sudden severe neurological deficit"),
]


class HealthChatAssistant:
    """Manages chat requests with medical safety verification and multi-provider execution."""

    def __init__(self) -> None:
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.ai_mode = os.getenv("AI_MODE", "mock").lower()

    def check_red_flags(self, text: str) -> tuple[bool, str]:
        """Detect urgent life-threatening symptoms requiring immediate emergency care."""
        lower_text = text.lower()
        for pattern, description in RED_FLAG_PATTERNS:
            if re.search(pattern, lower_text):
                return True, description
        return False, ""


    def _call_openrouter_api(self, message: str, history: list[dict[str, str]]) -> str:
        """Call OpenRouter Chat Completions API with medical safety system instructions."""
        system_instruction = (
            "You are an AI Health Information Assistant for general educational support. "
            "You must strictly follow these clinical safety guardrails:\n"
            "1. NEVER claim to diagnose any condition with certainty or replace a physician.\n"
            "2. NEVER prescribe medications or recommend specific dosages.\n"
            "3. Use cautious phrasing such as 'can be associated with' or 'common potential causes include'.\n"
            "4. Ask relevant follow-up questions about onset, duration, and severity.\n"
            "5. If the user presents symptoms, organize your response into clear sections:\n"
            "   - Potential Causes (general educational possibilities)\n"
            "   - What to Monitor (onset, duration, triggers, severity)\n"
            "   - General Home Care (rest, hydration, safe comfort measures)\n"
            "   - When to Seek Medical Attention (specific warning signs to watch for)\n"
            "6. Always conclude with a brief medical disclaimer."
        )

        messages = [{"role": "system", "content": system_instruction}]
        for item in history[-10:]:
            role = "user" if item.get("sender", "").upper() == "USER" else "assistant"
            messages.append({"role": role, "content": item.get("message", "")})

        messages.append({"role": "user", "content": message})

        reply_text = openrouter_client.chat_completion(messages, max_tokens=700, temperature=0.3)
        if "medical disclaimer" not in reply_text.lower() and "medical advice" not in reply_text.lower():
            reply_text = f"{reply_text}\n\n_{MEDICAL_DISCLAIMER}_"
        return reply_text

    def _call_gemini_api(self, message: str, history: list[dict[str, str]]) -> str:
        """Call Gemini REST API for conversational generation."""
        api_key = self.gemini_api_key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        system_instruction = (
            "You are an AI Health Information Assistant for general educational support. "
            "You must follow strict clinical safety guardrails:\n"
            "1. NEVER claim to diagnose any condition with certainty or replace a physician.\n"
            "2. NEVER prescribe medications or recommend specific dosages.\n"
            "3. Use cautious phrasing such as 'can be associated with' or 'common potential causes include'.\n"
            "4. Ask relevant follow-up questions about onset, duration, and severity.\n"
            "5. If the user presents symptoms, organize your response into:\n"
            "   - What it could mean (general educational possibilities)\n"
            "   - Important details to consider (duration, triggers, severity)\n"
            "   - General supportive self-care\n"
            "   - When to seek professional medical evaluation\n"
            "6. Always conclude with a brief medical disclaimer."
        )

        contents = []
        for item in history[-10:]:
            role = "user" if item.get("sender", "").upper() == "USER" else "model"
            contents.append({"role": role, "parts": [{"text": item.get("message", "")}]})

        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800},
        }

        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                text_parts = candidates[0].get("content", {}).get("parts", [])
                if text_parts and "text" in text_parts[0]:
                    return text_parts[0]["text"].strip()
        logger.warning("Gemini API call returned status %s: %s", resp.status_code, resp.text[:200])
        raise RuntimeError(f"Gemini API returned {resp.status_code}")

    def _call_openai_api(self, message: str, history: list[dict[str, str]]) -> str:
        """Call OpenAI Chat Completions API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI Health Information Assistant providing cautious, educational guidance. "
                    "Do not diagnose conditions, prescribe medications, or replace doctors. Use phrases like "
                    "'can be associated with'. Highlight red flags and recommend professional care when appropriate."
                ),
            }
        ]

        for item in history[-10:]:
            role = "user" if item.get("sender", "").upper() == "USER" else "assistant"
            messages.append({"role": role, "content": item.get("message", "")})

        messages.append({"role": "user", "content": message})

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
        raise RuntimeError(f"OpenAI API returned {resp.status_code}")

    def _generate_educational_guidance(self, message: str, history: list[dict[str, str]]) -> str:
        """Produce structured, non-diagnostic guidance using the built-in clinical safety rule engine."""
        lowered = message.lower()

        # Check for specific symptom domains
        if any(w in lowered for w in ["headache", "migraine", "head pain"]):
            category = "Headache / Head discomfort"
            possibilities = (
                "Headaches can be associated with tension or stress, dehydration, lack of sleep, "
                "eye strain, sinus congestion, or less commonly, migraine."
            )
            follow_ups = (
                "- Where is the pain located (forehead, temples, or one side)?\n"
                "- How long has it lasted, and was the onset sudden or gradual?\n"
                "- Are you experiencing any accompanying sensitivity to light or sound, or nausea?"
            )
            care_advice = (
                "General supportive steps may include resting in a quiet, dimly lit space, "
                "sipping water to stay hydrated, and avoiding prolonged screen exposure."
            )
            red_flags = (
                "Seek urgent medical evaluation if the headache is sudden and explosive ('worst headache of life'), "
                "accompanied by high fever, stiff neck, confusion, vision changes, or numbness."
            )
        elif any(w in lowered for w in ["fever", "chills", "high temp", "temperature"]):
            category = "Fever / Elevated body temperature"
            possibilities = (
                "A fever is typically the immune system's physiological response to an underlying infection, "
                "most commonly viral (such as cold or flu) or bacterial."
            )
            follow_ups = (
                "- What is the highest measured temperature and how many days has it persisted?\n"
                "- Are you having respiratory symptoms, body aches, sore throat, or urinary discomfort?\n"
                "- Are you able to drink and hold down fluids?"
            )
            care_advice = (
                "Supportive care generally includes plentiful oral hydration (water, broths, electrolyte solutions), "
                "adequate bed rest, and wearing light, breathable clothing."
            )
            red_flags = (
                "Contact a doctor if fever exceeds 103°F (39.4°C) in adults, lasts more than three days, "
                "or occurs alongside a rash, stiff neck, shortness of breath, or persistent vomiting."
            )
        elif any(w in lowered for w in ["stomach", "abdominal", "belly", "nausea", "vomit", "cramps"]):
            category = "Abdominal / Gastrointestinal symptoms"
            possibilities = (
                "Abdominal discomfort can be associated with viral gastroenteritis, dietary irritation, indigestion, "
                "gas, constipation, stress, or localized inflammation."
            )
            follow_ups = (
                "- Is the discomfort sharp, dull, or cramping, and where is it located?\n"
                "- When did your symptoms begin relative to your last meal?\n"
                "- Have you noticed any changes in bowel habits, nausea, or vomiting?"
            )
            care_advice = (
                "Drinking small, frequent sips of clear fluids, eating bland foods (e.g. crackers, rice, bananas) "
                "when appetite permits, and avoiding greasy or acidic meals can support digestion."
            )
            red_flags = (
                "Seek immediate medical care if pain is severe, sudden, localized to the lower right abdomen, "
                "or accompanied by persistent vomiting, blood in stool, or inability to keep liquids down."
            )
        elif any(w in lowered for w in ["cough", "throat", "congestion", "cold", "runny nose"]):
            category = "Respiratory / Cold symptoms"
            possibilities = (
                "Cough and throat irritation can be associated with upper respiratory viral infections, seasonal allergies, "
                "dry indoor air, or post-nasal drip."
            )
            follow_ups = (
                "- Is the cough dry or productive (producing phlegm)?\n"
                "- How long have you experienced these symptoms?\n"
                "- Do you have an accompanying fever, ear pain, or sinus pressure?"
            )
            care_advice = (
                "Warm fluids (tea with honey for adults), staying well-hydrated, resting your voice, and using a "
                "cool-mist humidifier can help soothe throat irritation."
            )
            red_flags = (
                "Consult a healthcare professional if you experience difficulty breathing, chest tightness, coughing up blood, "
                "or symptoms that worsen significantly after initially improving."
            )
        elif any(w in lowered for w in ["tired", "fatigue", "exhausted", "sleep", "insomnia"]):
            category = "Fatigue / Sleep concerns"
            possibilities = (
                "Persistent fatigue can be associated with inadequate sleep quality, high chronic stress, nutritional gaps "
                "(such as iron or vitamin D deficiency), thyroid fluctuations, or recent viral illness."
            )
            follow_ups = (
                "- How many hours of restful sleep do you typically get each night?\n"
                "- Has this fatigue been gradual over months or sudden over days?\n"
                "- Have you experienced unplanned weight changes, mood shifts, or temperature intolerance?"
            )
            care_advice = (
                "Maintaining a consistent sleep schedule, limiting caffeine in the afternoon, ensuring moderate daily activity, "
                "and eating balanced meals with adequate hydration are foundational steps."
            )
            red_flags = (
                "Schedule an in-person appointment with a primary care clinician if fatigue is unrelenting, interferes with "
                "daily function, or is accompanied by unexplained weight loss or night sweats."
            )
        else:
            category = "General health inquiry"
            possibilities = (
                "Health symptoms can have multiple overlapping physical and lifestyle contributing factors. "
                "Without a physical examination and diagnostic testing, it is not possible to specify an exact cause."
            )
            follow_ups = (
                "- Could you describe when these symptoms first started and their progression?\n"
                "- What activities or circumstances make the symptoms better or worse?\n"
                "- Are you currently taking any prescription medications or managing existing conditions?"
            )
            care_advice = (
                "Keep a brief log of your symptoms (timing, triggers, intensity) to share with your healthcare provider. "
                "Prioritize baseline wellness: rest, balanced hydration, and gentle activity."
            )
            red_flags = (
                "Always seek prompt medical care if your symptoms are sudden, severe, worsening, or causing you concern."
            )

        response = (
            f"**Regarding: {category}**\n\n"
            f"**1. What it could mean:**\n{possibilities}\n\n"
            f"**2. Helpful questions to consider:**\n{follow_ups}\n\n"
            f"**3. General supportive measures:**\n{care_advice}\n\n"
            f"**4. When to seek medical evaluation:**\n{red_flags}\n\n"
            f"_{MEDICAL_DISCLAIMER}_"
        )
        return response

    def respond(self, message: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        """Generate response with medical safety verification."""
        clean_msg = message.strip()
        history = history or []

        if not clean_msg:
            return {
                "reply": "Please provide a health question or symptom description so I can provide helpful information.",
                "provider": "validation-guard",
                "isUrgent": False,
            }

        # 1. Immediate Red-Flag Emergency Screening
        is_urgent, red_flag_reason = self.check_red_flags(clean_msg)
        if is_urgent:
            logger.info("Red-flag condition detected: %s", red_flag_reason)
            urgent_reply = (
                f"**[IMMEDIATE EMERGENCY ATTENTION RECOMMENDED]**\n\n"
                f"You mentioned symptoms that could be associated with **{red_flag_reason}**.\n\n"
                f"{EMERGENCY_DISCLAIMER}\n\n"
                f"While you arrange emergency care, stay as calm as possible, do not exert yourself, "
                f"and ensure you are in a safe position where someone can assist you if needed.\n\n"
                f"_{MEDICAL_DISCLAIMER}_"
            )
            return {
                "reply": urgent_reply,
                "provider": "emergency-safety-guard",
                "isUrgent": True,
            }

        # 2. External LLM via OpenRouter (or Gemini / OpenAI)
        if self.openrouter_api_key:
            try:
                reply = self._call_openrouter_api(clean_msg, history)
                return {
                    "reply": reply,
                    "provider": f"openrouter/{self.openrouter_model}",
                    "isUrgent": False,
                }
            except Exception as exc:
                logger.warning("OpenRouter generation failed: %s; falling back to alternative or safety engine", exc)

        if self.ai_mode in {"real", "production"}:
            if self.gemini_api_key:
                try:
                    reply = self._call_gemini_api(clean_msg, history)
                    return {"reply": reply, "provider": "gemini-1.5-flash", "isUrgent": False}
                except Exception as exc:
                    logger.warning("Gemini generation failed: %s; falling back to safety engine", exc)

            if self.openai_api_key:
                try:
                    reply = self._call_openai_api(clean_msg, history)
                    return {"reply": reply, "provider": "openai-gpt-4o-mini", "isUrgent": False}
                except Exception as exc:
                    logger.warning("OpenAI generation failed: %s; falling back to safety engine", exc)

        # 3. Built-in Clinical Safety Engine
        fallback_reply = self._generate_educational_guidance(clean_msg, history)
        provider_label = "safety-assistant-engine"
        if self.ai_mode == "mock":
            provider_label = "mock-health-assistant"
            fallback_reply = f"[Development Mock Mode]\n\n{fallback_reply}"

        return {
            "reply": fallback_reply,
            "provider": provider_label,
            "isUrgent": False,
        }


# Singleton instance
_assistant_instance: HealthChatAssistant | None = None


def get_health_assistant() -> HealthChatAssistant:
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = HealthChatAssistant()
    return _assistant_instance

"""Centralized OpenRouter API client with exponential backoff and retry logic.

Supports text chat completions and multimodal vision analysis for produce/food
freshness checks and mental wellness trend generation.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import time
from typing import Any
import requests

from services.settings import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterClient:
    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model or "google/gemini-2.5-flash"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "AI Health Companion",
            "Content-Type": "application/json",
        }

    def _post_with_retry(self, payload: dict[str, Any], max_retries: int = 3, timeout: int = 25) -> dict[str, Any]:
        """Post request to OpenRouter with automatic backoff for rate limits / 429 admission control."""
        if not self.is_available:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        last_error = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(OPENROUTER_URL, headers=self._get_headers(), json=payload, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()

                # Handle 429 / admission control with backoff
                if resp.status_code in {429, 502, 503, 504}:
                    wait_sec = (attempt + 1) * 2
                    logger.warning("OpenRouter %s on attempt %s. Retrying in %ss: %s",
                                   resp.status_code, attempt + 1, wait_sec, resp.text[:200])
                    time.sleep(wait_sec)
                    continue

                logger.warning("OpenRouter returned error %s: %s", resp.status_code, resp.text[:300])
                raise RuntimeError(f"OpenRouter returned HTTP {resp.status_code}: {resp.text[:200]}")

            except requests.RequestException as exc:
                last_error = exc
                wait_sec = (attempt + 1) * 2
                logger.warning("OpenRouter connection error on attempt %s: %s. Retrying in %ss...",
                               attempt + 1, exc, wait_sec)
                time.sleep(wait_sec)

        raise RuntimeError(f"OpenRouter request failed after {max_retries} attempts: {last_error}")

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int = 800,
        temperature: float = 0.3,
    ) -> str:
        """Execute chat completion and return the assistant response string."""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = self._post_with_retry(payload)
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter returned no choices in response.")
        return choices[0].get("message", {}).get("content", "").strip()

    def vision_analysis(
        self,
        prompt: str,
        image_bytes: bytes,
        content_type: str = "image/jpeg",
        max_tokens: int = 600,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str:
        """Execute multimodal vision analysis on an image."""
        b64_image = base64.b64encode(image_bytes).decode("ascii")
        mime = content_type if content_type in {"image/jpeg", "image/png", "image/webp"} else "image/jpeg"
        data_url = f"data:{mime};base64,{b64_image}"

        target_model = model or self.model
        payload = {
            "model": target_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = self._post_with_retry(payload)
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenRouter vision returned no choices in response.")
        return choices[0].get("message", {}).get("content", "").strip()

    @staticmethod
    def parse_json_response(raw_text: str) -> dict[str, Any]:
        """Extract and parse JSON object from LLM response, handling markdown blocks."""
        cleaned = raw_text.strip()
        # Remove ```json ... ``` code fence if present
        code_fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if code_fence_match:
            cleaned = code_fence_match.group(1).strip()

        # Look for the outer { ... } bracket
        json_match = re.search(r"(\{[\s\S]*\})", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        return json.loads(cleaned)


# Global singleton instance
openrouter_client = OpenRouterClient()

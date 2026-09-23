"""Stable contracts that make AI providers replaceable in later phases."""

from abc import ABC, abstractmethod
from typing import Any


class FoodAnalysisService(ABC):
    @abstractmethod
    async def analyze_visible_condition(self, image_bytes: bytes, content_type: str) -> dict[str, Any]:
        """Return visible-condition observations, never a food-safety guarantee."""


class HealthChatService(ABC):
    @abstractmethod
    async def respond(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Return non-diagnostic, safety-aware informational guidance."""


class WellnessAnalysisService(ABC):
    @abstractmethod
    async def analyze_trends(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Return trend observations, never a mental-health diagnosis."""

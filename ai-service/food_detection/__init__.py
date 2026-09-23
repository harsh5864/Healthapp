"""Computer-vision and freshness detection adapters."""

from food_detection.service import analyze_image
from models.freshness_detector import FreshnessDetector, FreshnessResult

__all__ = ["analyze_image", "FreshnessDetector", "FreshnessResult"]

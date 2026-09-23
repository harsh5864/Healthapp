"""Freshness Detection Model Adapter.

Implements visual condition and freshness classification for fruits and vegetables.
Uses a domain-trained Vision Transformer (ViT) model (default: Aryaman9999/Freshness-Fruit_Vegies)
with surface color/bruising feature corroboration.

CRITICAL SAFETY MANDATE:
Visual analysis CANNOT detect bacteria, foodborne toxins, internal rot, or chemical
hazards. Freshness scores are visual-only estimates, never a guarantee of food safety.
"""

from dataclasses import dataclass, field
from io import BytesIO
import logging
import re
import sys
from typing import Any, Optional

import numpy as np
from PIL import Image

from services.settings import settings

logger = logging.getLogger(__name__)

SAFETY_DISCLAIMER = (
    "Visual condition estimate only. This does not guarantee food safety. "
    "Image analysis cannot detect bacteria, microbial toxins, chemical residues, or internal spoilage."
)


@dataclass
class FreshnessResult:
    """Standard result structure for freshness detection."""
    is_determined: bool
    produce_name: str
    state: str  # "fresh", "rotten", "uncertain", or "undetermined"
    condition: str  # "Appears Fresh (Visual Estimate)", "Potentially Spoiled / Degraded", etc.
    freshness_score: int  # 0 to 100 (conservative)
    confidence: float  # 0.0 to 1.0
    observations: str
    recommendation: str
    top_predictions: list[dict[str, Any]] = field(default_factory=list)
    surface_browning_pct: float = 0.0
    provider: str = "freshness-detector"


class FreshnessDetector:
    """Dedicated model adapter for produce freshness and spoilage estimation."""

    _instance: Optional["FreshnessDetector"] = None
    _pipeline = None
    _load_error: Optional[str] = None

    def __init__(self, model_id: Optional[str] = None):
        self.model_id = model_id or settings.freshness_model_id

    @classmethod
    def get_instance(cls) -> "FreshnessDetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self):
        """Lazy load the Hugging Face image-classification pipeline on CPU."""
        if self._pipeline is not None or self._load_error is not None:
            return self._pipeline

        if not settings.freshness_model_enabled or not self.model_id:
            self._load_error = "Freshness model is disabled or model ID is empty"
            logger.info("Freshness model not loaded: %s", self._load_error)
            return None

        try:
            from transformers import pipeline
            logger.info("Loading freshness detection model: %s", self.model_id)
            try:
                self._pipeline = pipeline("image-classification", model=self.model_id, device=-1, model_kwargs={"local_files_only": True})
            except Exception:
                self._pipeline = pipeline("image-classification", model=self.model_id, device=-1)
            logger.info("Freshness model loaded successfully.")
        except Exception as exc:
            self._load_error = f"Failed to load freshness model '{self.model_id}': {exc.__class__.__name__}: {exc}"
            logger.warning(self._load_error)
            self._pipeline = None

        return self._pipeline

    def is_available(self) -> bool:
        """Check whether the model is loaded or loadable."""
        return self._load_model() is not None

    def analyze_surface_features(self, image: Image.Image) -> dict[str, float]:
        """Compute visual surface characteristics including foreground segmentation and discoloration ratio."""
        try:
            resized = image.convert("RGB").resize((128, 128))
            arr = np.asarray(resized, dtype=np.float32)
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
            brightness = (r + g + b) / 3.0

            max_c = np.maximum(np.maximum(r, g), b)
            min_c = np.minimum(np.minimum(r, g), b)
            chroma = max_c - min_c

            # Neutral background (white/grey/cream plates, countertops, cutting boards)
            is_neutral_bg = (chroma < 18) & (brightness > 130)
            is_foreground = ~is_neutral_bg
            total_pixels = 128 * 128
            fg_count = int(np.sum(is_foreground))

            # Guard against vibrant produce tones being mistaken for rot
            is_vibrant_green = (g > r + 25) & (g > b + 25) & (g > 60)
            is_vibrant_red = (r > g + 40) & (r > b + 40) & (r > 80)
            is_vibrant_yellow = (r > 160) & (g > 130) & (b < 100)

            # Dark necrotic spots or severe rot
            is_dark_rot = (brightness < 60) & (~is_vibrant_green) & (~is_vibrant_red)
            # Brown bruising, decay, or heavy speckling
            is_brown_bruise = (
                (r > 50) & (r < 165) & (g > 25) & (g < 115) & (b < 80)
                & (r > g + 8) & (g >= b * 0.7)
                & (~is_vibrant_yellow) & (~is_vibrant_red)
            )

            discolored = (is_dark_rot | is_brown_bruise)
            total_discoloration = float(np.sum(discolored) / total_pixels) * 100.0
            fg_discoloration = float(np.sum(discolored & is_foreground) / fg_count) * 100.0 if fg_count > 0 else total_discoloration
            effective_browning = max(total_discoloration, fg_discoloration * 0.65)

            return {
                "discoloration_pct": round(effective_browning, 1),
                "total_discoloration_pct": round(total_discoloration, 1),
                "fg_discoloration_pct": round(fg_discoloration, 1),
            }
        except Exception as exc:
            logger.debug("Surface feature extraction skipped: %s", exc)
            return {"discoloration_pct": 0.0, "total_discoloration_pct": 0.0, "fg_discoloration_pct": 0.0}

    def parse_label(self, raw_label: str) -> tuple[str, str]:
        """Parse raw model class label into (state, produce_name).

        Handles classes like:
        - 'FreshApple' -> ('fresh', 'Apple')
        - 'RottenTomato' -> ('rotten', 'Tomato')
        - 'fresh banana' -> ('fresh', 'Banana')
        - 'Tomato_rotten' -> ('rotten', 'Tomato')
        """
        cleaned = raw_label.strip()
        lower = cleaned.lower()

        # Format: FreshTomato / RottenTomato
        if lower.startswith("fresh"):
            item = cleaned[5:].strip(" _-")
            return "fresh", item.title() if item else "Produce"
        if lower.startswith("rotten") or lower.startswith("spoiled"):
            item = re.sub(r"^(rotten|spoiled)", "", cleaned, flags=re.IGNORECASE).strip(" _-")
            return "rotten", item.title() if item else "Produce"

        # Format: Tomato_fresh / Potato_rotten
        if lower.endswith("_fresh") or lower.endswith(" fresh"):
            item = re.sub(r"[_ ]fresh$", "", cleaned, flags=re.IGNORECASE).strip()
            return "fresh", item.title() if item else "Produce"
        if lower.endswith("_rotten") or lower.endswith(" rotten"):
            item = re.sub(r"[_ ]rotten$", "", cleaned, flags=re.IGNORECASE).strip()
            return "rotten", item.title() if item else "Produce"

        return "uncertain", cleaned.title()

    def predict(self, image: Image.Image) -> FreshnessResult:
        """Run freshness classification and surface analysis on an image."""
        surface_features = self.analyze_surface_features(image)
        discoloration_pct = surface_features.get("discoloration_pct", 0.0)

        clf = self._load_model()
        if clf is None:
            reason = self._load_error or "Model is not configured or available."
            return FreshnessResult(
                is_determined=False,
                produce_name="Produce item",
                state="undetermined",
                condition="Unable to Determine",
                freshness_score=0,
                confidence=0.0,
                observations=f"Freshness detection model unavailable ({reason}). {SAFETY_DISCLAIMER}",
                recommendation="Inspect the food yourself for signs of spoilage; this service cannot guarantee food safety.",
                surface_browning_pct=discoloration_pct,
                provider=self.model_id or "freshness-model-unavailable",
            )

        try:
            predictions = clf(image, top_k=5)
            if not predictions:
                raise ValueError("Model returned empty prediction list.")

            top_pred = predictions[0]
            top_label = str(top_pred.get("label", ""))
            top_conf = float(top_pred.get("score", 0.0))
            state, produce_name = self.parse_label(top_label)

            # Extract both fresh and rotten confidence for this produce
            fresh_conf = 0.0
            rotten_conf = 0.0
            for p in predictions:
                lbl = str(p.get("label", ""))
                sc = float(p.get("score", 0.0))
                p_st, p_prod = self.parse_label(lbl)
                if p_prod.lower() == produce_name.lower() or produce_name.lower() in p_prod.lower():
                    if p_st == "fresh":
                        fresh_conf = max(fresh_conf, sc)
                    elif p_st == "rotten":
                        rotten_conf = max(rotten_conf, sc)

            # Fallback if label didn't directly match produce name
            if fresh_conf == 0.0 and state == "fresh":
                fresh_conf = top_conf
            if rotten_conf == 0.0 and state == "rotten":
                rotten_conf = top_conf

            # Produce observations & condition synthesis:
            # 1. Obvious Spoilage / Severe Browning / Dark Bruising
            if (
                discoloration_pct >= 30.0
                or rotten_conf >= 0.50
                or (rotten_conf >= 0.30 and discoloration_pct >= 20.0)
                or (fresh_conf - rotten_conf < 0.15 and discoloration_pct >= 22.0)
            ):
                score = max(15, min(32, int(42 - discoloration_pct * 0.35 - rotten_conf * 25)))
                condition = "Potentially Spoiled / Degraded"
                state = "rotten"
                obs = (
                    f"Freshness detection model and visual analysis identified notable signs of degradation, severe browning, "
                    f"or dark bruising ({discoloration_pct:.0f}% surface browning/speckling detected, rotten probability {rotten_conf:.0%})."
                )
                rec = (
                    "Visible signs indicate significant over-ripeness, dark bruising, or potential degradation. "
                    "Inspect closely; discard if the flesh is mushy, leaking, discolored internally, or smells fermented or foul."
                )

            # 2. Advanced Ripeness / Surface Discoloration / Mixed Indicators
            elif (
                discoloration_pct >= 18.0
                or (fresh_conf < 0.65 and rotten_conf > 0.20)
                or (fresh_conf - rotten_conf < 0.25)
            ):
                score = max(38, min(54, int(58 - discoloration_pct * 0.4 - rotten_conf * 15)))
                condition = "Uncertain / Mixed Condition"
                state = "uncertain"
                obs = (
                    f"Produce exhibits visible signs of advanced ripeness, freckling, or surface browning "
                    f"({discoloration_pct:.0f}% surface discoloration, freshness vs decay confidence {fresh_conf:.0%} to {rotten_conf:.0%})."
                )
                rec = (
                    "Produce shows signs of advanced ripening or surface blemishes. Inspect firmness and aroma before consuming; "
                    "discard any soft or decayed parts."
                )

            # 3. Fresh Produce (High fresh confidence, low rotten confidence, low browning)
            elif state == "fresh" and fresh_conf >= 0.65 and (fresh_conf - rotten_conf >= 0.25) and discoloration_pct < 18.0:
                score = min(92, max(72, int(68 + fresh_conf * 24 - discoloration_pct * 0.5)))
                condition = "Appears Fresh (Visual Estimate)"
                obs = (
                    f"Freshness detection model identified '{top_label}' with {fresh_conf:.0%} confidence. "
                    f"Visible surface characteristics appear clean with minimal discoloration ({discoloration_pct:.0f}%)."
                )
                rec = (
                    "Store properly according to produce type. Inspect the food yourself for mold, bruising, "
                    "or unusual odor before consuming; visual checks do not guarantee safety."
                )

            # 4. Inconclusive / General Fallback
            else:
                score = 50
                condition = "Uncertain / Mixed Condition"
                obs = (
                    f"Freshness detection model top result was '{top_label}' with moderate confidence ({top_conf:.0%}). "
                    f"Visual surface discoloration is {discoloration_pct:.0f}%. Visual indicators are inconclusive."
                )
                rec = "Inspect the food thoroughly. Check firmness, aroma, and surface texture before use."

            return FreshnessResult(
                is_determined=True,
                produce_name=produce_name,
                state=state,
                condition=condition,
                freshness_score=score,
                confidence=round(top_conf, 3),
                observations=f"{obs} {SAFETY_DISCLAIMER}",
                recommendation=rec,
                top_predictions=predictions,
                surface_browning_pct=discoloration_pct,
                provider=self.model_id,
            )

        except Exception as exc:
            logger.warning("Freshness prediction error: %s", exc)
            return FreshnessResult(
                is_determined=False,
                produce_name="Produce item",
                state="undetermined",
                condition="Unable to Determine",
                freshness_score=0,
                confidence=0.0,
                observations=f"Inference error in freshness model: {exc.__class__.__name__}. {SAFETY_DISCLAIMER}",
                recommendation="Inspect the food yourself; image analysis cannot guarantee food safety.",
                surface_browning_pct=discoloration_pct,
                provider=self.model_id,
            )


# CLI test runner
if __name__ == "__main__":
    detector = FreshnessDetector.get_instance()
    print("Testing FreshnessDetector...")
    print("Model ID:", detector.model_id)
    print("Loading model on CPU...")

    # Create synthetic test image if no argument provided
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        print(f"Loading image from: {img_path}")
        test_img = Image.open(img_path)
    else:
        print("Generating test apple image...")
        test_img = Image.new("RGB", (224, 224), (255, 255, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.ellipse((40, 40, 184, 184), fill=(220, 20, 20))
        draw.rectangle((108, 15, 116, 45), fill=(70, 45, 20))

    result = detector.predict(test_img)
    print("\n=== FRESHNESS DETECTION RESULT ===")
    print("Produce Name:   ", result.produce_name)
    print("Condition:      ", result.condition)
    print("Freshness Score:", f"{result.freshness_score}/100")
    print("Confidence:     ", f"{result.confidence:.1%}")
    print("Observations:   ", result.observations)
    print("Recommendation: ", result.recommendation)
    print("Provider:       ", result.provider)
    print("Top Predictions:", result.top_predictions[:3])
    print("==================================")

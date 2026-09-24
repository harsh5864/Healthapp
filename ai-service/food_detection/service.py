"""Pretrained image classification and visual freshness estimation for produce.

Combines:
1. Category identification: general visible object classification (e.g. google/mobilenet_v2_1.0_224)
2. Freshness evaluation: domain-trained produce freshness model via FreshnessDetector (e.g. Aryaman9999/Freshness-Fruit_Vegies)

CRITICAL SAFETY BOUNDARY:
Visual condition estimates CANNOT detect bacteria, toxins, chemical contamination,
or internal spoilage. Any freshness score is conservative and visual-only.
"""

from io import BytesIO
import logging
from typing import Any

from PIL import Image, UnidentifiedImageError

from models.freshness_detector import FreshnessDetector, SAFETY_DISCLAIMER
from services.settings import settings

logger = logging.getLogger(__name__)

_food_classifier = None
_food_model_error: str | None = None


def _get_food_classifier():
    """Lazy load food classification model (e.g. MobileNetV2)."""
    global _food_classifier, _food_model_error
    if _food_classifier is not None or _food_model_error is not None:
        return _food_classifier
    if not settings.food_model_enabled or not settings.food_model_id:
        _food_model_error = "FOOD_MODEL_ENABLED is false or FOOD_MODEL_ID is empty"
        return None
    try:
        from transformers import pipeline
        logger.info("Loading food classification model: %s", settings.food_model_id)
        try:
            _food_classifier = pipeline(
                "image-classification",
                model=settings.food_model_id,
                device=-1,
                model_kwargs={"local_files_only": True}
            )
        except Exception:
            _food_classifier = pipeline(
                "image-classification",
                model=settings.food_model_id,
                device=-1
            )
        logger.info("Food classification model loaded successfully.")
    except Exception as exc:
        _food_model_error = f"Could not load food model {settings.food_model_id}: {exc.__class__.__name__}: {exc}"
        logger.warning(_food_model_error)
    return _food_classifier


def _clean_food_name(raw_name: str) -> str:
    """Clean ImageNet labels (e.g. 'Granny Smith, Granny Smith apple' -> 'Granny Smith')."""
    first_part = raw_name.split(",")[0].strip()
    return first_part.title()


def _safe_result(width: int, height: int, image_format: str, observation: str, provider: str) -> dict[str, Any]:
    """Return the safe fallback response matching the existing API contract."""
    return {
        "foodName": "Produce item",
        "freshnessScore": 0,
        "condition": "Unable to Determine",
        "observations": f"Image received ({width}×{height}, {image_format}). {observation} {SAFETY_DISCLAIMER}",
        "recommendation": "Inspect the food yourself; this image-only service cannot guarantee food safety.",
        "provider": provider,
    }


from services.openrouter_client import openrouter_client

def analyze_image(image_bytes: bytes, filename: str | None, content_type: str) -> dict[str, Any]:
    """Run food identification and visual freshness evaluation."""
    # Explicit mock mode check
    if settings.ai_mode.lower() == "mock":
        return {
            "foodName": "Fresh Red Apple (Mock)",
            "freshnessScore": 88,
            "condition": "Appears Fresh (Mock)",
            "observations": (
                "Mock mode is active. This is a deterministic sample response for development and testing, "
                f"not real model inference. {SAFETY_DISCLAIMER}"
            ),
            "recommendation": "Mock recommendation: Inspect food thoroughly before consumption. Visual checks cannot guarantee safety.",
            "provider": "mock-food-service",
        }

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = image.size
        image_format = image.format or content_type.split("/")[-1]
    except Exception as exc:
        raise ValueError("The uploaded file is not a readable image.") from exc

    # 1. Primary: High-accuracy multimodal vision via OpenRouter Gemini
    if openrouter_client.is_available:
        try:
            vision_prompt = (
                "You are an AI Food Freshness and Produce Inspection specialist for a health application.\n"
                "Examine this food or produce image closely and assess visible condition, freshness, and quality.\n"
                "Respond ONLY with a valid JSON object matching this schema:\n"
                "{\n"
                '  "foodName": "Specific name of produce/food (e.g. Honeycrisp Apple, Cavendish Banana, Baby Spinach, Sliced Tomato). If not food, output \'Non-Produce Item\'.",\n'
                '  "freshnessScore": integer between 0 and 100 representing visible condition (e.g. 90-100 very fresh, 70-89 good/ripe, 40-69 fair/consume soon, 1-39 spoiling, 0 spoiled/non-food),\n'
                '  "condition": "Must be exactly one of: \'Appears Fresh\', \'Good / Ripe\', \'Fair - Consume Soon\', \'Spoiled / Past Prime\', or \'Unable to Determine\'",\n'
                '  "observations": "2-3 sentences describing visible traits: color uniformity, firmness clues, surface texture, blemishes, bruising, browning, or mold signs.",\n'
                '  "recommendation": "Practical advice for optimal storage, preparation, or safety inspection."\n'
                "}\n"
                "Safety rule: If the image is unclear or not produce, set condition to 'Unable to Determine' and freshnessScore to 0."
            )
            raw_res = openrouter_client.vision_analysis(
                prompt=vision_prompt,
                image_bytes=image_bytes,
                content_type=content_type,
                max_tokens=500,
                temperature=0.2,
            )
            parsed = openrouter_client.parse_json_response(raw_res)

            food_name = str(parsed.get("foodName") or "Produce item").strip()
            score = int(parsed.get("freshnessScore", 0))
            score = max(0, min(100, score))
            cond = str(parsed.get("condition") or "Unable to Determine").strip()
            obs = str(parsed.get("observations") or "").strip()
            rec = str(parsed.get("recommendation") or "Inspect thoroughly before eating.").strip()

            if SAFETY_DISCLAIMER not in obs:
                obs = f"{obs} {SAFETY_DISCLAIMER}".strip()

            return {
                "foodName": food_name,
                "freshnessScore": score,
                "condition": cond,
                "observations": obs,
                "recommendation": rec,
                "provider": f"openrouter/{openrouter_client.model}",
            }
        except Exception as exc:
            logger.warning("OpenRouter vision analysis encountered an error: %s; falling back to local models", exc)

    # 2. Secondary fallback: Local classification & FreshnessDetector models
    food_clf = _get_food_classifier()
    freshness_detector = FreshnessDetector.get_instance()

    detected_food_name = "Produce item"
    food_obs = ""
    provider_names = []

    # 1. Food Category Identification (MobileNetV2)
    if food_clf is not None:
        try:
            food_preds = food_clf(image, top_k=3)
            if food_preds:
                best_food = food_preds[0]
                raw_label = str(best_food.get("label", "unknown object"))
                food_conf = float(best_food.get("score", 0.0))
                detected_food_name = _clean_food_name(raw_label)
                provider_names.append(settings.food_model_id)

                alts = ", ".join(_clean_food_name(str(p.get("label", ""))) for p in food_preds[1:] if p.get("label"))
                food_obs = f"Visual classifier identified '{detected_food_name}' ({food_conf:.0%} confidence)."
                if alts:
                    food_obs += f" Other visible matches: {alts}."
        except Exception as exc:
            logger.warning("Food classification inference failed: %s", exc)
            food_obs = f"General food classification encountered an error ({exc.__class__.__name__})."

    # 2. Freshness Detection Model (FreshnessDetector)
    freshness_result = freshness_detector.predict(image)

    if freshness_result.is_determined:
        provider_names.append(freshness_result.provider)

        # Refine produce name if freshness model recognized specific produce
        if freshness_result.produce_name and freshness_result.produce_name.lower() not in {"produce", "item", "unknown"}:
            detected_food_name = freshness_result.produce_name

        combined_obs = f"{food_obs} {freshness_result.observations}".strip()

        return {
            "foodName": detected_food_name,
            "freshnessScore": freshness_result.freshness_score,
            "condition": freshness_result.condition,
            "observations": combined_obs,
            "recommendation": freshness_result.recommendation,
            "provider": " + ".join(provider_names) or "ai-service-freshness-models",
        }

    # Freshness model was not available or could not determine condition
    if food_clf is None:
        return _safe_result(
            width, height, image_format,
            "Configured AI models are currently unavailable.",
            "ai-service-fallback"
        )

    provider_names.append(settings.food_model_id)
    combined_obs = (
        f"{food_obs} Freshness detection model is unavailable or condition could not be established. "
        f"This model only identifies visible food categories and cannot determine spoilage. "
        f"{SAFETY_DISCLAIMER}".strip()
    )

    return {
        "foodName": detected_food_name,
        "freshnessScore": 0,
        "condition": "Unable to Determine",
        "observations": combined_obs,
        "recommendation": "Inspect the food yourself for mold, unusual odor, leakage, bruising, or other spoilage signs. The classifier cannot guarantee food safety.",
        "provider": " + ".join(provider_names) or settings.food_model_id or "ai-service",
    }

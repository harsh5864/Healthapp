"""Real food and meal nutritional intake analysis service.

Powered by Google Gemma 4 26B A4B (google/gemma-4-26b-a4b-it) via OpenRouter.
Analyzes real food, home-cooked dishes, and restaurant meals from photos
to calculate calorie estimates, macronutrients (protein, carbs, fat, fiber),
portion sizes, and health highlights for daily nutrient intake tracking.
"""

from __future__ import annotations

from io import BytesIO
import logging
from typing import Any

from PIL import Image

from services.openrouter_client import openrouter_client
from services.settings import settings

logger = logging.getLogger(__name__)

REAL_FOOD_DISCLAIMER = (
    "Caloric and macronutrient figures are estimated from visual portions. "
    "Preparation methods, oils, and hidden ingredients can affect actual values. "
    "Use these values as an everyday nutritional guide."
)


def analyze_real_food(image_bytes: bytes, filename: str | None, content_type: str) -> dict[str, Any]:
    """Analyze real cooked food, a plate, or a meal using Gemma 4 26B A4B."""
    # 1. Explicit mock mode check
    if settings.ai_mode.lower() == "mock":
        return {
            "foodName": "Mediterranean Chicken & Quinoa Bowl (Mock)",
            "portionSize": "1 standard bowl (~380g)",
            "calories": 490,
            "protein": 36.0,
            "carbs": 48.0,
            "fat": 15.0,
            "fiber": 7.0,
            "sugar": 4.0,
            "sodiumMg": 410,
            "freshnessScore": 90,
            "condition": "Nutrient-Dense Balanced Meal",
            "micronutrients": ["Vitamin C", "Iron", "Potassium", "Magnesium"],
            "observations": (
                "A balanced combination of lean grilled chicken breast, complex carbs from quinoa, "
                "and fiber-rich vegetables (cucumbers, cherry tomatoes, and kalamata olives)."
            ),
            "recommendation": "High protein and sustained energy release. Excellent post-exercise or lunch option.",
            "provider": "mock-meal-service",
            "scanType": "REAL_FOOD",
        }

    # Verify readable image
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = image.size
        image_format = image.format or content_type.split("/")[-1]
    except Exception as exc:
        raise ValueError("The uploaded file is not a readable image.") from exc

    # 2. OpenRouter with Gemma 4 26B A4B
    target_model = settings.packed_food_model or "google/gemma-4-26b-a4b-it"

    if openrouter_client.is_available:
        try:
            prompt = (
                "You are an expert Clinical Nutritionist and Dietary Intake Specialist analyzing a real food meal photo.\n"
                "Examine the dish, visible ingredients, and portion size.\n"
                "Calculate realistic estimated caloric and macronutrient values for an adult single portion.\n"
                "Respond in strictly valid JSON format matching this schema:\n"
                "{\n"
                '  "foodName": "Specific dish or food name (e.g. Grilled Salmon with Steamed Broccoli and Rice, Veggie Omelette with Avocado)",\n'
                '  "portionSize": "Estimated portion (e.g. 1 standard bowl ~350g, 2 medium tacos ~220g)",\n'
                '  "calories": integer representing estimated total calories (e.g. 450),\n'
                '  "protein": float grams of protein (e.g. 32.5),\n'
                '  "carbs": float grams of carbohydrates (e.g. 44.0),\n'
                '  "fat": float grams of total fat (e.g. 15.0),\n'
                '  "fiber": float grams of dietary fiber (e.g. 6.0),\n'
                '  "sugar": float grams of sugars (e.g. 3.5),\n'
                '  "sodiumMg": integer estimated sodium in milligrams (e.g. 380),\n'
                '  "healthScore": integer from 0 to 100 based on nutritional density and balance,\n'
                '  "condition": "Concise meal classification (e.g. Balanced Meal, High-Protein, Nutrient-Dense, Indulgent / High-Calorie)",\n'
                '  "micronutrients": ["Array of 3-4 notable vitamins or minerals (e.g. Vitamin C, Potassium, Iron, Omega-3)"],\n'
                '  "observations": "2-3 sentences reviewing the macronutrient balance and ingredient quality.",\n'
                '  "recommendation": "Practical advice for how this meal fits into daily nutrition."\n'
                "}\n"
                "Safety rule: If the image is not food or is unclear, return calories: 0, foodName: 'Unrecognized Dish', healthScore: 0."
            )

            raw_res = openrouter_client.vision_analysis(
                prompt=prompt,
                image_bytes=image_bytes,
                content_type=content_type,
                max_tokens=650,
                temperature=0.2,
                model=target_model,
            )

            parsed = openrouter_client.parse_json_response(raw_res)

            food_name = str(parsed.get("foodName") or "Prepared Meal").strip()
            portion = str(parsed.get("portionSize") or "1 standard serving").strip()
            calories = int(parsed.get("calories", 0))
            protein = float(parsed.get("protein", 0.0))
            carbs = float(parsed.get("carbs", 0.0))
            fat = float(parsed.get("fat", 0.0))
            fiber = float(parsed.get("fiber", 0.0))
            sugar = float(parsed.get("sugar", 0.0))
            sodium = int(parsed.get("sodiumMg", 0))
            health_score = max(0, min(100, int(parsed.get("healthScore", 70))))
            condition = str(parsed.get("condition") or "Nutrient-Dense Meal").strip()
            micronutrients = [str(m) for m in parsed.get("micronutrients", []) if str(m).strip()]
            obs = str(parsed.get("observations") or "").strip()
            rec = str(parsed.get("recommendation") or "Enjoy as part of a varied, balanced diet.").strip()

            if REAL_FOOD_DISCLAIMER not in obs:
                obs = f"{obs}\n\n{REAL_FOOD_DISCLAIMER}".strip()

            return {
                "foodName": food_name,
                "portionSize": portion,
                "calories": calories,
                "protein": round(protein, 1),
                "carbs": round(carbs, 1),
                "fat": round(fat, 1),
                "fiber": round(fiber, 1),
                "sugar": round(sugar, 1),
                "sodiumMg": sodium,
                "freshnessScore": health_score,
                "condition": condition,
                "micronutrients": micronutrients,
                "observations": obs,
                "recommendation": rec,
                "provider": f"openrouter/{target_model}",
                "scanType": "REAL_FOOD",
            }

        except Exception as exc:
            logger.warning("Gemma 4 26B real food meal analysis failed: %s; falling back to safe response", exc)

    # Safe fallback if API unavailable
    return {
        "foodName": "Prepared Meal",
        "portionSize": "1 standard portion",
        "calories": 400,
        "protein": 20.0,
        "carbs": 45.0,
        "fat": 14.0,
        "fiber": 4.0,
        "sugar": 5.0,
        "sodiumMg": 400,
        "freshnessScore": 75,
        "condition": "Prepared Meal (Estimated)",
        "micronutrients": ["Dietary Fiber", "Vitamins"],
        "observations": f"Image received. Automated nutrition parsing temporarily offline. {REAL_FOOD_DISCLAIMER}",
        "recommendation": "Estimate intake based on standard portion guidelines.",
        "provider": "meal-fallback-engine",
        "scanType": "REAL_FOOD",
    }

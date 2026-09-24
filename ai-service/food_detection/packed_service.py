"""Packaged food and ingredient label analysis service.

Powered by Google Gemma 4 26B A4B (google/gemma-4-26b-a4b-it) via OpenRouter.
Evaluates ingredient lists, nutrition labels, and product packaging to assign
Nutritional Health Grades from 'A' (Best) to 'F' (Worst / Ultra-processed),
highlighting additives, preservatives, processing levels, and healthier alternatives.
"""

from __future__ import annotations

from io import BytesIO
import logging
from typing import Any

from PIL import Image

from services.openrouter_client import openrouter_client
from services.settings import settings

logger = logging.getLogger(__name__)

PACKED_FOOD_DISCLAIMER = (
    "Nutritional grading is based on visible ingredient labels and packaging indicators for informational purposes. "
    "Always consult manufacturer allergen warnings and speak to a certified dietitian for individualized medical dietary needs."
)


def analyze_packed_food(image_bytes: bytes, filename: str | None, content_type: str) -> dict[str, Any]:
    """Analyze a food packet or ingredient list using Gemma 4 26B A4B."""
    # 1. Explicit mock mode check
    if settings.ai_mode.lower() == "mock":
        return {
            "foodName": "Whole Grain Oat Granola (Sample)",
            "grade": "A",
            "freshnessScore": 92,
            "condition": "Grade A - Excellent Choice",
            "processingLevel": "Minimally Processed (NOVA 1)",
            "positives": ["100% whole grain oats", "Zero artificial preservatives", "Naturally sweetened with honey"],
            "concerns": ["Moderate natural sugars from honey"],
            "observations": (
                "[Grade A - Score 92/100] Minimally Processed. Positives: 100% whole grain oats, zero artificial preservatives. "
                "Concerns: Moderate natural sugars. Clean wholesome ingredients without harmful additives."
            ),
            "recommendation": "Excellent everyday breakfast or snack. Pair with unsweetened Greek yogurt for balanced protein.",
            "provider": "mock-packed-service",
            "scanType": "PACKED_FOOD",
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
                "You are an expert Food Science & Nutritional Quality Inspector analyzing packaged foods and ingredient labels.\n"
                "Look closely at the uploaded photo of the food packaging, brand, nutrition facts, or ingredient list.\n"
                "Assign a comprehensive Health Grade from 'A' to 'F' where:\n"
                "- 'A' (Score 85-100): Best / Excellent nutritional quality, clean whole ingredients, minimal/no harmful additives, low sugar & sodium.\n"
                "- 'B' (Score 70-84): Good / Wholesome choice, balanced nutrition, light processing.\n"
                "- 'C' (Score 50-69): Moderate / Fair quality, some added sugar/refined oils or salt, consume in moderation.\n"
                "- 'D' (Score 30-49): Poor nutritional profile, highly processed, high refined sugars, palm/seed oils, or artificial flavors.\n"
                "- 'F' (Score 0-29): Worst / Ultra-processed (NOVA 4), hazardous additives (TBHQ, BHT, artificial food dyes, hydrogenated fats, high fructose corn syrup), heavily refined.\n\n"
                "Return ONLY a valid JSON object matching this schema:\n"
                "{\n"
                '  "productName": "Name and brand of the product (e.g. Honey Nut Cheerios, Lay\'s Classic, Greek Yogurt)",\n'
                '  "grade": "Must be exactly one letter: \'A\', \'B\', \'C\', \'D\', or \'F\'",\n'
                '  "score": integer between 0 and 100 representing overall nutritional health,\n'
                '  "processingLevel": "e.g. Minimally Processed (NOVA 1), Processed Culinary (NOVA 2), Processed (NOVA 3), or Ultra-Processed (NOVA 4)",\n'
                '  "positives": ["Array of 2-4 positive traits, whole grains, fiber, clean ingredients, vitamins"],\n'
                '  "concerns": ["Array of 1-4 red flags or additives: excessive sugar, sodium, palm oil, artificial colors, preservatives"],\n'
                '  "verdict": "2-3 clear sentences summarizing why this grade was assigned based on the visible ingredients.",\n'
                '  "recommendation": "Practical consumption advice and a healthier swap/alternative if Grade is C, D, or F."\n'
                "}\n"
                "If the image does not show food packaging or ingredients, set grade to 'F', score to 0, and verdict to 'Could not detect food packaging or an ingredient list in this image.'"
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

            product_name = str(parsed.get("productName") or "Packaged food item").strip()
            grade_raw = str(parsed.get("grade") or "C").strip().upper()
            grade = grade_raw if grade_raw in {"A", "B", "C", "D", "F"} else "C"

            score = int(parsed.get("score", 50))
            score = max(0, min(100, score))

            proc_level = str(parsed.get("processingLevel") or "Processed Food").strip()
            positives = [str(p) for p in parsed.get("positives", []) if str(p).strip()]
            concerns = [str(c) for c in parsed.get("concerns", []) if str(c).strip()]
            verdict = str(parsed.get("verdict") or "").strip()
            rec = str(parsed.get("recommendation") or "Inspect packaging for allergens and storage guidelines.").strip()

            grade_labels = {
                "A": "Grade A - Excellent Choice",
                "B": "Grade B - Good & Wholesome",
                "C": "Grade C - Moderate / Fair",
                "D": "Grade D - Poor Nutritional Quality",
                "F": "Grade F - Ultra-Processed / Avoid",
            }
            condition_str = grade_labels.get(grade, f"Grade {grade}")

            # Combine into a structured, readable observations text
            obs_parts = [f"[{condition_str} · Score {score}/100 · {proc_level}]", verdict]
            if positives:
                obs_parts.append("Key Positives: " + "; ".join(positives) + ".")
            if concerns:
                obs_parts.append("Nutritional Concerns: " + "; ".join(concerns) + ".")
            obs_parts.append(PACKED_FOOD_DISCLAIMER)

            combined_obs = "\n\n".join(obs_parts)

            return {
                "foodName": product_name,
                "grade": grade,
                "freshnessScore": score,
                "condition": condition_str,
                "processingLevel": proc_level,
                "positives": positives,
                "concerns": concerns,
                "observations": combined_obs,
                "recommendation": rec,
                "provider": f"openrouter/{target_model}",
                "scanType": "PACKED_FOOD",
            }

        except Exception as exc:
            logger.warning("Gemma 4 26B packed food analysis failed: %s; falling back to safe response", exc)

    # Safe fallback if API unavailable
    return {
        "foodName": "Packaged food item",
        "grade": "C",
        "freshnessScore": 50,
        "condition": "Grade C - Moderate (Estimated)",
        "processingLevel": "Processed Food",
        "positives": ["Packaging received"],
        "concerns": ["Automated classification unavailable"],
        "observations": (
            "Image received. Automated AI ingredient grading service is temporarily unavailable. "
            "Please check the nutrition facts panel manually for high sugar, saturated fats, or artificial additives. "
            f"{PACKED_FOOD_DISCLAIMER}"
        ),
        "recommendation": "Review the ingredient list for whole foods as the primary ingredients.",
        "provider": "packed-fallback-engine",
        "scanType": "PACKED_FOOD",
    }

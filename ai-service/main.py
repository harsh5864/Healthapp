"""AI service boundary for future computer-vision, chat and wellness providers.

Phase 1 intentionally exposes only a readiness endpoint. It does not pretend to
perform analysis, and it does not contact an external AI provider.
"""

import base64
import json

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from chatbot.service import get_health_assistant
from food_detection.service import analyze_image
from services.settings import settings

class ChatMessageItem(BaseModel):
    sender: str = "USER"
    message: str = ""

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessageItem] = []

app = FastAPI(
    title="AI Health Companion AI Service",
    version="0.1.0",
    description="Provider-isolated AI service for food, health-chat and wellness features.",
)


@app.get("/health", tags=["platform"])
def health_check() -> dict[str, str]:
    """Returns service readiness and the explicitly configured AI mode."""
    return {"status": "available", "service": "ai-health-companion-ai", "aiMode": settings.ai_mode}


@app.post("/analyze/food", tags=["food"])
async def analyze_food(image: UploadFile = File(...)) -> dict[str, object]:
    """Analyze an uploaded food image through the replaceable CV boundary."""
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG or WebP image.")
    payload = await image.read()
    if not payload:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    try:
        return analyze_image(payload, image.filename, image.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze/food/raw", tags=["food"])
async def analyze_food_raw(request: Request) -> dict[str, object]:
    """Internal backend transport: image bytes in the request body."""
    payload = await request.body()
    return {
        "foodName": "Produce item",
        "freshnessScore": 0,
        "condition": "Unable to Determine",
        "observations": f"Image received ({len(payload)} bytes). A computer-vision model is not configured, so no visual freshness claim was made.",
        "recommendation": "Inspect the food yourself; this service cannot guarantee food safety.",
        "provider": "ai-service-unconfigured",
    }


@app.post("/analyze/food/base64", tags=["food"])
async def analyze_food_base64(request: Request) -> dict[str, object]:
    """Internal JSON transport used by Spring for reliable byte transfer."""
    try:
        body = await request.body()
        data = json.loads(body.decode("utf-8", errors="replace")) if body else {}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    raw_b64 = data.get("imageBase64", "")
    if not raw_b64:
        return {
            "foodName": "Produce item",
            "freshnessScore": 0,
            "condition": "Unable to Determine",
            "observations": "The AI service received no decodable image bytes.",
            "recommendation": "Inspect the food yourself; this service cannot guarantee food safety.",
            "provider": "ai-service-unconfigured",
        }

    try:
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        payload = base64.b64decode(raw_b64)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid image payload.") from exc

    if not payload:
        return {
            "foodName": "Produce item",
            "freshnessScore": 0,
            "condition": "Unable to Determine",
            "observations": "The AI service received no decodable image bytes.",
            "recommendation": "Inspect the food yourself; this service cannot guarantee food safety.",
            "provider": "ai-service-unconfigured",
        }
    try:
        return analyze_image(payload, data.get("filename"), data.get("contentType", "image/png"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat", tags=["chat"])
def chat(request: ChatRequest) -> dict[str, object]:
    """Provide general health-information chat with strict medical safety guardrails."""
    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if len(msg) > 10000:
        raise HTTPException(status_code=400, detail="Message exceeds maximum length of 10,000 characters.")

    assistant = get_health_assistant()
    history_dicts = [{"sender": h.sender, "message": h.message} for h in request.history]
    return assistant.respond(msg, history_dicts)

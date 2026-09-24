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
from food_detection.packed_service import analyze_packed_food
from food_detection.meal_service import analyze_real_food
from services.settings import settings
from wellness.menta import analyze_menta
from wellness.service import analyze_wellness
from wellness.sleeplm import analyze_sleeplm

class ChatMessageItem(BaseModel):
    sender: str = "USER"
    message: str = ""

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessageItem] = []

class WellnessEntryItem(BaseModel):
    mood: int = 7
    stress: int = 4
    energy: int = 7
    activity: int = 5
    sleepHours: float = 7.0
    journalText: str = ""
    createdAt: str = ""

class WellnessAnalyzeRequest(BaseModel):
    averageMood: float = 7.0
    averageStress: float = 4.0
    averageEnergy: float = 7.0
    averageActivity: float = 5.0
    averageSleep: float = 7.0
    entries: list[WellnessEntryItem] = []

class SleepLmRequest(BaseModel):
    averageSleep: float = 7.0
    entries: list[WellnessEntryItem] = []

class MentaRequest(BaseModel):
    averageMood: float = 7.0
    averageStress: float = 4.0
    averageEnergy: float = 7.0
    averageActivity: float = 5.0
    entries: list[WellnessEntryItem] = []

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
    scan_type = str(data.get("scanType", "PRODUCE")).upper()
    try:
        if "REAL" in scan_type or "MEAL" in scan_type:
            return analyze_real_food(payload, data.get("filename"), data.get("contentType", "image/png"))
        if "PACKED" in scan_type:
            return analyze_packed_food(payload, data.get("filename"), data.get("contentType", "image/png"))
        return analyze_image(payload, data.get("filename"), data.get("contentType", "image/png"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze/meal", tags=["food"])
async def analyze_meal(image: UploadFile = File(...)) -> dict[str, object]:
    """Analyze a real food meal or dish using Gemma 4 26B A4B."""
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG or WebP image.")
    payload = await image.read()
    if not payload:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    try:
        return analyze_real_food(payload, image.filename, image.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze/packed", tags=["food"])
async def analyze_packed(image: UploadFile = File(...)) -> dict[str, object]:
    """Analyze a food packet or ingredient list using Gemma 4 26B A4B."""
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG or WebP image.")
    payload = await image.read()
    if not payload:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    try:
        return analyze_packed_food(payload, image.filename, image.content_type)
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


@app.post("/wellness/analyze", tags=["wellness"])
def wellness_analyze(request: WellnessAnalyzeRequest) -> dict[str, object]:
    """Generate empathetic trend insights, SleepLM sleep architecture, and Menta mind-body synthesis."""
    entries_dicts = [e.model_dump() for e in request.entries]
    return analyze_wellness(
        entries=entries_dicts,
        avg_mood=request.averageMood,
        avg_stress=request.averageStress,
        avg_energy=request.averageEnergy,
        avg_sleep=request.averageSleep,
        avg_activity=request.averageActivity,
    )


@app.post("/wellness/sleeplm", tags=["wellness"])
def wellness_sleeplm(request: SleepLmRequest) -> dict[str, object]:
    """Dedicated SleepLM endpoint for clinical-grade sleep summaries and restorative recommendations."""
    entries_dicts = [e.model_dump() for e in request.entries]
    return analyze_sleeplm(
        entries=entries_dicts,
        avg_sleep=request.averageSleep,
    )


@app.post("/wellness/menta", tags=["wellness"])
def wellness_menta(request: MentaRequest) -> dict[str, object]:
    """Dedicated Menta endpoint for holistic mood, energy, activity, and stress multi-pillar synthesis."""
    entries_dicts = [e.model_dump() for e in request.entries]
    return analyze_menta(
        entries=entries_dicts,
        avg_mood=request.averageMood,
        avg_stress=request.averageStress,
        avg_energy=request.averageEnergy,
        avg_activity=request.averageActivity,
    )

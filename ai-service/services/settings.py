"""Environment-backed settings for the separate AI service."""

from dataclasses import dataclass
from os import getenv
from pathlib import Path
from dotenv import load_dotenv

# Load root .env
root_env = Path(__file__).resolve().parents[2] / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
load_dotenv()


@dataclass(frozen=True)
class Settings:
    ai_mode: str = getenv("AI_MODE", "mock")
    provider_base_url: str = getenv("AI_PROVIDER_BASE_URL", "")
    food_model_id: str = getenv("FOOD_MODEL_ID", "google/mobilenet_v2_1.0_224")
    food_model_enabled: bool = getenv("FOOD_MODEL_ENABLED", "true").lower() == "true"
    freshness_model_id: str = getenv("FRESHNESS_MODEL_ID", "Aryaman9999/Freshness-Fruit_Vegies")
    freshness_model_enabled: bool = getenv("FRESHNESS_MODEL_ENABLED", "true").lower() == "true"
    openrouter_api_key: str = getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    packed_food_model: str = getenv("PACKED_FOOD_MODEL", "google/gemma-4-26b-a4b-it")


settings = Settings()


import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .models import ResearchConfig


class Settings(BaseModel):
    config_path: Path = Path("config/research_queries.yaml")
    output_dir: Path = Path("data/research")
    timeout_seconds: float = Field(default=15.0, gt=0)
    gemini_timeout_seconds: float = Field(default=90.0, gt=0)
    gemini_max_attempts: int = Field(default=2, ge=1, le=3)
    gemini_retry_base_seconds: float = Field(default=10.0, ge=0)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"
    discord_webhook_url: str | None = None


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        config_path=Path(os.getenv("PHASE1_CONFIG_PATH", "config/research_queries.yaml")),
        output_dir=Path(os.getenv("PHASE1_OUTPUT_DIR", "data/research")),
        timeout_seconds=float(os.getenv("PHASE1_TIMEOUT_SECONDS", "15")),
        gemini_timeout_seconds=float(os.getenv("PHASE1_GEMINI_TIMEOUT_SECONDS", "90")),
        gemini_max_attempts=int(os.getenv("PHASE1_GEMINI_MAX_ATTEMPTS", "2")),
        gemini_retry_base_seconds=float(os.getenv("PHASE1_GEMINI_RETRY_BASE_SECONDS", "10")),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL") or None,
    )


def load_research_config(path: Path) -> ResearchConfig:
    with path.open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    shared = raw.get("shared", {})
    phase1 = raw.get("phase1", {})
    outfit = phase1.get("outfit", {})
    return ResearchConfig(
        country=shared.get("country", "India"),
        occasion_minimum_lead_days=outfit.get("occasion_minimum_lead_days", 10),
        occasion_horizon_days=outfit.get("occasion_horizon_days", 120),
        outfit_categories=outfit.get("categories", []),
        gender_options=outfit.get("gender_options", ["male", "female"]),
        gender_balance_max_runs=outfit.get("gender_balance_max_runs", 20),
        outfit_history_limit=outfit.get("history_limit", 5),
    )
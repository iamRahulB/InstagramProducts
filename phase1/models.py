from datetime import date as Date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Occasion(BaseModel):
    name: str = Field(min_length=1)
    date: Date | None = None
    days_until: int = Field(default=0, ge=0)
    relevance: str = ""


class TemporalContext(BaseModel):
    date: Date
    month: str
    year: int
    day_of_week: str
    season: str
    occasion: str | None = None
    fashion_direction: str
    reason: str


class FashionDirection(BaseModel):
    direction: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    occasion_relevance: str | None = None
    season_relevance: str | None = None
    gender_recommendation: str = Field(min_length=1)
    style_keywords: list[str] = Field(default_factory=list)
    avoid_repetition: list[str] = Field(default_factory=list)


class OutfitItem(BaseModel):
    category: str = Field(min_length=2)
    subcategory: str = Field(min_length=1)
    visual_requirements: dict[str, str] = Field(min_length=1)
    search_query: str = Field(min_length=5)


class Outfit(BaseModel):
    gender: str = Field(min_length=1)
    concept: str = Field(min_length=1)
    items: list[OutfitItem] = Field(min_length=2)

class OutfitSpecification(BaseModel):
    research_id: str = Field(min_length=1)
    outfit_id: str = Field(min_length=1)
    generated_at: datetime
    country: str = Field(min_length=1)
    context: TemporalContext
    outfit: Outfit
    warnings: list[str] = Field(default_factory=list)

    def validate_occasion_is_calendar_sourced(self, calendar_occasions: list[Occasion]) -> None:
        if self.context.occasion:
            occasion_names = {occasion.name for occasion in calendar_occasions}
            occasion_lower = self.context.occasion.lower().strip()
            if not any(
                occasion_lower == name.lower().strip() or
                occasion_lower in name.lower() or
                name.lower() in occasion_lower
                for name in occasion_names
            ):
                raise ValueError(f"context.occasion '{self.context.occasion}' must come from the supplied calendar occasions: {occasion_names}")


class ResearchConfig(BaseModel):
    country: Literal["India"] = "India"
    occasion_minimum_lead_days: int = Field(default=10, ge=10, le=365)
    occasion_horizon_days: int = Field(default=120, ge=1, le=730)
    outfit_categories: list[str] = Field(default_factory=list)
    gender_options: list[str] = Field(default_factory=lambda: ["male", "female"])
    gender_balance_max_runs: int = Field(default=20, ge=2, le=100)
    outfit_history_limit: int = Field(default=5, ge=1, le=20)
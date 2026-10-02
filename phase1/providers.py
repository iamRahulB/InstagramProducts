import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Protocol

import httpx
from pydantic import ValidationError

from prompts import build_direction_prompt, build_outfit_prompt

from .models import FashionDirection, Occasion, OutfitSpecification

logger = logging.getLogger(__name__)


class OutfitAIProvider(Protocol):
    def synthesize_outfit(
        self,
        context: dict[str, Any],
        occasions: list[Occasion],
        country: str,
        research_id: str,
        outfit_id: str,
        categories: list[str],
        gender_options: list[str],
        preferred_gender: str,
        recent_outfits: list[dict[str, Any]],
    ) -> OutfitSpecification: ...


class GeminiProvider:
    def __init__(self, api_key: str, model: str, timeout: float = 90.0, max_attempts: int = 2, retry_base_seconds: float = 10.0):
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client(timeout=timeout)
        self.max_attempts = max_attempts
        self.retry_base_seconds = retry_base_seconds

    def analyze_fashion_direction(
        self,
        context: dict[str, Any],
        occasions: list[Occasion],
        country: str,
        gender_options: list[str],
        preferred_gender: str,
        recent_outfits: list[dict[str, Any]],
    ) -> FashionDirection:
        occasion_text = "\n".join(f"- {item.name}: {item.date}, {item.days_until} days remaining" for item in occasions) or "None"
        prompt = build_direction_prompt(context, occasion_text, country, gender_options, preferred_gender, recent_outfits)
        for attempt in range(1, self.max_attempts + 1):
            text = self._generate_text(prompt, direction_response_schema())
            try:
                return FashionDirection.model_validate_json(normalize_json_response(text))
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                if attempt == self.max_attempts:
                    raise RuntimeError(f"Gemini returned invalid direction JSON: {str(exc)[:500]}") from exc
                prompt += f"\n\nYour previous JSON failed validation. Return the full corrected JSON only. Validation errors: {str(exc)[:1200]}"
                logger.warning("Gemini direction JSON failed validation; requesting one corrected response")
        raise RuntimeError("Gemini produced no valid fashion direction")

    def synthesize_outfit(
        self,
        context: dict[str, Any],
        occasions: list[Occasion],
        country: str,
        research_id: str,
        outfit_id: str,
        categories: list[str],
        gender_options: list[str],
        preferred_gender: str,
        recent_outfits: list[dict[str, Any]],
        direction: FashionDirection,
    ) -> OutfitSpecification:
        occasion_text = "\n".join(f"- {item.name}: {item.date}, {item.days_until} days remaining" for item in occasions) or "None"
        prompt = build_outfit_prompt(context, occasion_text, country, research_id, outfit_id, categories, recent_outfits, direction)
        for attempt in range(1, self.max_attempts + 1):
            text = self._generate_text(prompt, outfit_response_schema(categories, gender_options))
            try:
                payload = repair_outfit_payload(json.loads(normalize_json_response(text)), country, research_id, outfit_id, categories, gender_options)
                return OutfitSpecification.model_validate(payload)
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                if attempt == self.max_attempts:
                    raise RuntimeError(f"Gemini returned invalid outfit JSON: {str(exc)[:500]}") from exc
                prompt += f"\n\nYour previous JSON failed validation. Return the full corrected JSON only. Validation errors: {str(exc)[:1200]}"
                logger.warning("Gemini outfit JSON failed validation; requesting one corrected response")
        raise RuntimeError("Gemini produced no valid outfit specification")

    def _generate_text(self, prompt: str, response_schema: dict[str, Any]) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "responseSchema": response_schema},
        }
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                    headers={"x-goog-api-key": self.api_key},
                    json=payload,
                )
            except httpx.TimeoutException:
                if attempt == self.max_attempts:
                    raise
                delay = self.retry_base_seconds * (2 ** (attempt - 1))
                logger.warning("Gemini request timed out; retrying in %.1fs", delay)
                time.sleep(delay)
                continue
            if response.status_code not in {408, 429, 500, 502, 503, 504} or attempt == self.max_attempts:
                break
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else self.retry_base_seconds * (2 ** (attempt - 1))
            logger.warning("Gemini transient response %s; retrying in %.1fs", response.status_code, delay)
            time.sleep(delay)
        response.raise_for_status()
        body = response.json()
        candidates = body.get("candidates", [])
        if not candidates or not candidates[0].get("content", {}).get("parts"):
            reason = body.get("promptFeedback", {}).get("blockReason") or body.get("candidates", [{}])[0].get("finishReason", "unknown")
            raise RuntimeError(f"Gemini returned no usable candidate ({reason})")
        return candidates[0]["content"]["parts"][0].get("text", "")


def normalize_json_response(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1]).strip()
    return cleaned


def repair_outfit_payload(payload: dict[str, Any], country: str, research_id: str, outfit_id: str, categories: list[str], gender_options: list[str]) -> dict[str, Any]:
    """Validate the AI-produced outfit and apply only structural fixes (IDs, country, casing).

    Query wording is decided by the AI. This function never rewrites fashion content;
    non-compliant queries raise ValueError so the caller can ask the AI to correct them.
    """
    outfit = payload.get("outfit", {})
    items = outfit.get("items", []) if isinstance(outfit, dict) else []
    gender = outfit.get("gender", "")
    if gender not in gender_options:
        raise ValueError(f"unsupported gender {gender!r}; configured options are {gender_options}")
    payload["research_id"] = research_id
    payload["outfit_id"] = outfit_id
    payload["country"] = country
    for item in items:
        category = item.get("category")
        if category not in categories:
            raise ValueError(f"unsupported outfit category {category!r}")
        query = str(item.get("search_query", "")).strip()
        if not query:
            raise ValueError(f"item {category!r} is missing search_query")
        query = re.sub(rf"\b{re.escape(country)}\b", "", query, flags=re.IGNORECASE)
        query = " ".join(query.split()).lower()
        if not re.search(r"\b(men|women)\b", query):
            raise ValueError(f"search_query for {category!r} must use natural market terminology (men/women): {query!r}")
        subcategory = str(item.get("subcategory", "")).strip().lower()
        if subcategory and not any(token in query for token in subcategory.split()):
            raise ValueError(f"search_query for {category!r} must contain the product type from subcategory {subcategory!r}: {query!r}")
        if len(query.split()) > 12:
            raise ValueError(f"search_query for {category!r} is overloaded ({len(query.split())} words): {query!r}")
        item["search_query"] = query
        item.pop("queries", None)
        item.pop("matched_to", None)
    return payload


def direction_response_schema() -> dict[str, Any]:
    return {
        "type": "OBJECT",
        "properties": {
            "direction": {"type": "STRING"},
            "reasoning": {"type": "STRING"},
            "occasion_relevance": {"type": "STRING", "nullable": True},
            "season_relevance": {"type": "STRING", "nullable": True},
            "gender_recommendation": {"type": "STRING"},
            "style_keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
            "avoid_repetition": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
    }


def outfit_response_schema(categories: list[str], gender_options: list[str]) -> dict[str, Any]:
    visual = {"type": "OBJECT", "properties": {key: {"type": "STRING"} for key in ("fit", "material", "pattern", "style", "silhouette", "strap", "color", "neckline", "length", "rise", "design", "embellishment", "heel_type")}}
    item = {"type": "OBJECT", "properties": {"category": {"type": "STRING", "enum": categories}, "subcategory": {"type": "STRING"}, "visual_requirements": visual, "search_query": {"type": "STRING"}}, "required": ["category", "subcategory", "visual_requirements", "search_query"]}
    context = {"type": "OBJECT", "properties": {"date": {"type": "STRING"}, "month": {"type": "STRING"}, "year": {"type": "INTEGER"}, "day_of_week": {"type": "STRING"}, "season": {"type": "STRING"}, "occasion": {"type": "STRING", "nullable": True}, "fashion_direction": {"type": "STRING"}, "reason": {"type": "STRING"}}}
    return {"type": "OBJECT", "properties": {"research_id": {"type": "STRING"}, "outfit_id": {"type": "STRING"}, "generated_at": {"type": "STRING"}, "country": {"type": "STRING"}, "context": context, "outfit": {"type": "OBJECT", "properties": {"gender": {"type": "STRING", "enum": gender_options}, "concept": {"type": "STRING"}, "items": {"type": "ARRAY", "items": item}}}, "warnings": {"type": "ARRAY", "items": {"type": "STRING"}}}}
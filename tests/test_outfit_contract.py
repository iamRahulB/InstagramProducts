from datetime import date

import pytest

from phase1.calendar import upcoming_indian_occasions
from phase1.models import OutfitSpecification
from phase1.providers import normalize_json_response, outfit_response_schema, repair_outfit_payload
from prompts import build_outfit_prompt


def test_outfit_contract_uses_one_search_query_and_no_match_field():
    outfit = OutfitSpecification.model_validate(
        {
            "research_id": "test-1",
            "outfit_id": "outfit-2026-09-26-test1",
            "generated_at": "2026-09-26T00:00:00Z",
            "country": "India",
            "context": {"date": "2026-09-26", "month": "September", "year": 2026, "day_of_week": "Saturday", "season": "dynamic", "fashion_direction": "dynamic", "reason": "calendar"},
            "outfit": {"gender": "female", "concept": "Relaxed current look", "items": [{"category": "top", "subcategory": "relaxed top", "visual_requirements": {"fit": "relaxed"}, "search_query": "women relaxed fit top"}, {"category": "handbag", "subcategory": "structured handbag", "visual_requirements": {"style": "minimal"}, "search_query": "women minimal structured handbag"}]},
        }
    )
    assert outfit.outfit.items[0].search_query.startswith("women ")
    assert not hasattr(outfit.outfit.items[1], "matched_to")


def test_calendar_occasion_has_ten_day_lead_time():
    occasions = upcoming_indian_occasions(date(2026, 9, 26), minimum_lead_days=10, horizon_days=120)
    assert occasions
    assert all(item.days_until >= 10 for item in occasions)


def test_outfit_prompt_and_schema_are_calendar_only():
    from phase1.models import FashionDirection
    direction = FashionDirection(direction="test", reasoning="test", gender_recommendation="female", style_keywords=[], avoid_repetition=[])
    prompt = build_outfit_prompt({"date": "2026-09-26"}, "None", "India", "test-1", "outfit-test-1", ["kurta", "pants"], [], direction)
    schema = outfit_response_schema(["kurta", "pants"], ["male", "female"])
    assert "at least 10 days" in prompt
    assert "5-9 words" in prompt
    assert "omit India" in prompt
    assert "men or women" in prompt
    assert schema["properties"]["outfit"]["properties"]["items"]["type"] == "ARRAY"
    assert schema["properties"]["outfit"]["properties"]["items"]["items"]["properties"]["category"]["enum"] == ["kurta", "pants"]
    assert normalize_json_response("```json\n{}\n```") == "{}"


def test_repair_validates_ai_queries_without_rewriting():
    payload = {"outfit": {"gender": "female", "items": [{"category": "kurta", "subcategory": "peplum kurta", "visual_requirements": {"color": "maroon", "fit": "fitted", "material": "silk", "style": "festive"}, "search_query": "women maroon fitted silk peplum kurta"}, {"category": "pants", "subcategory": "straight pants", "visual_requirements": {"fit": "tailored"}, "search_query": "women tailored straight pants"}]}}
    repaired = repair_outfit_payload(payload, "India", "research-test", "outfit-test", ["kurta", "pants"], ["male", "female"])
    assert repaired["research_id"] == "research-test"
    assert repaired["outfit_id"] == "outfit-test"
    assert repaired["outfit"]["items"][0]["search_query"] == "women maroon fitted silk peplum kurta"
    assert "matched_to" not in repaired["outfit"]["items"][0]


def test_repair_rejects_non_compliant_query():
    payload = {"outfit": {"gender": "female", "items": [{"category": "kurta", "subcategory": "peplum kurta", "visual_requirements": {"color": "maroon"}, "search_query": "female fitted silk peplum kurta"}, {"category": "pants", "subcategory": "straight pants", "visual_requirements": {"fit": "tailored"}, "search_query": "women tailored straight pants"}]}}
    with pytest.raises(ValueError, match="men/women"):
        repair_outfit_payload(payload, "India", "research-test", "outfit-test", ["kurta", "pants"], ["male", "female"])
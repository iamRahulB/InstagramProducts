import json
from datetime import date
from pathlib import Path

from phase1.calendar import upcoming_indian_occasions
from phase1.config import Settings
from phase1.models import OutfitSpecification
from phase1.service import load_outfit_history, run


def test_service_produces_valid_outfit_report(tmp_path: Path, monkeypatch):
    class FakeGemini:
        def __init__(self, *args, **kwargs):
            pass

        def analyze_fashion_direction(self, context, occasions, country, gender_options, preferred_gender, recent_outfits):
            from phase1.models import FashionDirection
            return FashionDirection(direction="test", reasoning="test", gender_recommendation=preferred_gender, style_keywords=[], avoid_repetition=[])

        def synthesize_outfit(self, context, occasions, country, research_id, outfit_id, categories, gender_options, preferred_gender, recent_outfits, direction):
            assert preferred_gender in gender_options
            gender_term = "women" if preferred_gender == "female" else "men"
            return OutfitSpecification.model_validate(
                {
                    "research_id": research_id,
                        "outfit_id": outfit_id,
                    "generated_at": "2026-09-26T00:00:00Z",
                    "country": country,
                    "context": {
                        "date": "2026-09-26",
                        "month": "September",
                        "year": 2026,
                        "day_of_week": "Saturday",
                        "season": "AI-derived seasonal context",
                        "occasion": None,
                        "fashion_direction": "Current wearable fashion",
                        "reason": "Mocked synthesis",
                    },
                    "outfit": {
                        "gender": preferred_gender,
                        "concept": "Current wearable fashion",
                        "items": [
                            {"category": "tshirt", "subcategory": "relaxed t-shirt", "visual_requirements": {"fit": "relaxed"}, "search_query": f"{gender_term} relaxed t-shirt"},
                            {"category": "sneakers", "subcategory": "casual sneakers", "visual_requirements": {"style": "casual"}, "search_query": f"{gender_term} casual sneakers"},
                        ],
                    },
                }
            )

    settings = Settings(output_dir=tmp_path, config_path=Path("config/research_queries.yaml"))
    report, output_path = run(settings, date(2026, 9, 26), ai_provider=FakeGemini())
    saved = json.loads(Path(output_path).read_text(encoding="utf-8"))
    assert saved["research_id"] == report.research_id
    assert saved["outfit_id"].startswith("outfit-2026-09-26-")
    assert saved["country"] == "India"
    assert saved["outfit"]["items"]
    assert saved["outfit"]["items"][1]["search_query"]


def test_indian_calendar_returns_dated_occasions():
    occasions = upcoming_indian_occasions(
        date(2026, 9, 26),
        horizon_days=120,
    )
    assert occasions
    assert all(item.date is not None for item in occasions)
    assert all(item.days_until >= 10 for item in occasions)


def test_gender_planner_balances_prior_saved_reports(tmp_path: Path):
    (tmp_path / "prior.json").write_text(json.dumps({"outfit": {"gender": "male", "concept": "streetwear", "items": [{"category": "shirt", "subcategory": "oversized shirt"}]}, "context": {"fashion_direction": "casual"}}))
    history, preferred = load_outfit_history(tmp_path, ["male", "female"], 20, 5, date(2026, 9, 26))
    assert len(history) == 1
    assert history[0]["items"] == ["shirt: oversized shirt"]
    assert preferred == "female"
    
def test_gender_balance_counts_history_not_only_latest_gender(tmp_path: Path):
    (tmp_path / "older.json").write_text(json.dumps({"outfit": {"gender": "male", "concept": "A", "items": []}}))
    (tmp_path / "middle.json").write_text(json.dumps({"outfit": {"gender": "male", "concept": "B", "items": []}}))
    (tmp_path / "newer.json").write_text(json.dumps({"outfit": {"gender": "female", "concept": "C", "items": []}}))
    _, preferred = load_outfit_history(tmp_path, ["male", "female"], 20, 5, date(2026, 9, 26))
    assert preferred == "female"


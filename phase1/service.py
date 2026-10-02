import logging
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from .config import Settings, load_research_config
from .calendar import upcoming_indian_occasions
from .models import OutfitSpecification
from .notifications import notify
from .output import write_report
from .providers import GeminiProvider, OutfitAIProvider

logger = logging.getLogger(__name__)


def run(settings: Settings, today: date | None = None, ai_provider: OutfitAIProvider | None = None) -> tuple[OutfitSpecification, str]:
    today = today or date.today()
    config = load_research_config(settings.config_path)
    run_suffix = uuid4().hex[:8]
    report_id = f"research-{today.isoformat()}-{run_suffix}"
    outfit_id = f"outfit-{today.isoformat()}-{run_suffix}"
    notify(settings.discord_webhook_url, f"Phase 1 research started: {report_id}")
    occasions = upcoming_indian_occasions(
        today,
        config.occasion_minimum_lead_days,
        config.occasion_horizon_days,
    )
    warnings: list[str] = []
    history, preferred_gender = load_outfit_history(
        settings.output_dir,
        config.gender_options,
        config.gender_balance_max_runs,
        config.outfit_history_limit,
        today,
    )
    context = {
        "date": today.isoformat(),
        "month": today.strftime("%B"),
        "year": today.year,
        "day_of_week": today.strftime("%A"),
        "season": "unknown",
        "country": config.country,
    }
    if ai_provider is None and not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required for outfit synthesis; no trend or outfit facts can be safely inferred offline.")
    synthesizer = ai_provider or GeminiProvider(settings.gemini_api_key or "", settings.gemini_model, timeout=settings.gemini_timeout_seconds, max_attempts=settings.gemini_max_attempts, retry_base_seconds=settings.gemini_retry_base_seconds)
    try:
        direction = synthesizer.analyze_fashion_direction(
            context,
            occasions,
            config.country,
            config.gender_options,
            preferred_gender,
            history,
        )
        report = synthesizer.synthesize_outfit(
            context,
            occasions,
            config.country,
            report_id,
            outfit_id,
            config.outfit_categories,
            config.gender_options,
            preferred_gender,
            history,
            direction,
        )
    except Exception as exc:
        warnings.append(f"Gemini synthesis failed: {str(exc)[:500]}")
        raise RuntimeError(warnings[-1]) from exc
    report = report.model_copy(update={"warnings": [*report.warnings, *warnings]})
    report.validate_occasion_is_calendar_sourced(occasions)
    path = write_report(report, settings.output_dir)
    notify(settings.discord_webhook_url, f"Phase 1 completed: {report_id}; outfit={report.outfit.concept}; output={path}")
    return report, str(path)


def load_outfit_history(output_dir: Path, gender_options: list[str], max_runs: int, history_limit: int, today: date) -> tuple[list[dict[str, object]], str]:
    records = []
    for path in sorted(output_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            outfit = report.get("outfit", {})
            gender = outfit.get("gender")
            if gender not in gender_options:
                continue
            items = outfit.get("items", [])
            records.append(
                {
                    "gender": gender,
                    "concept": outfit.get("concept", ""),
                    "fashion_direction": report.get("context", {}).get("fashion_direction", ""),
                    "occasion": report.get("context", {}).get("occasion"),
                    "items": [f"{item.get('category', '')}: {item.get('subcategory', '')}" for item in items],
                }
            )
            if len(records) >= max_runs:
                break
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            continue

    counts = {gender: sum(record["gender"] == gender for record in records) for gender in gender_options}
    lowest = min(counts.values(), default=0)
    candidates = [gender for gender in gender_options if counts[gender] == lowest]
    most_recent_gender = records[0]["gender"] if records else None
    if most_recent_gender in candidates and len(candidates) > 1:
        candidates.remove(most_recent_gender)
    if len(candidates) > 1:
        selected = candidates[today.toordinal() % len(candidates)]
    else:
        selected = candidates[0] if candidates else gender_options[0]
    return records[:history_limit], selected
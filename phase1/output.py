import json
from pathlib import Path

from .models import OutfitSpecification


def write_report(report: OutfitSpecification, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report.research_id}.json"
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path
"""Phase runner: executes the implemented chain Phase 1 → Phase 2."""

import logging

from phase1.config import load_settings
from phase1.service import run as run_phase1
from phase2.service import load_phase2_config, run as run_phase2


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = load_settings()

    outfit, phase1_path = run_phase1(settings)
    print(f"Phase 1 complete: {outfit.outfit.concept} ({outfit.outfit.gender}) -> {phase1_path}")

    phase2_config = load_phase2_config(settings.config_path)
    if phase2_config.enabled:
        report, phase2_path = run_phase2(outfit, phase2_config)
        total = sum(len(item.products) for item in report.items)
        print(f"Phase 2 complete: {total} products across {len(report.items)} items -> {phase2_path}")
        for warning in report.warnings:
            print(f"  warning: {warning}")
    else:
        print("Phase 2 disabled in configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

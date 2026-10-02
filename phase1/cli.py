import logging

from .config import load_settings
from .service import run


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    report, path = run(load_settings())
    print("----------------------------------------")
    print("PHASE 1 - FASHION RESEARCH")
    print("----------------------------------------")
    print(f"Country: {report.country}")
    print(f"Date: {report.context.date}")
    print(f"Outfit: {report.outfit.concept}")
    print(f"Gender: {report.outfit.gender}")
    for index, item in enumerate(report.outfit.items, start=1):
        print(f"{index}. {item.category}: {item.search_query}")
    print(f"Output: {path}")
    print("PHASE 1 COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
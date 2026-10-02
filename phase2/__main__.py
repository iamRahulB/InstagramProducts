"""Standalone Phase 2 execution: search SerpApi for an ad-hoc query.

Usage:
    python -m phase2 "women maroon silk peplum kurta"
"""

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .models import ItemDiscovery, ProductDiscoveryReport
from .providers import SerpApiProvider
from .service import _download_image, load_phase2_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 standalone product search")
    parser.add_argument("query", help="Product search query, e.g. 'women maroon silk peplum kurta'")
    parser.add_argument("--config", default="config/research_queries.yaml")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise SystemExit("SERPAPI_API_KEY is required. Add it to .env.")

    config = load_phase2_config(Path(args.config))
    provider = SerpApiProvider(api_key)
    products = provider.search(args.query, config)
    if config.resolve_product_links:
        products = [provider.resolve_link(p) for p in products]

    run_id = f"standalone-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    if config.download_images:
        products = [_download_image(p, config, run_id, "standalone") for p in products]

    report = ProductDiscoveryReport(
        research_id=run_id,
        outfit_id=run_id,
        country=config.country,
        gender="unknown",
        items=[ItemDiscovery(category="standalone", subcategory=args.query, search_query=args.query, products=products)],
    )
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run_id}.json"
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")

    print(f"Query: {args.query}")
    print(f"Products found: {len(products)}")
    for product in products:
        price = f"{product.currency} {product.price}" if product.price is not None else "price unknown"
        print(f"- {product.title} | {product.retailer} | {price}")
        print(f"  {product.product_url}")
        if product.local_image_path:
            print(f"  image: {product.local_image_path}")
    print(f"Saved: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import logging
import os
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

from phase1.models import OutfitSpecification

from .models import ItemDiscovery, Phase2Config, ProductCandidate, ProductDiscoveryReport
from .providers import ProductSearchProvider, SerpApiProvider

logger = logging.getLogger(__name__)


def load_phase2_config(path: Path) -> Phase2Config:
    with path.open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    shared = raw.get("shared", {})
    phase2 = dict(raw.get("phase2") or {})
    phase2.setdefault("country", shared.get("country", "India"))
    phase2.setdefault("run_type", shared.get("run_type", "dry_run"))
    return Phase2Config(**phase2)


def run(
    outfit: OutfitSpecification,
    config: Phase2Config,
    provider: ProductSearchProvider | None = None,
) -> tuple[ProductDiscoveryReport, str]:
    """Discover real products for every Phase 1 item. Never invents product data."""
    warnings: list[str] = []
    if not config.enabled:
        raise RuntimeError("Phase 2 is disabled in configuration.")
    if config.gender_filter != "both" and outfit.outfit.gender != config.gender_filter:
        report = ProductDiscoveryReport(
            research_id=outfit.research_id,
            outfit_id=outfit.outfit_id,
            country=outfit.country,
            gender=outfit.outfit.gender,
            items=[],
            warnings=[f"Skipped: outfit gender '{outfit.outfit.gender}' does not match phase2 gender_filter '{config.gender_filter}'."],
        )
        path = _write_report(report, Path(config.output_dir))
        return report, str(path)

    if provider is None:
        load_dotenv()
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise RuntimeError("SERPAPI_API_KEY is required for Phase 2 product discovery.")
        provider = SerpApiProvider(api_key)

    # Dry run: query only the first item to conserve SerpApi credits.
    items_to_search = outfit.outfit.items
    if config.run_type == "dry_run":
        items_to_search = items_to_search[:1]
        warnings.append("run_type=dry_run: only the first item was searched to conserve SerpApi credits.")

    discoveries: list[ItemDiscovery] = []
    for item in items_to_search:
        try:
            products = provider.search(item.search_query, config)
            if config.resolve_product_links:
                products = [provider.resolve_link(p) for p in products]
            if config.download_images:
                products = [_download_image(p, config, outfit.outfit_id, item.category) for p in products]
            if not products:
                warnings.append(f"No retailer-matching products found for '{item.search_query}'.")
            discoveries.append(
                ItemDiscovery(
                    category=item.category,
                    subcategory=item.subcategory,
                    search_query=item.search_query,
                    products=products,
                )
            )
        except Exception as exc:
            warnings.append(f"Search failed for '{item.search_query}': {exc.__class__.__name__}")
            discoveries.append(
                ItemDiscovery(
                    category=item.category,
                    subcategory=item.subcategory,
                    search_query=item.search_query,
                    products=[],
                    error=str(exc)[:300],
                )
            )

    report = ProductDiscoveryReport(
        research_id=outfit.research_id,
        outfit_id=outfit.outfit_id,
        country=outfit.country,
        gender=outfit.outfit.gender,
        items=discoveries,
        warnings=warnings,
    )
    path = _write_report(report, Path(config.output_dir))
    return report, str(path)


def _write_report(report: ProductDiscoveryReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report.research_id}.json"
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def _download_image(product: ProductCandidate, config: Phase2Config, outfit_id: str, category: str) -> ProductCandidate:
    """Download the product image locally; failures never fail the run."""
    if not product.image_url:
        return product
    try:
        image_dir = Path(config.output_dir) / "images" / outfit_id
        image_dir.mkdir(parents=True, exist_ok=True)
        response = httpx.get(str(product.image_url), timeout=20, follow_redirects=True)
        response.raise_for_status()
        suffix = ".jpg"
        content_type = response.headers.get("content-type", "")
        if "png" in content_type:
            suffix = ".png"
        elif "webp" in content_type:
            suffix = ".webp"
        filename = f"{category}-{abs(hash(str(product.product_url))) % 100000}{suffix}"
        path = image_dir / filename
        path.write_bytes(response.content)
        return product.model_copy(update={"local_image_path": str(path)})
    except Exception as exc:
        logger.warning("Image download failed for %s: %s", product.product_url, exc)
        return product

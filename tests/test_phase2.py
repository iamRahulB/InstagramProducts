from datetime import date
from pathlib import Path

from phase1.models import OutfitSpecification
from phase2.models import Phase2Config, ProductCandidate
from phase2.providers import SerpApiProvider
from phase2.service import load_phase2_config, run


def _outfit(gender: str = "female") -> OutfitSpecification:
    return OutfitSpecification.model_validate(
        {
            "research_id": "research-test",
            "outfit_id": "outfit-test",
            "generated_at": "2026-09-27T00:00:00Z",
            "country": "India",
            "context": {"date": "2026-09-27", "month": "September", "year": 2026, "day_of_week": "Sunday", "season": "post-monsoon", "fashion_direction": "festive", "reason": "test"},
            "outfit": {"gender": gender, "concept": "test", "items": [
                {"category": "kurta", "subcategory": "peplum kurta", "visual_requirements": {"color": "maroon"}, "search_query": "women maroon silk peplum kurta"},
                {"category": "heels", "subcategory": "block heels", "visual_requirements": {"color": "gold"}, "search_query": "women gold block heels"},
            ]},
        }
    )


def test_phase2_config_reads_shared_and_phase2():
    config = load_phase2_config(Path("config/research_queries.yaml"))
    assert config.country == "India"
    assert config.run_type == "dry_run"
    assert config.gender_filter == "female"
    assert "myntra.com" in config.retailers


def test_serpapi_parser_filters_retailers_and_extracts_fields():
    provider = SerpApiProvider("test-key")
    body = {"shopping_results": [
        {"title": "Kurta", "link": "https://www.myntra.com/kurta/123", "source": "Myntra", "extracted_price": 1299.0, "rating": 4.2, "reviews": 88, "thumbnail": "https://img.example.com/1.jpg", "product_id": 123},
        {"title": "Other", "link": "https://www.unknown-shop.example/item", "source": "Unknown"},
    ]}
    config = Phase2Config()
    products = provider._parse(body, config)
    assert len(products) == 1
    assert products[0].domain == "myntra.com"
    assert products[0].price == 1299.0
    assert products[0].product_id == "123"


def test_serpapi_parser_matches_retailer_by_source_when_link_is_google_redirect():
    provider = SerpApiProvider("test-key")
    body = {"shopping_results": [
        {"title": "Kurta", "product_link": "https://www.google.com/search?ibp=oshop&q=kurta", "source": "Myntra", "extracted_price": 1299.0, "product_id": "999"},
        {"title": "Flipkart item", "product_link": "https://www.google.com/search?ibp=oshop&q=heels", "source": "Flipkart", "extracted_price": 799.0},
        {"title": "Random", "product_link": "https://www.google.com/search?ibp=oshop&q=bag", "source": "Some Shop"},
    ]}
    products = provider._parse(body, Phase2Config())
    assert [p.domain for p in products] == ["myntra.com", "flipkart.com"]
    assert products[0].retailer == "Myntra"


def test_phase2_gender_filter_skips_mismatched_outfit(tmp_path: Path):
    config = Phase2Config(gender_filter="male", output_dir=str(tmp_path))
    report, path = run(_outfit(gender="female"), config, provider=None if False else _FakeProvider())
    assert report.items == []
    assert "gender_filter" in report.warnings[0]
    assert Path(path).exists()


def test_phase2_dry_run_searches_only_first_item(tmp_path: Path):
    provider = _FakeProvider()
    config = Phase2Config(run_type="dry_run", output_dir=str(tmp_path), download_images=False)
    report, _ = run(_outfit(), config, provider=provider)
    assert provider.calls == 1
    assert len(report.items) == 1
    assert any("dry_run" in w for w in report.warnings)


def test_phase2_production_searches_all_items(tmp_path: Path):
    provider = _FakeProvider()
    config = Phase2Config(run_type="production", output_dir=str(tmp_path), download_images=False, resolve_product_links=False)
    report, _ = run(_outfit(), config, provider=provider)
    assert provider.calls == 2
    assert len(report.items) == 2
    assert report.items[0].products[0].domain == "myntra.com"


class _FakeProvider:
    def __init__(self):
        self.calls = 0

    def search(self, query, config):
        self.calls += 1
        return [ProductCandidate(title="Kurta", product_url="https://www.myntra.com/k/1", retailer="Myntra", domain="myntra.com", price=999.0, currency="INR")]

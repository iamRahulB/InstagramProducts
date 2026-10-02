import logging
import time
from typing import Any, Protocol
from urllib.parse import urlsplit

import httpx

from .models import Phase2Config, ProductCandidate

logger = logging.getLogger(__name__)


class ProductSearchProvider(Protocol):
    def search(self, query: str, config: Phase2Config) -> list[ProductCandidate]: ...
    def resolve_link(self, product: ProductCandidate) -> ProductCandidate: ...


class SerpApiProvider:
    """SerpApi google_shopping adapter. Never invents product data."""

    def __init__(self, api_key: str, timeout: float = 30.0, max_attempts: int = 2, retry_base_seconds: float = 5.0):
        self.api_key = api_key
        self.client = httpx.Client(timeout=timeout)
        self.max_attempts = max_attempts
        self.retry_base_seconds = retry_base_seconds

    def search(self, query: str, config: Phase2Config) -> list[ProductCandidate]:
        params = {
            "engine": config.serpapi_engine,
            "q": query,
            "gl": config.gl,
            "hl": config.hl,
            "api_key": self.api_key,
        }
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.client.get("https://serpapi.com/search.json", params=params)
            except httpx.TimeoutException:
                if attempt == self.max_attempts:
                    raise
                time.sleep(self.retry_base_seconds * (2 ** (attempt - 1)))
                continue
            if response.status_code not in {408, 429, 500, 502, 503, 504} or attempt == self.max_attempts:
                break
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else self.retry_base_seconds * (2 ** (attempt - 1))
            logger.warning("SerpApi transient response %s; retrying in %.1fs", response.status_code, delay)
            time.sleep(delay)
        response.raise_for_status()
        return self._parse(response.json(), config)

    def resolve_link(self, product: ProductCandidate) -> ProductCandidate:
        """Resolve to the direct merchant URL via google_immersive_product stores[].link."""
        token = product.page_token
        if not token:
            return product
        try:
            response = self.client.get(
                "https://serpapi.com/search.json",
                params={"engine": "google_immersive_product", "page_token": token, "api_key": self.api_key},
            )
            response.raise_for_status()
            stores = (response.json().get("product_results", {}) or {}).get("stores", []) or []
            # Prefer the store matching the product's retailer/domain
            for store in stores:
                link = store.get("link")
                if not link:
                    continue
                link_domain = urlsplit(link).netloc.lower().removeprefix("www.")
                if link_domain == product.domain or link_domain.endswith("." + product.domain):
                    return product.model_copy(update={"product_url": link})
            # Otherwise take the first store link that isn't a Google URL
            for store in stores:
                link = store.get("link")
                if link and "google.com" not in link:
                    return product.model_copy(update={"product_url": link})
        except Exception as exc:
            logger.warning("Immersive link resolution failed for %s: %s", product.title, exc)
        return product

    def _parse(self, body: dict[str, Any], config: Phase2Config) -> list[ProductCandidate]:
        candidates: list[ProductCandidate] = []
        for result in body.get("shopping_results", []) or []:
            link = result.get("link") or result.get("product_link")
            if not link:
                continue
            source = str(result.get("source") or "")
            domain = urlsplit(link).netloc.lower().removeprefix("www.")
            # google_shopping product_link is a Google redirect; the retailer is in `source`.
            retailer_domain = self._retailer_domain(source, domain, config.retailers)
            if config.retailers and retailer_domain is None:
                continue
            domain = retailer_domain or domain
            price = result.get("extracted_price")
            if price is None and isinstance(result.get("price"), str):
                digits = "".join(ch for ch in result["price"] if ch.isdigit() or ch == ".")
                price = float(digits) if digits else None
            try:
                candidates.append(
                    ProductCandidate(
                        title=result.get("title", "Untitled product"),
                        product_url=link,
                        retailer=source or domain,
                        domain=domain,
                        price=price,
                        currency=config.currency if price is not None else None,
                        rating=result.get("rating"),
                        review_count=result.get("reviews"),
                        image_url=result.get("thumbnail"),
                        thumbnail=result.get("thumbnail"),
                        product_id=str(result.get("product_id")) if result.get("product_id") else None,
                        availability=result.get("delivery") or result.get("availability"),
                        page_token=result.get("immersive_product_page_token"),
                    )
                )
            except Exception as exc:
                logger.warning("Skipping malformed product result: %s", exc)
        return candidates[: config.max_products_per_item]

    @staticmethod
    def _retailer_domain(source: str, link_domain: str, retailers: list[str]) -> str | None:
        """Match a result to a configured retailer by source name or link domain."""
        source_norm = source.lower().replace(" ", "").replace("-", "")
        for retailer in retailers:
            name = retailer.split(".")[0]
            if name in source_norm or link_domain == retailer or link_domain.endswith("." + retailer):
                return retailer
        return None

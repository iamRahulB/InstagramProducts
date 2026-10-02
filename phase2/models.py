from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Phase2Config(BaseModel):
    enabled: bool = True
    run_type: Literal["dry_run", "production"] = "dry_run"
    country: str = "India"
    gender_filter: Literal["male", "female", "both"] = "both"
    max_products_per_item: int = Field(default=5, ge=1, le=20)
    serpapi_engine: str = "google_shopping"
    gl: str = "in"
    hl: str = "en"
    currency: str = "INR"
    download_images: bool = True
    resolve_product_links: bool = True
    retailers: list[str] = Field(default_factory=lambda: ["myntra.com", "amazon.in", "flipkart.com"])
    output_dir: str = "data/products"


class ProductCandidate(BaseModel):
    title: str = Field(min_length=1)
    product_url: HttpUrl
    retailer: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    price: float | None = None
    currency: str | None = None
    rating: float | None = None
    review_count: int | None = None
    image_url: HttpUrl | None = None
    thumbnail: HttpUrl | None = None
    product_id: str | None = None
    source: str = "serpapi"
    availability: str | None = None
    local_image_path: str | None = None
    page_token: str | None = Field(default=None, exclude=True)


class ItemDiscovery(BaseModel):
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    search_query: str = Field(min_length=1)
    products: list[ProductCandidate] = Field(default_factory=list)
    error: str | None = None


class ProductDiscoveryReport(BaseModel):
    research_id: str = Field(min_length=1)
    outfit_id: str = Field(min_length=1)
    country: str = Field(min_length=1)
    gender: str = Field(min_length=1)
    items: list[ItemDiscovery] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

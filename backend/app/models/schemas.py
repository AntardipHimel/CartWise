from pydantic import BaseModel, Field


class ShoppingFilter(BaseModel):
    brand: str | None = None
    package_size: float | None = None
    package_unit: str | None = None
    max_price: float | None = None
    must_buy: bool = True
    allow_substitutes: bool = True


class ShoppingItem(BaseModel):
    item_key: str
    filters: ShoppingFilter = Field(default_factory=ShoppingFilter)


class CandidateProduct(BaseModel):
    store_id: str
    product_id: str
    price: float
    match_score: float
    brand: str | None = None
    package_size: float | None = None
    package_unit: str | None = None
    item_name: str | None = None
    vendor: str | None = None


class StoreNode(BaseModel):
    store_id: str
    lat: float
    lon: float
    name: str | None = None
    vendor: str | None = None
    open_time: str = "08:00"
    close_time: str = "22:00"
    visit_penalty_minutes: int = 10


class CandidateBundle(BaseModel):
    item_key: str
    filters: ShoppingFilter
    candidates: list[CandidateProduct]


class OptimizeRequest(BaseModel):
    email: str | None = None
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    trip_start_time: str = "18:00"
    max_radius_miles: float = 15.0
    max_store_count: int = 3
    vehicle_mpg: float = 25.0
    gas_price_per_gallon: float = 3.50
    candidate_limit_per_item: int = 30
    minimum_multi_store_savings: float = 2.0
    items: list[ShoppingItem]


class SelectedProduct(BaseModel):
    item_key: str
    store_id: str
    product_id: str
    price: float
    match_score: float
    brand: str | None = None
    package_size: float | None = None
    package_unit: str | None = None
    item_name: str | None = None
    vendor: str | None = None


class RouteCategory(BaseModel):
    category: str
    summary: str
    stores: list[dict]
    route: list[dict]
    included_products: list[SelectedProduct]
    missing_items: list[str]
    metrics: dict


class OptimizeResponse(BaseModel):
    recommended_category: str
    recommendation_reason: str
    request_context: dict
    categories: dict[str, RouteCategory]
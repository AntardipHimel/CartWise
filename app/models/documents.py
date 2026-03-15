from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    username: str
    email: str
    zip_code: str
    preferred_stores: list[str] = []
    regular_items: list[str] = []
    brand_preferences: dict[str, str] = {}
    vehicle_mpg: float = 25.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)


class ProductCandidate(BaseModel):
    name: str
    brand: str = ""
    store_id: str
    store_name: str
    price: float
    unit_size: float
    unit_type: str
    category: str = ""
    image_url: str = ""
    upc: str = ""
    in_stock: bool = True
    stock_confidence: float = 1.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PriceCache(BaseModel):
    item_query: str
    store_id: str
    candidates: list[ProductCandidate]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = None


class PurchasedItem(BaseModel):
    query: str
    product_name: str
    brand: str = ""
    store_id: str
    store_name: str = ""
    price: float
    unit_size: float = 0
    unit_type: str = ""
    quantity: int = 1


class RouteTaken(BaseModel):
    total_distance_miles: float = 0
    total_time_minutes: float = 0
    gas_cost: float = 0


class ShoppingTrip(BaseModel):
    user_id: str
    trip_date: datetime = Field(default_factory=datetime.utcnow)
    plan_chosen: str = "single"
    items_purchased: list[PurchasedItem] = []
    stores_visited: list[str] = []
    route_taken: RouteTaken = Field(default_factory=RouteTaken)
    total_spent: float = 0.0
    total_saved: float = 0.0


class ItemPattern(BaseModel):
    user_id: str
    item_query: str
    preferred_brand: str = ""
    preferred_size: str = ""
    preferred_store: str = ""
    avg_price_paid: float = 0.0
    purchase_count: int = 0
    avg_days_between: float = 0.0
    last_purchased: datetime = Field(default_factory=datetime.utcnow)
    next_expected: datetime = None


class PriceHistoryEntry(BaseModel):
    price: float
    date: datetime = Field(default_factory=datetime.utcnow)


class PriceHistory(BaseModel):
    product_name: str
    store_id: str
    prices: list[PriceHistoryEntry] = []
    trend: str = "stable"
    lowest_seen: float = 0.0
    avg_price: float = 0.0


class DemandSignal(BaseModel):
    product_name: str
    store_id: str
    zip_code: str
    recommendation_count: int = 0
    last_recommended: datetime = Field(default_factory=datetime.utcnow)
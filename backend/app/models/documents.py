from datetime import datetime
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


class ShoppingTrip(BaseModel):
    user_id: str
    items_purchased: list[dict] = []
    stores_visited: list[str] = []
    total_spent: float = 0.0
    total_saved: float = 0.0
    trip_date: datetime = Field(default_factory=datetime.utcnow)


class DemandSignal(BaseModel):
    product_name: str
    store_id: str
    zip_code: str
    recommendation_count: int = 0
    last_recommended: datetime = Field(default_factory=datetime.utcnow)
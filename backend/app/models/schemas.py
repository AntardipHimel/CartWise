from pydantic import BaseModel
from typing import Optional


class ShoppingItem(BaseModel):
    name: str
    quantity: int = 1
    preferred_brand: Optional[str] = None
    category: Optional[str] = None


class Store(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    rating: float = 4.0
    address: Optional[str] = None


class PriceEntry(BaseModel):
    item_name: str
    store_id: str
    price: float
    unit_size: float
    unit_type: str
    on_sale: bool = False
    brand: Optional[str] = None


class OptimizeRequest(BaseModel):
    items: list[ShoppingItem]
    user_lat: float
    user_lng: float
    convenience_weight: float = 0.5
    gas_price_per_gallon: float = 3.50
    vehicle_mpg: float = 25.0


class StorePlan(BaseModel):
    stores: list[Store]
    items_per_store: dict[str, list[str]]
    total_item_cost: float
    travel_cost: float
    travel_time_minutes: float
    travel_distance_miles: float
    net_savings: float


class OptimizeResponse(BaseModel):
    single_store_plan: StorePlan
    multi_store_plan: StorePlan
    recommended: str
    total_savings_vs_worst: float
    recommendation_reason: str

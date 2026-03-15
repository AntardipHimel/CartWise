from datetime import datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    email: str
    password_hash: str = ""
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    destination_latitude: float = 0.0
    destination_longitude: float = 0.0
    max_drive_miles: float = 15.0
    max_store_count: int = 3
    vehicle_mpg: float = 25.0
    gas_price: float = 3.50
    brand_preferences: dict[str, str] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Store(BaseModel):
    store_id: str
    vendor: str
    name: str
    address: str = ""
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    open_time: str = "08:00"
    close_time: str = "22:00"
    visit_penalty_minutes: int = 10
    is_active: bool = True


class Product(BaseModel):
    product_id: str
    store_id: str
    vendor: str
    item_key: str
    item_name: str
    brand: str = ""
    package_size: float = 0.0
    package_unit: str = ""
    price: float = 0.0
    match_score: float = 1.0
    in_stock: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)
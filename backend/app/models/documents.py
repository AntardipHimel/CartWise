from datetime import datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    email: str
    password_hash: str = ""
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    max_drive_miles: float = 15.0
    vehicle_mpg: float = 25.0
    gas_price: float = 3.50
    brand_preferences: dict[str, str] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Store(BaseModel):
    store_id: str
    name: str
    chain: str
    address: str = ""
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    rating: float = 4.0
    hours: str = ""
    phone: str = ""


class Product(BaseModel):
    store_id: str
    product_name: str
    generic_name: str
    brand: str = ""
    price: float = 0.0
    unit_size: float = 0.0
    unit_type: str = ""
    category: str = ""
    upc: str = ""
    image_url: str = ""
    in_stock: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)
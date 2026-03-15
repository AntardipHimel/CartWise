import asyncio
import random
from datetime import datetime

from app.db import connect_db, get_db

STORE_COUNT = 1000
PRODUCT_COUNT = 100000
PRODUCTS_PER_STORE = PRODUCT_COUNT // STORE_COUNT

VENDOR_CONFIG = {
    "walmart": {
        "name_prefix": "Walmart",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 14,
    },
    "kroger": {
        "name_prefix": "Kroger",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 12,
    },
    "target": {
        "name_prefix": "Target",
        "open_time": "08:00",
        "close_time": "22:00",
        "visit_penalty_minutes": 12,
    },
    "costco": {
        "name_prefix": "Costco",
        "open_time": "10:00",
        "close_time": "20:30",
        "visit_penalty_minutes": 18,
    },
    "traderjoes": {
        "name_prefix": "Trader Joe's",
        "open_time": "08:00",
        "close_time": "21:00",
        "visit_penalty_minutes": 10,
    },
}

AREA_CENTERS = [
    ("Mountain View", "94040", 37.3861, -122.0839),
    ("Palo Alto", "94301", 37.4419, -122.1430),
    ("Sunnyvale", "94085", 37.3688, -122.0363),
    ("Santa Clara", "95050", 37.3541, -121.9552),
    ("Cupertino", "95014", 37.3229, -122.0322),
    ("Redwood City", "94063", 37.4852, -122.2364),
    ("San Mateo", "94401", 37.5630, -122.3255),
    ("Menlo Park", "94025", 37.4530, -122.1817),
]

ITEM_CATALOG = [
    {"item_key": "milk", "display_name": "Whole Milk", "category": "Dairy", "brands": ["Great Value", "Kroger", "Good & Gather", "Organic Valley", "Fairlife"], "sizes": [(1, "gallon"), (64, "fl_oz"), (128, "fl_oz")]},
    {"item_key": "eggs", "display_name": "Large Eggs", "category": "Dairy", "brands": ["Great Value", "Kroger", "Good & Gather", "Eggland's Best"], "sizes": [(12, "count"), (18, "count"), (24, "count")]},
    {"item_key": "bread", "display_name": "Bread", "category": "Bakery", "brands": ["Great Value", "Kroger", "Nature's Own", "Good & Gather"], "sizes": [(20, "oz"), (24, "oz")]},
    {"item_key": "rice", "display_name": "Rice", "category": "Grains", "brands": ["Great Value", "Kroger", "Royal", "Mahatma"], "sizes": [(2, "lb"), (5, "lb"), (10, "lb"), (20, "lb")]},
    {"item_key": "chicken breast", "display_name": "Chicken Breast", "category": "Meat", "brands": ["Great Value", "Kroger", "Tyson", "Good & Gather"], "sizes": [(1.5, "lb"), (2, "lb"), (2.5, "lb"), (3, "lb")]},
    {"item_key": "olive oil", "display_name": "Olive Oil", "category": "Cooking", "brands": ["Great Value", "Kroger", "Good & Gather", "Bertolli"], "sizes": [(16.9, "fl_oz"), (17, "fl_oz"), (34, "fl_oz"), (67.6, "fl_oz")]},
    {"item_key": "bananas", "display_name": "Bananas", "category": "Produce", "brands": [""], "sizes": [(1, "lb"), (3, "lb"), (1, "count")]},
    {"item_key": "cereal", "display_name": "Cereal", "category": "Breakfast", "brands": ["Great Value", "Kroger", "Cheerios", "Good & Gather"], "sizes": [(12, "oz"), (18, "oz"), (24, "oz")]},
    {"item_key": "pasta", "display_name": "Pasta", "category": "Grains", "brands": ["Great Value", "Kroger", "Barilla", "Good & Gather"], "sizes": [(12, "oz"), (16, "oz"), (32, "oz")]},
    {"item_key": "laundry detergent", "display_name": "Laundry Detergent", "category": "Household", "brands": ["Tide", "Great Value", "Kroger", "Gain"], "sizes": [(64, "fl_oz"), (92, "fl_oz"), (128, "fl_oz")]},
    {"item_key": "broccoli", "display_name": "Broccoli", "category": "Produce", "brands": [""], "sizes": [(1, "count"), (12, "oz"), (1, "lb")]},
    {"item_key": "apples", "display_name": "Apples", "category": "Produce", "brands": ["Gala", "Fuji", "Honeycrisp"], "sizes": [(2, "lb"), (3, "lb"), (1, "count")]},
    {"item_key": "oranges", "display_name": "Oranges", "category": "Produce", "brands": ["Navel", "Cara Cara"], "sizes": [(2, "lb"), (3, "lb"), (1, "count")]},
    {"item_key": "yogurt", "display_name": "Greek Yogurt", "category": "Dairy", "brands": ["Chobani", "Oikos", "Kroger", "Great Value"], "sizes": [(5.3, "oz"), (32, "oz")]},
    {"item_key": "cheese", "display_name": "Cheese", "category": "Dairy", "brands": ["Kraft", "Kroger", "Great Value", "Sargento"], "sizes": [(8, "oz"), (16, "oz")]},
    {"item_key": "butter", "display_name": "Butter", "category": "Dairy", "brands": ["Kroger", "Great Value", "Land O Lakes"], "sizes": [(16, "oz"), (32, "oz")]},
    {"item_key": "coffee", "display_name": "Coffee", "category": "Beverages", "brands": ["Folgers", "Maxwell House", "Kroger", "Starbucks"], "sizes": [(12, "oz"), (24, "oz"), (40, "oz")]},
    {"item_key": "tea", "display_name": "Tea Bags", "category": "Beverages", "brands": ["Lipton", "Kroger", "Bigelow"], "sizes": [(20, "count"), (40, "count"), (80, "count")]},
    {"item_key": "juice", "display_name": "Orange Juice", "category": "Beverages", "brands": ["Tropicana", "Simply", "Kroger", "Great Value"], "sizes": [(52, "fl_oz"), (89, "fl_oz")]},
    {"item_key": "water", "display_name": "Bottled Water", "category": "Beverages", "brands": ["Pure Life", "Dasani", "Kroger", "Great Value"], "sizes": [(24, "count"), (32, "count"), (40, "count")]},
    {"item_key": "chips", "display_name": "Potato Chips", "category": "Snacks", "brands": ["Lay's", "Kroger", "Great Value", "Ruffles"], "sizes": [(7.75, "oz"), (9, "oz"), (13, "oz")]},
    {"item_key": "cookies", "display_name": "Cookies", "category": "Snacks", "brands": ["Oreo", "Chips Ahoy", "Kroger", "Great Value"], "sizes": [(10, "oz"), (14, "oz"), (20, "oz")]},
    {"item_key": "crackers", "display_name": "Crackers", "category": "Snacks", "brands": ["Ritz", "Kroger", "Great Value"], "sizes": [(10, "oz"), (13.7, "oz")]},
    {"item_key": "soda", "display_name": "Soda", "category": "Beverages", "brands": ["Coca-Cola", "Pepsi", "Sprite", "Dr Pepper"], "sizes": [(12, "count"), (24, "count")]},
    {"item_key": "sparkling water", "display_name": "Sparkling Water", "category": "Beverages", "brands": ["LaCroix", "Bubly", "Kroger"], "sizes": [(8, "count"), (12, "count")]},
    {"item_key": "toilet paper", "display_name": "Toilet Paper", "category": "Household", "brands": ["Charmin", "Scott", "Kroger", "Great Value"], "sizes": [(6, "count"), (12, "count"), (24, "count")]},
    {"item_key": "paper towels", "display_name": "Paper Towels", "category": "Household", "brands": ["Bounty", "Kroger", "Great Value"], "sizes": [(2, "count"), (6, "count"), (12, "count")]},
    {"item_key": "dish soap", "display_name": "Dish Soap", "category": "Household", "brands": ["Dawn", "Palmolive", "Kroger"], "sizes": [(19.4, "fl_oz"), (28, "fl_oz")]},
    {"item_key": "shampoo", "display_name": "Shampoo", "category": "Personal Care", "brands": ["Pantene", "Head & Shoulders", "Tresemme"], "sizes": [(12, "fl_oz"), (20, "fl_oz")]},
    {"item_key": "toothpaste", "display_name": "Toothpaste", "category": "Personal Care", "brands": ["Colgate", "Crest"], "sizes": [(3.5, "oz"), (5.5, "oz")]},
    {"item_key": "soap", "display_name": "Bar Soap", "category": "Personal Care", "brands": ["Dove", "Irish Spring", "Dial"], "sizes": [(6, "count"), (8, "count")]},
    {"item_key": "frozen pizza", "display_name": "Frozen Pizza", "category": "Frozen", "brands": ["DiGiorno", "Totino's", "Kroger"], "sizes": [(12, "oz"), (20, "oz"), (28, "oz")]},
    {"item_key": "ice cream", "display_name": "Ice Cream", "category": "Frozen", "brands": ["Ben & Jerry's", "Breyers", "Kroger"], "sizes": [(16, "fl_oz"), (48, "fl_oz")]},
    {"item_key": "frozen vegetables", "display_name": "Frozen Vegetables", "category": "Frozen", "brands": ["Birds Eye", "Kroger", "Great Value"], "sizes": [(10, "oz"), (12, "oz"), (16, "oz")]},
    {"item_key": "ground beef", "display_name": "Ground Beef", "category": "Meat", "brands": ["Kroger", "Great Value", "Simple Truth"], "sizes": [(1, "lb"), (2, "lb"), (3, "lb")]},
    {"item_key": "salmon", "display_name": "Salmon", "category": "Seafood", "brands": ["Kroger", "Great Value"], "sizes": [(12, "oz"), (1, "lb"), (2, "lb")]},
    {"item_key": "shrimp", "display_name": "Shrimp", "category": "Seafood", "brands": ["Kroger", "Great Value"], "sizes": [(12, "oz"), (16, "oz"), (2, "lb")]},
    {"item_key": "lettuce", "display_name": "Lettuce", "category": "Produce", "brands": [""], "sizes": [(1, "count"), (10, "oz")]},
    {"item_key": "tomatoes", "display_name": "Tomatoes", "category": "Produce", "brands": [""], "sizes": [(1, "lb"), (2, "lb"), (1, "count")]},
    {"item_key": "onions", "display_name": "Onions", "category": "Produce", "brands": [""], "sizes": [(2, "lb"), (3, "lb"), (1, "count")]},
    {"item_key": "potatoes", "display_name": "Potatoes", "category": "Produce", "brands": ["Russet", "Gold"], "sizes": [(3, "lb"), (5, "lb"), (10, "lb")]},
    {"item_key": "carrots", "display_name": "Carrots", "category": "Produce", "brands": [""], "sizes": [(1, "lb"), (2, "lb")]},
    {"item_key": "spinach", "display_name": "Spinach", "category": "Produce", "brands": ["Simple Truth", "Organic Girl", "Fresh Express"], "sizes": [(5, "oz"), (10, "oz")]},
    {"item_key": "cucumber", "display_name": "Cucumber", "category": "Produce", "brands": [""], "sizes": [(1, "count")]},
    {"item_key": "strawberries", "display_name": "Strawberries", "category": "Produce", "brands": [""], "sizes": [(16, "oz"), (32, "oz")]},
    {"item_key": "blueberries", "display_name": "Blueberries", "category": "Produce", "brands": [""], "sizes": [(6, "oz"), (18, "oz")]},
    {"item_key": "grapes", "display_name": "Grapes", "category": "Produce", "brands": [""], "sizes": [(1, "lb"), (2, "lb")]},
    {"item_key": "bagels", "display_name": "Bagels", "category": "Bakery", "brands": ["Thomas", "Kroger", "Great Value"], "sizes": [(6, "count")]},
    {"item_key": "muffins", "display_name": "Muffins", "category": "Bakery", "brands": ["Kroger", "Great Value"], "sizes": [(4, "count"), (6, "count")]},
    {"item_key": "peanut butter", "display_name": "Peanut Butter", "category": "Pantry", "brands": ["Jif", "Skippy", "Kroger", "Great Value"], "sizes": [(16, "oz"), (28, "oz"), (40, "oz")]},
    {"item_key": "jelly", "display_name": "Jelly", "category": "Pantry", "brands": ["Smucker's", "Kroger", "Great Value"], "sizes": [(18, "oz"), (30, "oz")]},
    {"item_key": "flour", "display_name": "Flour", "category": "Baking", "brands": ["Gold Medal", "Kroger", "Great Value"], "sizes": [(2, "lb"), (5, "lb"), (10, "lb")]},
    {"item_key": "sugar", "display_name": "Sugar", "category": "Baking", "brands": ["Domino", "Kroger", "Great Value"], "sizes": [(2, "lb"), (4, "lb"), (10, "lb")]},
    {"item_key": "salt", "display_name": "Salt", "category": "Spices", "brands": ["Morton", "Kroger"], "sizes": [(26, "oz")]},
    {"item_key": "black pepper", "display_name": "Black Pepper", "category": "Spices", "brands": ["McCormick", "Kroger"], "sizes": [(3, "oz"), (6, "oz")]},
]

DEMO_USERS = [
    {
        "name": "Demo User",
        "email": "demo@cartwise.com",
        "password_hash": "demo123",
        "zip_code": "94040",
        "latitude": 37.45,
        "longitude": -122.15,
        "destination_latitude": 37.45,
        "destination_longitude": -122.15,
        "max_drive_miles": 15.0,
        "max_store_count": 3,
        "vehicle_mpg": 28.0,
        "gas_price": 3.49,
        "brand_preferences": {},
        "created_at": datetime.utcnow(),
    }
]


def jitter_coordinate(lat: float, lon: float) -> tuple[float, float]:
    lat_offset = random.uniform(-0.12, 0.12)
    lon_offset = random.uniform(-0.12, 0.12)
    return round(lat + lat_offset, 6), round(lon + lon_offset, 6)


def build_stores() -> list[dict]:
    vendors = list(VENDOR_CONFIG.keys())
    stores: list[dict] = []

    for index in range(STORE_COUNT):
        vendor = vendors[index % len(vendors)]
        center_city, zip_code, base_lat, base_lon = AREA_CENTERS[index % len(AREA_CENTERS)]
        lat, lon = jitter_coordinate(base_lat, base_lon)
        vendor_meta = VENDOR_CONFIG[vendor]

        stores.append(
            {
                "store_id": f"{vendor}-{index + 1:04d}",
                "vendor": vendor,
                "name": f"{vendor_meta['name_prefix']} {center_city} #{index + 1:04d}",
                "address": f"{100 + (index % 9000)} {center_city} Ave",
                "zip_code": zip_code,
                "latitude": lat,
                "longitude": lon,
                "open_time": vendor_meta["open_time"],
                "close_time": vendor_meta["close_time"],
                "visit_penalty_minutes": vendor_meta["visit_penalty_minutes"],
                "is_active": True,
            }
        )

    return stores


def format_item_name(brand: str, display_name: str, package_size: float, package_unit: str) -> str:
    size_text = f"{package_size:g} {package_unit}"
    if brand:
        return f"{brand} {display_name} {size_text}"
    return f"{display_name} {size_text}"


def vendor_brand_adjustment(vendor: str, brands: list[str]) -> list[str]:
    if vendor == "costco":
        if "Kirkland" not in brands:
            return ["Kirkland"] + brands[:2]
    if vendor == "traderjoes":
        return ["Trader Joe's"] + brands[:2]
    return brands


def build_products_for_store(store: dict, rng: random.Random) -> list[dict]:
    catalog_sample = rng.sample(ITEM_CATALOG, k=min(PRODUCTS_PER_STORE, len(ITEM_CATALOG)))
    products: list[dict] = []

    while len(products) < PRODUCTS_PER_STORE:
        if len(products) < len(catalog_sample):
            item = catalog_sample[len(products)]
        else:
            item = rng.choice(ITEM_CATALOG)

        candidate_brands = vendor_brand_adjustment(store["vendor"], item["brands"])
        brand = rng.choice(candidate_brands)
        package_size, package_unit = rng.choice(item["sizes"])

        base_price = max(0.99, package_size * rng.uniform(0.4, 2.6))
        if store["vendor"] == "costco":
            base_price *= 1.4
            package_size = package_size * (2 if package_unit in {"count", "oz", "fl_oz"} else 1.5)
        elif store["vendor"] == "traderjoes":
            base_price *= 1.05
        elif store["vendor"] == "walmart":
            base_price *= 0.96

        price = round(base_price, 2)
        match_score = round(rng.uniform(0.82, 1.0), 3)

        product = {
            "product_id": f"{store['store_id']}-p{len(products) + 1:03d}",
            "store_id": store["store_id"],
            "vendor": store["vendor"],
            "item_key": item["item_key"],
            "item_name": format_item_name(brand, item["display_name"], package_size, package_unit),
            "brand": brand,
            "package_size": round(package_size, 2),
            "package_unit": package_unit,
            "price": price,
            "match_score": match_score,
            "in_stock": rng.random() > 0.08,
            "last_updated": datetime.utcnow(),
        }
        products.append(product)

    return products


async def recreate_indexes(db):
    try:
        await db.stores.drop_index("store_id_1")
    except Exception:
        pass

    try:
        await db.products.drop_index("product_id_1")
    except Exception:
        pass

    try:
        await db.users.drop_index("email_1")
    except Exception:
        pass

    await db.stores.create_index("store_id", unique=True)
    await db.stores.create_index([("latitude", 1), ("longitude", 1)])
    await db.stores.create_index("vendor")
    await db.stores.create_index("is_active")

    await db.products.create_index("product_id", unique=True)
    await db.products.create_index("store_id")
    await db.products.create_index("item_key")
    await db.products.create_index([("item_key", 1), ("brand", 1)])
    await db.products.create_index([("item_key", 1), ("package_size", 1), ("package_unit", 1)])
    await db.products.create_index([("item_key", 1), ("price", 1)])
    await db.products.create_index([("store_id", 1), ("item_key", 1)])
    await db.products.create_index("in_stock")

    await db.users.create_index("email", unique=True)
    await db.shopping_trips.create_index("user_id")
    await db.shopping_trips.create_index("trip_date")


async def seed_database():
    await connect_db()
    db = get_db()

    await db.stores.delete_many({})
    await db.products.delete_many({})
    await db.users.delete_many({})
    await db.shopping_trips.delete_many({})

    stores = build_stores()
    await db.stores.insert_many(stores)
    print(f"Inserted {len(stores)} stores")

    rng = random.Random(42)
    product_buffer: list[dict] = []

    for store in stores:
        product_buffer.extend(build_products_for_store(store, rng))

        if len(product_buffer) >= 5000:
            await db.products.insert_many(product_buffer)
            print(f"Inserted {len(product_buffer)} products batch")
            product_buffer = []

    if product_buffer:
        await db.products.insert_many(product_buffer)
        print(f"Inserted {len(product_buffer)} products batch")

    await db.users.insert_many(DEMO_USERS)
    print(f"Inserted {len(DEMO_USERS)} demo user(s)")

    await recreate_indexes(db)
    print("Indexes created")
    print(f"Seed complete with {STORE_COUNT} stores and {PRODUCT_COUNT} products target")


if __name__ == "__main__":
    asyncio.run(seed_database())
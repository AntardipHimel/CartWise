import asyncio
from datetime import datetime
from app.db import connect_db, get_db


STORES = [
    {"store_id": "walmart-mv-01", "name": "Walmart Supercenter", "chain": "walmart", "address": "555 Showers Dr, Mountain View, CA", "zip_code": "94040", "latitude": 37.4849, "longitude": -122.1478, "rating": 3.8, "hours": "6AM-11PM"},
    {"store_id": "walmart-pa-01", "name": "Walmart Neighborhood Market", "chain": "walmart", "address": "2100 El Camino Real, Palo Alto, CA", "zip_code": "94306", "latitude": 37.4219, "longitude": -122.1430, "rating": 3.6, "hours": "7AM-11PM"},
    {"store_id": "kroger-mv-01", "name": "Kroger", "chain": "kroger", "address": "3922 Middlefield Rd, Mountain View, CA", "zip_code": "94040", "latitude": 37.4600, "longitude": -122.1200, "rating": 3.9, "hours": "6AM-12AM"},
    {"store_id": "kroger-sv-01", "name": "Kroger Marketplace", "chain": "kroger", "address": "750 E Arques Ave, Sunnyvale, CA", "zip_code": "94085", "latitude": 37.3825, "longitude": -122.0245, "rating": 4.1, "hours": "6AM-11PM"},
    {"store_id": "costco-mv-01", "name": "Costco Wholesale", "chain": "costco", "address": "1000 N Rengstorff Ave, Mountain View, CA", "zip_code": "94043", "latitude": 37.4255, "longitude": -122.0980, "rating": 4.4, "hours": "10AM-8:30PM"},
    {"store_id": "tj-pa-01", "name": "Trader Joe's", "chain": "traderjoes", "address": "855 El Camino Real, Palo Alto, CA", "zip_code": "94301", "latitude": 37.4400, "longitude": -122.1600, "rating": 4.5, "hours": "8AM-9PM"},
    {"store_id": "target-sv-01", "name": "Target", "chain": "target", "address": "1 Levis Plaza, Sunnyvale, CA", "zip_code": "94089", "latitude": 37.3890, "longitude": -122.0150, "rating": 4.1, "hours": "8AM-10PM"},
]

PRODUCTS = [
    # MILK
    {"store_id": "walmart-mv-01", "product_name": "Great Value Whole Milk 1 Gallon", "generic_name": "milk", "brand": "Great Value", "price": 3.48, "unit_size": 128, "unit_type": "fl_oz", "category": "Dairy"},
    {"store_id": "walmart-mv-01", "product_name": "Fairlife Whole Milk 52oz", "generic_name": "milk", "brand": "Fairlife", "price": 5.98, "unit_size": 52, "unit_type": "fl_oz", "category": "Dairy"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Whole Milk 1 Gallon", "generic_name": "milk", "brand": "Kroger", "price": 3.29, "unit_size": 128, "unit_type": "fl_oz", "category": "Dairy"},
    {"store_id": "kroger-mv-01", "product_name": "Organic Valley Whole Milk 64oz", "generic_name": "milk", "brand": "Organic Valley", "price": 6.49, "unit_size": 64, "unit_type": "fl_oz", "category": "Dairy"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Whole Milk 2 Gallon", "generic_name": "milk", "brand": "Kirkland", "price": 6.49, "unit_size": 256, "unit_type": "fl_oz", "category": "Dairy"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Whole Milk 1 Gallon", "generic_name": "milk", "brand": "Trader Joe's", "price": 3.99, "unit_size": 128, "unit_type": "fl_oz", "category": "Dairy"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather Whole Milk 1 Gallon", "generic_name": "milk", "brand": "Good & Gather", "price": 3.89, "unit_size": 128, "unit_type": "fl_oz", "category": "Dairy"},

    # EGGS
    {"store_id": "walmart-mv-01", "product_name": "Great Value Large Eggs 12ct", "generic_name": "eggs", "brand": "Great Value", "price": 3.12, "unit_size": 12, "unit_type": "count", "category": "Dairy"},
    {"store_id": "walmart-mv-01", "product_name": "Eggland's Best Large Eggs 12ct", "generic_name": "eggs", "brand": "Eggland's Best", "price": 4.98, "unit_size": 12, "unit_type": "count", "category": "Dairy"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Large Eggs 12ct", "generic_name": "eggs", "brand": "Kroger", "price": 2.99, "unit_size": 12, "unit_type": "count", "category": "Dairy"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Organic Eggs 36ct", "generic_name": "eggs", "brand": "Kirkland", "price": 7.99, "unit_size": 36, "unit_type": "count", "category": "Dairy"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Free Range Eggs 12ct", "generic_name": "eggs", "brand": "Trader Joe's", "price": 3.79, "unit_size": 12, "unit_type": "count", "category": "Dairy"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather Large Eggs 12ct", "generic_name": "eggs", "brand": "Good & Gather", "price": 3.49, "unit_size": 12, "unit_type": "count", "category": "Dairy"},

    # BREAD
    {"store_id": "walmart-mv-01", "product_name": "Great Value White Bread 20oz", "generic_name": "bread", "brand": "Great Value", "price": 2.48, "unit_size": 20, "unit_type": "oz", "category": "Bakery"},
    {"store_id": "walmart-mv-01", "product_name": "Nature's Own Whole Wheat 20oz", "generic_name": "bread", "brand": "Nature's Own", "price": 4.28, "unit_size": 20, "unit_type": "oz", "category": "Bakery"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger White Bread 20oz", "generic_name": "bread", "brand": "Kroger", "price": 2.79, "unit_size": 20, "unit_type": "oz", "category": "Bakery"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Artisan Bread 44oz", "generic_name": "bread", "brand": "Kirkland", "price": 4.99, "unit_size": 44, "unit_type": "oz", "category": "Bakery"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Sourdough Bread 24oz", "generic_name": "bread", "brand": "Trader Joe's", "price": 3.49, "unit_size": 24, "unit_type": "oz", "category": "Bakery"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather White Bread 20oz", "generic_name": "bread", "brand": "Good & Gather", "price": 3.29, "unit_size": 20, "unit_type": "oz", "category": "Bakery"},

    # RICE
    {"store_id": "walmart-mv-01", "product_name": "Great Value Long Grain Rice 5lb", "generic_name": "rice", "brand": "Great Value", "price": 3.98, "unit_size": 5, "unit_type": "lb", "category": "Grains"},
    {"store_id": "walmart-mv-01", "product_name": "Mahatma Enriched Rice 5lb", "generic_name": "rice", "brand": "Mahatma", "price": 4.47, "unit_size": 5, "unit_type": "lb", "category": "Grains"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Long Grain Rice 5lb", "generic_name": "rice", "brand": "Kroger", "price": 4.29, "unit_size": 5, "unit_type": "lb", "category": "Grains"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Jasmine Rice 25lb", "generic_name": "rice", "brand": "Kirkland", "price": 16.99, "unit_size": 25, "unit_type": "lb", "category": "Grains"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Basmati Rice 3lb", "generic_name": "rice", "brand": "Trader Joe's", "price": 3.49, "unit_size": 3, "unit_type": "lb", "category": "Grains"},
    {"store_id": "target-sv-01", "product_name": "Market Pantry Long Grain Rice 5lb", "generic_name": "rice", "brand": "Market Pantry", "price": 4.49, "unit_size": 5, "unit_type": "lb", "category": "Grains"},

    # CHICKEN BREAST
    {"store_id": "walmart-mv-01", "product_name": "Great Value Chicken Breast 3lb", "generic_name": "chicken breast", "brand": "Great Value", "price": 8.47, "unit_size": 3, "unit_type": "lb", "category": "Meat"},
    {"store_id": "walmart-mv-01", "product_name": "Tyson Chicken Breast 2.5lb", "generic_name": "chicken breast", "brand": "Tyson", "price": 11.98, "unit_size": 2.5, "unit_type": "lb", "category": "Meat"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Chicken Breast 2.5lb", "generic_name": "chicken breast", "brand": "Kroger", "price": 7.99, "unit_size": 2.5, "unit_type": "lb", "category": "Meat"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Chicken Breast 6.5lb", "generic_name": "chicken breast", "brand": "Kirkland", "price": 22.99, "unit_size": 6.5, "unit_type": "lb", "category": "Meat"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Chicken Breast 1.5lb", "generic_name": "chicken breast", "brand": "Trader Joe's", "price": 6.99, "unit_size": 1.5, "unit_type": "lb", "category": "Meat"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather Chicken Breast 2lb", "generic_name": "chicken breast", "brand": "Good & Gather", "price": 9.99, "unit_size": 2, "unit_type": "lb", "category": "Meat"},

    # OLIVE OIL
    {"store_id": "walmart-mv-01", "product_name": "Great Value Extra Virgin Olive Oil 17oz", "generic_name": "olive oil", "brand": "Great Value", "price": 5.97, "unit_size": 17, "unit_type": "fl_oz", "category": "Cooking"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Extra Virgin Olive Oil 17oz", "generic_name": "olive oil", "brand": "Kroger", "price": 6.99, "unit_size": 17, "unit_type": "fl_oz", "category": "Cooking"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Organic Olive Oil 2L", "generic_name": "olive oil", "brand": "Kirkland", "price": 12.99, "unit_size": 67.6, "unit_type": "fl_oz", "category": "Cooking"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Spanish Olive Oil 16.9oz", "generic_name": "olive oil", "brand": "Trader Joe's", "price": 5.99, "unit_size": 16.9, "unit_type": "fl_oz", "category": "Cooking"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather Olive Oil 17oz", "generic_name": "olive oil", "brand": "Good & Gather", "price": 6.49, "unit_size": 17, "unit_type": "fl_oz", "category": "Cooking"},

    # BANANAS
    {"store_id": "walmart-mv-01", "product_name": "Bananas per lb", "generic_name": "bananas", "brand": "", "price": 0.62, "unit_size": 1, "unit_type": "lb", "category": "Produce"},
    {"store_id": "kroger-mv-01", "product_name": "Bananas per lb", "generic_name": "bananas", "brand": "", "price": 0.59, "unit_size": 1, "unit_type": "lb", "category": "Produce"},
    {"store_id": "costco-mv-01", "product_name": "Bananas 3lb Bunch", "generic_name": "bananas", "brand": "", "price": 1.99, "unit_size": 3, "unit_type": "lb", "category": "Produce"},
    {"store_id": "tj-pa-01", "product_name": "Bananas Each", "generic_name": "bananas", "brand": "", "price": 0.23, "unit_size": 1, "unit_type": "count", "category": "Produce"},
    {"store_id": "target-sv-01", "product_name": "Bananas per lb", "generic_name": "bananas", "brand": "", "price": 0.69, "unit_size": 1, "unit_type": "lb", "category": "Produce"},

    # CEREAL
    {"store_id": "walmart-mv-01", "product_name": "Great Value Toasted Oats 18oz", "generic_name": "cereal", "brand": "Great Value", "price": 3.98, "unit_size": 18, "unit_type": "oz", "category": "Breakfast"},
    {"store_id": "walmart-mv-01", "product_name": "Cheerios 18oz", "generic_name": "cereal", "brand": "General Mills", "price": 5.48, "unit_size": 18, "unit_type": "oz", "category": "Breakfast"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Toasted Oats 18oz", "generic_name": "cereal", "brand": "Kroger", "price": 3.79, "unit_size": 18, "unit_type": "oz", "category": "Breakfast"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Granola 40oz", "generic_name": "cereal", "brand": "Kirkland", "price": 7.49, "unit_size": 40, "unit_type": "oz", "category": "Breakfast"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Maple Oat Clusters 14oz", "generic_name": "cereal", "brand": "Trader Joe's", "price": 3.49, "unit_size": 14, "unit_type": "oz", "category": "Breakfast"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather Oat Crunch 18oz", "generic_name": "cereal", "brand": "Good & Gather", "price": 4.29, "unit_size": 18, "unit_type": "oz", "category": "Breakfast"},

    # PASTA
    {"store_id": "walmart-mv-01", "product_name": "Great Value Spaghetti 16oz", "generic_name": "pasta", "brand": "Great Value", "price": 1.28, "unit_size": 16, "unit_type": "oz", "category": "Grains"},
    {"store_id": "walmart-mv-01", "product_name": "Barilla Spaghetti 16oz", "generic_name": "pasta", "brand": "Barilla", "price": 1.98, "unit_size": 16, "unit_type": "oz", "category": "Grains"},
    {"store_id": "kroger-mv-01", "product_name": "Kroger Spaghetti 16oz", "generic_name": "pasta", "brand": "Kroger", "price": 1.39, "unit_size": 16, "unit_type": "oz", "category": "Grains"},
    {"store_id": "costco-mv-01", "product_name": "Barilla Spaghetti 4lb", "generic_name": "pasta", "brand": "Barilla", "price": 4.49, "unit_size": 64, "unit_type": "oz", "category": "Grains"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Italian Spaghetti 16oz", "generic_name": "pasta", "brand": "Trader Joe's", "price": 0.99, "unit_size": 16, "unit_type": "oz", "category": "Grains"},
    {"store_id": "target-sv-01", "product_name": "Good & Gather Spaghetti 16oz", "generic_name": "pasta", "brand": "Good & Gather", "price": 1.49, "unit_size": 16, "unit_type": "oz", "category": "Grains"},

    # LAUNDRY DETERGENT
    {"store_id": "walmart-mv-01", "product_name": "Tide Original 92oz", "generic_name": "laundry detergent", "brand": "Tide", "price": 11.97, "unit_size": 92, "unit_type": "fl_oz", "category": "Household"},
    {"store_id": "walmart-mv-01", "product_name": "Great Value Detergent 64oz", "generic_name": "laundry detergent", "brand": "Great Value", "price": 5.97, "unit_size": 64, "unit_type": "fl_oz", "category": "Household"},
    {"store_id": "kroger-mv-01", "product_name": "Tide Original 92oz", "generic_name": "laundry detergent", "brand": "Tide", "price": 11.49, "unit_size": 92, "unit_type": "fl_oz", "category": "Household"},
    {"store_id": "costco-mv-01", "product_name": "Kirkland Ultra Clean 170oz", "generic_name": "laundry detergent", "brand": "Kirkland", "price": 19.99, "unit_size": 170, "unit_type": "fl_oz", "category": "Household"},
    {"store_id": "tj-pa-01", "product_name": "Trader Joe's Liquid Detergent 64oz", "generic_name": "laundry detergent", "brand": "Trader Joe's", "price": 7.99, "unit_size": 64, "unit_type": "fl_oz", "category": "Household"},
    {"store_id": "target-sv-01", "product_name": "Tide Original 92oz", "generic_name": "laundry detergent", "brand": "Tide", "price": 12.49, "unit_size": 92, "unit_type": "fl_oz", "category": "Household"},
]


async def seed_database():
    await connect_db()
    db = get_db()

    await db.stores.delete_many({})
    await db.products.delete_many({})

    await db.stores.insert_many(STORES)
    print(f"Inserted {len(STORES)} stores")

    for p in PRODUCTS:
        p["last_updated"] = datetime.utcnow()
    await db.products.insert_many(PRODUCTS)
    print(f"Inserted {len(PRODUCTS)} products")

    await db.products.create_index("generic_name")
    await db.products.create_index("store_id")
    await db.stores.create_index("store_id")
    print("Indexes created")

    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
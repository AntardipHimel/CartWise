from app.db import get_db


async def load_stores(limit: int = 200):
    db = get_db()
    return await db.stores.find(
        {},
        {
            "_id": 0,
            "store_id": 1,
            "vendor": 1,
            "name": 1,
            "address": 1,
            "zip_code": 1,
            "latitude": 1,
            "longitude": 1,
            "open_time": 1,
            "close_time": 1,
            "visit_penalty_minutes": 1,
            "is_active": 1,
        },
    ).limit(limit).to_list(length=limit)


async def load_products(item_key: str | None = None, limit: int = 200):
    db = get_db()
    query = {}
    if item_key:
        query["item_key"] = item_key.lower()

    return await db.products.find(
        query,
        {
            "_id": 0,
            "product_id": 1,
            "store_id": 1,
            "vendor": 1,
            "item_key": 1,
            "item_name": 1,
            "brand": 1,
            "package_size": 1,
            "package_unit": 1,
            "price": 1,
            "match_score": 1,
            "in_stock": 1,
        },
    ).limit(limit).to_list(length=limit)
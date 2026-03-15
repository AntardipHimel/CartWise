from fastapi import APIRouter

from app.db import get_db

router = APIRouter()


@router.get("/products")
async def get_products(item_key: str | None = None, limit: int = 200):
    db = get_db()
    query = {}
    if item_key:
        query["item_key"] = item_key.lower()

    docs = await db.products.find(
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

    return {"products": docs, "count": len(docs)}
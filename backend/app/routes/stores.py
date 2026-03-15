from fastapi import APIRouter

from app.db import get_db

router = APIRouter()


@router.get("/stores")
async def get_stores(limit: int = 200):
    db = get_db()
    docs = await db.stores.find(
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

    return {"stores": docs, "count": len(docs)}
from fastapi import APIRouter, Query

from app.models.schemas import ShoppingItem
from app.services.candidate_engine import (
    build_candidate_bundles,
    get_item_filter_values,
    suggest_item_keys,
)

router = APIRouter()


@router.get("/items/suggest")
async def suggest_items(q: str = Query(..., min_length=1), limit: int = 12):
    suggestions = await suggest_item_keys(q, limit)
    return {
        "query": q,
        "suggestions": suggestions,
        "total": len(suggestions),
    }


@router.get("/items/{item_key}/filters")
async def get_filters_for_item(item_key: str):
    return await get_item_filter_values(item_key)


@router.post("/candidates/build")
async def build_candidates(data: dict):
    parsed_items = [ShoppingItem(**item) for item in data.get("items", [])]

    bundles, nearby_stores = await build_candidate_bundles(
        items=parsed_items,
        start_lat=float(data.get("start_lat")),
        start_lng=float(data.get("start_lng")),
        max_radius_miles=float(data.get("max_radius_miles", 15.0)),
        candidate_limit_per_item=int(data.get("candidate_limit_per_item", 30)),
    )

    return {
        "candidate_limit_per_item": int(data.get("candidate_limit_per_item", 30)),
        "nearby_store_count": len(nearby_stores),
        "nearby_stores": [store.model_dump() for store in nearby_stores],
        "items": [bundle.model_dump() for bundle in bundles],
    }
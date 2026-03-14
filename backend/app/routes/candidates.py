from fastapi import APIRouter
from app.services.candidate_engine import score_candidates, build_smart_list

router = APIRouter()


@router.get("/candidates/{query}")
async def get_candidates(query: str, limit: int = 10, sort_by: str = "value"):
    """
    Search for product candidates across all stores.
    User types 'rice' -> gets top 10 options ranked by value.
    """
    result = await score_candidates(query, limit=limit, sort_by=sort_by)
    return result


@router.post("/smart-list")
async def create_smart_list(data: dict):
    """
    Takes a list of generic item names, auto-selects best product for each.
    Input: {"items": ["rice", "milk", "eggs"], "preferences": {"brand_preferences": {"milk": "Kirkland"}}}
    """
    items = data.get("items", [])
    preferences = data.get("preferences", None)
    smart_list = await build_smart_list(items, preferences)
    return {"smart_list": smart_list, "total_items": len(smart_list)}
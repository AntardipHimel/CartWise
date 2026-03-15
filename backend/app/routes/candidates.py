from fastapi import APIRouter
from app.services.candidate_engine import search_autocomplete, get_candidates, build_smart_list

router = APIRouter()


@router.get("/autocomplete/{prefix}")
async def autocomplete(prefix: str, limit: int = 10):
    results = await search_autocomplete(prefix, limit)
    return {"prefix": prefix, "suggestions": results}


@router.get("/candidates/{generic_name}")
async def get_product_candidates(generic_name: str, email: str = None, sort_by: str = "value"):
    result = await get_candidates(generic_name, email, sort_by)
    return result


@router.post("/smart-list")
async def create_smart_list(data: dict):
    items = data.get("items", [])
    email = data.get("email", None)
    smart_list = await build_smart_list(items, email)
    return {"smart_list": smart_list, "total_items": len(smart_list)}
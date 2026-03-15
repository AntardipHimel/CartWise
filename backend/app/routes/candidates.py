import json
import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Optional
from app.services.candidate_engine import search_autocomplete, get_candidates, get_multi_candidates, build_smart_list

router = APIRouter()


@router.get("/autocomplete/{prefix}")
async def autocomplete(prefix: str, limit: int = 10):
    results = await search_autocomplete(prefix, limit)
    return {"prefix": prefix, "suggestions": results}


@router.get("/candidates/{generic_name}")
async def get_product_candidates(
    generic_name: str,
    brand: Optional[str] = None,
    min_size: Optional[float] = None,
    max_size: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "value",
    limit: int = 15,
):
    result = await get_candidates(
        generic_name=generic_name,
        brand=brand,
        min_size=min_size,
        max_size=max_size,
        max_price=max_price,
        sort_by=sort_by,
        limit=limit,
    )
    return result


@router.get("/candidates/{generic_name}/export")
async def export_candidates(
    generic_name: str,
    format: str = "json",
    brand: Optional[str] = None,
    max_price: Optional[float] = None,
    min_size: Optional[float] = None,
):
    result = await get_candidates(
        generic_name=generic_name,
        brand=brand,
        max_price=max_price,
        min_size=min_size,
    )
    candidates = result["candidate_products"]

    if format == "csv":
        output = io.StringIO()
        if candidates:
            writer = csv.DictWriter(output, fieldnames=candidates[0].keys())
            writer.writeheader()
            writer.writerows(candidates)
        content = output.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={generic_name}_candidates.csv"}
        )
    else:
        content = json.dumps({"item": generic_name, "candidate_products": candidates}, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={generic_name}_candidates.json"}
        )


@router.post("/candidates")
async def get_multiple_candidates(data: dict):
    items = data.get("items", [])
    results = await get_multi_candidates(items)
    return results


@router.post("/smart-list")
async def create_smart_list(data: dict):
    items = data.get("items", [])
    email = data.get("email", None)
    smart_list = await build_smart_list(items, email)
    return {"smart_list": smart_list, "total_items": len(smart_list)}
from fastapi import APIRouter
from app.services.data_loader import load_price_entries

router = APIRouter()


@router.get("/products")
async def get_products():
    entries = load_price_entries()
    unique_items = sorted(set(e.item_name for e in entries))
    return {"products": unique_items, "total_entries": len(entries)}

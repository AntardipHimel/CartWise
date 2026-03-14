from fastapi import APIRouter
from app.models.schemas import OptimizeRequest
from app.services.value_scorer import rank_items_by_store
from app.services.route_optimizer import optimize
from app.services.data_loader import load_stores, load_price_entries

router = APIRouter()


@router.post("/optimize")
async def optimize_shopping(request: OptimizeRequest):
    stores = load_stores()
    price_entries = load_price_entries()
    item_names = [item.name for item in request.items]
    rankings = rank_items_by_store(item_names, price_entries, stores)
    result = optimize(
        item_store_rankings=rankings,
        stores=stores,
        user_lat=request.user_lat,
        user_lng=request.user_lng,
        gas_price=request.gas_price_per_gallon,
        mpg=request.vehicle_mpg,
        convenience_weight=request.convenience_weight,
    )
    return {
        "single_store_plan": result["single_store_plan"],
        "multi_store_plan": result["multi_store_plan"],
        "recommended": result["recommended"],
        "recommendation_reason": result["recommendation_reason"],
        "item_rankings": rankings,
    }

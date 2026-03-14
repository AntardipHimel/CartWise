from fastapi import APIRouter
from app.models.schemas import OptimizeRequest, Store
from app.services.value_scorer import rank_items_by_store
from app.services.route_optimizer import optimize
from app.services.data_loader import load_stores, load_price_entries
from app.services.candidate_engine import build_smart_list
from app.models.schemas import PriceEntry

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


@router.post("/optimize-smart")
async def optimize_smart(data: dict):
    """
    Smart optimization using real candidate data from store APIs.
    Takes generic item names, fetches real prices, then optimizes.
    """
    item_names = data.get("items", [])
    user_lat = data.get("user_lat", 37.45)
    user_lng = data.get("user_lng", -122.15)
    convenience_weight = data.get("convenience_weight", 0.5)
    gas_price = data.get("gas_price_per_gallon", 3.50)
    mpg = data.get("vehicle_mpg", 25.0)
    preferences = data.get("preferences", {})

    smart_list = await build_smart_list(item_names, preferences)

    price_entries = []
    store_set = {}

    for item in smart_list:
        selected = item["selected"]
        all_options = [selected] + item.get("alternatives", [])

        for opt in all_options:
            price_entries.append(PriceEntry(
                item_name=item["item_name"],
                store_id=opt["store_id"],
                price=opt["price"],
                unit_size=opt["unit_size"],
                unit_type=opt["unit_type"],
                brand=opt["brand"],
                on_sale=False,
            ))

            if opt["store_id"] not in store_set:
                store_set[opt["store_id"]] = Store(
                    id=opt["store_id"],
                    name=opt["store_name"],
                    latitude=user_lat + (hash(opt["store_id"]) % 100) * 0.001,
                    longitude=user_lng + (hash(opt["store_id"]) % 50) * 0.001,
                    rating=4.0,
                )

    stores = list(store_set.values())
    rankings = rank_items_by_store(
        [item["item_name"] for item in smart_list],
        price_entries,
        stores,
    )

    result = optimize(
        item_store_rankings=rankings,
        stores=stores,
        user_lat=user_lat,
        user_lng=user_lng,
        gas_price=gas_price,
        mpg=mpg,
        convenience_weight=convenience_weight,
    )

    return {
        "single_store_plan": result["single_store_plan"],
        "multi_store_plan": result["multi_store_plan"],
        "recommended": result["recommended"],
        "recommendation_reason": result["recommendation_reason"],
        "smart_list": smart_list,
        "item_rankings": rankings,
    }
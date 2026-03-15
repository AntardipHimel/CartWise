from fastapi import APIRouter
from app.models.schemas import OptimizeRequest, Store, PriceEntry
from app.services.value_scorer import rank_items_by_store
from app.services.route_optimizer import optimize
from app.services.candidate_engine import build_smart_list
from app.db import get_db

router = APIRouter()


@router.post("/optimize")
async def optimize_shopping(request: OptimizeRequest):
    from app.services.data_loader import load_stores, load_price_entries
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
    db = get_db()
    item_names = data.get("items", [])
    user_email = data.get("email", None)
    convenience_weight = data.get("convenience_weight", 0.5)
    gas_price = data.get("gas_price_per_gallon", 3.50)
    mpg = data.get("vehicle_mpg", 25.0)

    user_lat = data.get("user_lat", 37.45)
    user_lng = data.get("user_lng", -122.15)

    if user_email:
        user = await db.users.find_one({"email": user_email})
        if user:
            user_lat = user.get("latitude", user_lat)
            user_lng = user.get("longitude", user_lng)
            gas_price = user.get("gas_price", gas_price)
            mpg = user.get("vehicle_mpg", mpg)

    smart_list = await build_smart_list(item_names, user_email)

    price_entries = []
    store_set = {}

    for item in smart_list:
        all_options = [item["selected"]] + item.get("alternatives", [])
        for opt in all_options:
            price_entries.append(PriceEntry(
                item_name=item["item_name"],
                store_id=opt["store_id"],
                price=opt["price"],
                unit_size=opt["unit_size"],
                unit_type=opt["unit_type"],
                brand=opt.get("brand", ""),
                on_sale=False,
            ))

            if opt["store_id"] not in store_set:
                store_doc = await db.stores.find_one({"store_id": opt["store_id"]})
                if store_doc:
                    store_set[opt["store_id"]] = Store(
                        id=store_doc["store_id"],
                        name=store_doc["name"],
                        latitude=store_doc["latitude"],
                        longitude=store_doc["longitude"],
                        rating=store_doc.get("rating", 4.0),
                        address=store_doc.get("address", ""),
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
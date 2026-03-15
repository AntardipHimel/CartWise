from fastapi import APIRouter

from app.models.schemas import OptimizeRequest, OptimizeResponse
from app.services.candidate_engine import build_candidate_bundles
from app.services.route_optimizer import optimize_categories

router = APIRouter()


@router.post("/optimize-smart", response_model=OptimizeResponse)
async def optimize_smart(payload: OptimizeRequest):
    candidate_bundles, nearby_stores = await build_candidate_bundles(
        items=payload.items,
        start_lat=payload.start_lat,
        start_lng=payload.start_lng,
        max_radius_miles=payload.max_radius_miles,
        candidate_limit_per_item=payload.candidate_limit_per_item,
    )

    categories, recommended_category, recommendation_reason = optimize_categories(
        candidate_bundles=candidate_bundles,
        stores=nearby_stores,
        start_lat=payload.start_lat,
        start_lng=payload.start_lng,
        end_lat=payload.end_lat,
        end_lng=payload.end_lng,
        trip_start_time=payload.trip_start_time,
        max_store_count=payload.max_store_count,
        vehicle_mpg=payload.vehicle_mpg,
        gas_price_per_gallon=payload.gas_price_per_gallon,
        minimum_multi_store_savings=payload.minimum_multi_store_savings,
    )

    return OptimizeResponse(
        recommended_category=recommended_category,
        recommendation_reason=recommendation_reason,
        request_context={
            "start": {"lat": payload.start_lat, "lng": payload.start_lng},
            "end": {"lat": payload.end_lat, "lng": payload.end_lng},
            "trip_start_time": payload.trip_start_time,
            "max_radius_miles": payload.max_radius_miles,
            "max_store_count": payload.max_store_count,
            "vehicle_mpg": payload.vehicle_mpg,
            "gas_price_per_gallon": payload.gas_price_per_gallon,
            "candidate_limit_per_item": payload.candidate_limit_per_item,
            "minimum_multi_store_savings": payload.minimum_multi_store_savings,
            "nearby_store_count": len(nearby_stores),
            "item_count": len(payload.items),
        },
        categories=categories,
    )
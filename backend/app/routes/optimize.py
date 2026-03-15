from fastapi import APIRouter

from app.models.schemas import OptimizeRequest, OptimizeResponse
from app.services.candidate_engine import build_candidate_bundles
from app.services.route_optimizer import optimize_categories, find_top_n_plans, choose_balanced

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


@router.post("/optimize-smart-ranked")
async def optimize_smart_ranked(payload: OptimizeRequest):
    """
    Returns up to 10 cheapest route plans sorted by total cost,
    plus identifies the Best Balanced route among them.
    """
    candidate_bundles, nearby_stores = await build_candidate_bundles(
        items=payload.items,
        start_lat=payload.start_lat,
        start_lng=payload.start_lng,
        max_radius_miles=payload.max_radius_miles,
        candidate_limit_per_item=payload.candidate_limit_per_item,
    )

    plans = find_top_n_plans(
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
        max_routes=10,
    )

    balanced_index = choose_balanced(plans) if plans else -1

    # Serialize each RouteCategory with a rank label
    routes = []
    for i, plan in enumerate(plans):
        routes.append({
            "rank": i + 1,
            "label": f"Route {i + 1}",
            "is_balanced_pick": i == balanced_index,
            **plan.model_dump(),
        })

    balanced_rank = balanced_index + 1 if plans else 0
    balanced_plan = plans[balanced_index] if plans and balanced_index >= 0 else None

    if balanced_plan and balanced_rank == 1:
        reason = (
            f"Route 1 is both the cheapest and best balanced — "
            f"${balanced_plan.metrics['total_cost']:.2f} total, "
            f"{balanced_plan.metrics['travel_distance_miles']:.1f} mi, "
            f"~{balanced_plan.metrics['travel_time_minutes']:.0f} min."
        )
    elif balanced_plan:
        cheapest_plan = plans[0]
        reason = (
            f"Route {balanced_rank} is the best balanced pick: "
            f"${balanced_plan.metrics['total_cost']:.2f} total / "
            f"{balanced_plan.metrics['travel_distance_miles']:.1f} mi / "
            f"~{balanced_plan.metrics['travel_time_minutes']:.0f} min. "
            f"Route 1 is cheapest at ${cheapest_plan.metrics['total_cost']:.2f} "
            f"but travels {cheapest_plan.metrics['travel_distance_miles']:.1f} mi."
        )
    else:
        reason = "No feasible routes found."

    return {
        "routes": routes,
        "balanced_route_rank": balanced_rank,
        "total_items_requested": len(payload.items),
        "recommendation_reason": reason,
        "request_context": {
            "start": {"lat": payload.start_lat, "lng": payload.start_lng},
            "end": {"lat": payload.end_lat, "lng": payload.end_lng},
            "trip_start_time": payload.trip_start_time,
        },
    }
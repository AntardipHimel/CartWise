import math
from itertools import combinations

from app.models.schemas import CandidateBundle, RouteCategory, SelectedProduct, StoreNode


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def parse_minutes(hhmm: str) -> int:
    parts = hhmm.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def is_store_open(store: StoreNode, trip_start_time: str) -> bool:
    current = parse_minutes(trip_start_time)
    open_m = parse_minutes(store.open_time)
    close_m = parse_minutes(store.close_time)
    if close_m >= open_m:
        return open_m <= current <= close_m
    return current >= open_m or current <= close_m


def nearest_neighbor_route(
    stores: list[StoreNode],
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
) -> tuple[list[dict], float]:
    """Greedy nearest-neighbor route instead of brute-force permutations."""
    if not stores:
        return (
            [
                {"type": "start", "lat": start_lat, "lon": start_lng},
                {"type": "end", "lat": end_lat, "lon": end_lng},
            ],
            0.0,
        )

    remaining = list(stores)
    ordered = []
    current_lat, current_lng = start_lat, start_lng
    total_distance = 0.0

    while remaining:
        nearest = min(
            remaining,
            key=lambda s: haversine_miles(current_lat, current_lng, s.lat, s.lon),
        )
        dist = haversine_miles(current_lat, current_lng, nearest.lat, nearest.lon)
        total_distance += dist
        current_lat, current_lng = nearest.lat, nearest.lon
        ordered.append(nearest)
        remaining.remove(nearest)

    total_distance += haversine_miles(current_lat, current_lng, end_lat, end_lng)

    route = [{"type": "start", "lat": start_lat, "lon": start_lng}]
    for store in ordered:
        route.append({
            "type": "store",
            "store_id": store.store_id,
            "name": store.name,
            "vendor": store.vendor,
            "lat": store.lat,
            "lon": store.lon,
            "open_time": store.open_time,
            "close_time": store.close_time,
        })
    route.append({"type": "end", "lat": end_lat, "lon": end_lng})

    road_distance = round(total_distance * 1.18, 2)
    return route, road_distance


def prefilter_relevant_stores(
    candidate_bundles: list[CandidateBundle],
    stores: list[StoreNode],
    trip_start_time: str,
) -> list[StoreNode]:
    """Only keep stores that are open AND have at least one candidate product."""
    candidate_store_ids = set()
    for bundle in candidate_bundles:
        for c in bundle.candidates:
            candidate_store_ids.add(c.store_id)

    return [
        s for s in stores
        if s.store_id in candidate_store_ids and is_store_open(s, trip_start_time)
    ]


def quick_score_combo(
    combo_store_ids: set[str],
    candidate_bundles: list[CandidateBundle],
) -> tuple[float, int]:
    """Fast estimate: total cheapest price + missing count without building full plan."""
    total_price = 0.0
    missing = 0
    for bundle in candidate_bundles:
        valid = [c for c in bundle.candidates if c.store_id in combo_store_ids]
        if valid:
            total_price += min(c.price for c in valid)
        else:
            missing += 1
    return total_price, missing


def build_plan_for_store_subset(
    category: str,
    candidate_bundles: list[CandidateBundle],
    selected_stores: list[StoreNode],
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    vehicle_mpg: float,
    gas_price_per_gallon: float,
) -> RouteCategory:
    selected_store_ids = {store.store_id for store in selected_stores}

    included_products: list[SelectedProduct] = []
    missing_items: list[str] = []

    for bundle in candidate_bundles:
        valid = [c for c in bundle.candidates if c.store_id in selected_store_ids]
        if not valid:
            missing_items.append(bundle.item_key)
            continue

        chosen = min(valid, key=lambda c: (c.price, -c.match_score))
        included_products.append(
            SelectedProduct(
                item_key=bundle.item_key,
                store_id=chosen.store_id,
                product_id=chosen.product_id,
                price=chosen.price,
                match_score=chosen.match_score,
                brand=chosen.brand,
                package_size=chosen.package_size,
                package_unit=chosen.package_unit,
                item_name=chosen.item_name,
                vendor=chosen.vendor,
            )
        )

    active_store_ids = {p.store_id for p in included_products}
    active_stores = [s for s in selected_stores if s.store_id in active_store_ids]

    route, travel_distance_miles = nearest_neighbor_route(
        active_stores, start_lat, start_lng, end_lat, end_lng,
    )

    travel_cost = round((travel_distance_miles / max(vehicle_mpg, 1)) * gas_price_per_gallon, 2)
    visit_penalty = sum(s.visit_penalty_minutes for s in active_stores)
    travel_time_minutes = round((travel_distance_miles / 30.0) * 60.0 + visit_penalty, 1)
    total_item_cost = round(sum(p.price for p in included_products), 2)

    if included_products:
        match_score_avg = round(
            sum(p.match_score for p in included_products) / len(included_products), 3
        )
    else:
        match_score_avg = 0.0

    total_cost = round(total_item_cost + travel_cost, 2)
    coverage_ratio = round(
        len(included_products) / len(candidate_bundles) if candidate_bundles else 0.0, 3
    )

    summary = (
        f"{len(active_stores)} store(s), {len(included_products)} item(s), "
        f"${total_item_cost:.2f} items + ${travel_cost:.2f} gas = ${total_cost:.2f}"
    )

    return RouteCategory(
        category=category,
        summary=summary,
        stores=[
            {
                "store_id": s.store_id,
                "name": s.name,
                "vendor": s.vendor,
                "lat": s.lat,
                "lon": s.lon,
                "open_time": s.open_time,
                "close_time": s.close_time,
                "visit_penalty_minutes": s.visit_penalty_minutes,
            }
            for s in active_stores
        ],
        route=route,
        included_products=included_products,
        missing_items=missing_items,
        metrics={
            "store_count": len(active_stores),
            "items_requested": len(candidate_bundles),
            "items_included": len(included_products),
            "items_missing": len(missing_items),
            "coverage_ratio": coverage_ratio,
            "average_match_score": match_score_avg,
            "total_item_cost": total_item_cost,
            "travel_cost": travel_cost,
            "travel_distance_miles": travel_distance_miles,
            "travel_time_minutes": travel_time_minutes,
            "total_cost": total_cost,
        },
    )


def empty_plan(category: str, candidate_bundles, start_lat, start_lng, end_lat, end_lng):
    return RouteCategory(
        category=category,
        summary=f"No feasible {category} plan found",
        stores=[],
        route=[
            {"type": "start", "lat": start_lat, "lon": start_lng},
            {"type": "end", "lat": end_lat, "lon": end_lng},
        ],
        included_products=[],
        missing_items=[b.item_key for b in candidate_bundles],
        metrics={
            "store_count": 0,
            "items_requested": len(candidate_bundles),
            "items_included": 0,
            "items_missing": len(candidate_bundles),
            "coverage_ratio": 0.0,
            "average_match_score": 0.0,
            "total_item_cost": 0.0,
            "travel_cost": 0.0,
            "travel_distance_miles": 0.0,
            "travel_time_minutes": 0.0,
            "total_cost": 0.0,
        },
    )


def find_best_plan(
    category: str,
    candidate_bundles: list[CandidateBundle],
    stores: list[StoreNode],
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    trip_start_time: str,
    max_store_count: int,
    vehicle_mpg: float,
    gas_price_per_gallon: float,
    optimize_for: str = "cost",
) -> RouteCategory:
    """
    Optimized store combination search.
    Pre-filters stores, uses quick scoring to prune bad combos early.
    """
    relevant = prefilter_relevant_stores(candidate_bundles, stores, trip_start_time)

    if not relevant:
        return empty_plan(category, candidate_bundles, start_lat, start_lng, end_lat, end_lng)

    # Sort by distance from start — closer stores checked first
    relevant.sort(key=lambda s: haversine_miles(start_lat, start_lng, s.lat, s.lon))

    # Limit to top 15 closest relevant stores to keep combos manageable
    relevant = relevant[:15]

    best_plan: RouteCategory | None = None
    best_score = None

    for size in range(1, min(max_store_count, len(relevant)) + 1):
        for combo in combinations(relevant, size):
            combo_ids = {s.store_id for s in combo}

            # Quick pre-check: skip if this combo can't cover more items
            _, missing_count = quick_score_combo(combo_ids, candidate_bundles)
            if best_plan and missing_count > best_plan.metrics["items_missing"]:
                continue

            plan = build_plan_for_store_subset(
                category=category,
                candidate_bundles=candidate_bundles,
                selected_stores=list(combo),
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                vehicle_mpg=vehicle_mpg,
                gas_price_per_gallon=gas_price_per_gallon,
            )

            if optimize_for == "distance":
                score = (
                    plan.metrics["items_missing"],
                    plan.metrics["travel_distance_miles"],
                    plan.metrics["travel_time_minutes"],
                    plan.metrics["total_cost"],
                    plan.metrics["store_count"],
                )
            else:
                score = (
                    plan.metrics["items_missing"],
                    plan.metrics["total_cost"],
                    plan.metrics["travel_distance_miles"],
                    plan.metrics["store_count"],
                )

            if best_plan is None or score < best_score:
                best_plan = plan
                best_score = score

    return best_plan or empty_plan(category, candidate_bundles, start_lat, start_lng, end_lat, end_lng)


def choose_recommended_category(
    cheapest: RouteCategory,
    shortest: RouteCategory,
    minimum_multi_store_savings: float,
) -> tuple[str, str]:
    cheapest_total = float(cheapest.metrics["total_cost"])
    shortest_total = float(shortest.metrics["total_cost"])

    if cheapest.metrics["items_missing"] < shortest.metrics["items_missing"]:
        return "cheapest", "Cheapest route covers more requested items within the selected radius and store hours."

    if shortest.metrics["items_missing"] < cheapest.metrics["items_missing"]:
        return "shortest", "Shortest route covers more requested items within the selected radius and store hours."

    if cheapest_total + minimum_multi_store_savings < shortest_total:
        savings = round(shortest_total - cheapest_total, 2)
        return "cheapest", f"Cheapest route saves ${savings:.2f} overall after gas."

    return "shortest", "Shortest route is the better choice because extra travel does not save enough money."


def optimize_categories(
    candidate_bundles: list[CandidateBundle],
    stores: list[StoreNode],
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    trip_start_time: str,
    max_store_count: int,
    vehicle_mpg: float,
    gas_price_per_gallon: float,
    minimum_multi_store_savings: float,
) -> tuple[dict[str, RouteCategory], str, str]:
    cheapest = find_best_plan(
        category="cheapest",
        candidate_bundles=candidate_bundles,
        stores=stores,
        start_lat=start_lat,
        start_lng=start_lng,
        end_lat=end_lat,
        end_lng=end_lng,
        trip_start_time=trip_start_time,
        max_store_count=max_store_count,
        vehicle_mpg=vehicle_mpg,
        gas_price_per_gallon=gas_price_per_gallon,
        optimize_for="cost",
    )

    shortest = find_best_plan(
        category="shortest",
        candidate_bundles=candidate_bundles,
        stores=stores,
        start_lat=start_lat,
        start_lng=start_lng,
        end_lat=end_lat,
        end_lng=end_lng,
        trip_start_time=trip_start_time,
        max_store_count=max_store_count,
        vehicle_mpg=vehicle_mpg,
        gas_price_per_gallon=gas_price_per_gallon,
        optimize_for="distance",
    )

    recommended_category, recommendation_reason = choose_recommended_category(
        cheapest=cheapest,
        shortest=shortest,
        minimum_multi_store_savings=minimum_multi_store_savings,
    )

    return {
        "cheapest": cheapest,
        "shortest": shortest,
    }, recommended_category, recommendation_reason
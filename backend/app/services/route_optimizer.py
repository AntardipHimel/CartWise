import math
from itertools import combinations, permutations

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
    hour = int(parts[0])
    minute = int(parts[1])
    return hour * 60 + minute


def is_store_open(store: StoreNode, trip_start_time: str) -> bool:
    current = parse_minutes(trip_start_time)
    open_minutes = parse_minutes(store.open_time)
    close_minutes = parse_minutes(store.close_time)

    if close_minutes >= open_minutes:
        return open_minutes <= current <= close_minutes

    return current >= open_minutes or current <= close_minutes


def compute_best_route(
    stores: list[StoreNode],
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
) -> tuple[list[dict], float]:
    if not stores:
        return (
            [
                {"type": "start", "lat": start_lat, "lon": start_lng},
                {"type": "end", "lat": end_lat, "lon": end_lng},
            ],
            0.0,
        )

    best_distance = float("inf")
    best_order: list[StoreNode] = []

    for order in permutations(stores):
        total = 0.0
        current_lat = start_lat
        current_lng = start_lng

        for store in order:
            total += haversine_miles(current_lat, current_lng, store.lat, store.lon)
            current_lat = store.lat
            current_lng = store.lon

        total += haversine_miles(current_lat, current_lng, end_lat, end_lng)

        if total < best_distance:
            best_distance = total
            best_order = list(order)

    route = [{"type": "start", "lat": start_lat, "lon": start_lng}]
    for store in best_order:
        route.append(
            {
                "type": "store",
                "store_id": store.store_id,
                "name": store.name,
                "vendor": store.vendor,
                "lat": store.lat,
                "lon": store.lon,
                "open_time": store.open_time,
                "close_time": store.close_time,
            }
        )
    route.append({"type": "end", "lat": end_lat, "lon": end_lng})

    road_distance = round(best_distance * 1.18, 2)
    return route, road_distance


def build_plan_for_store_subset(
    category: str,
    candidate_bundles: list[CandidateBundle],
    selected_stores: list[StoreNode],
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    trip_start_time: str,
    vehicle_mpg: float,
    gas_price_per_gallon: float,
) -> RouteCategory:
    open_stores = [store for store in selected_stores if is_store_open(store, trip_start_time)]
    selected_store_ids = {store.store_id for store in open_stores}

    included_products: list[SelectedProduct] = []
    missing_items: list[str] = []

    for bundle in candidate_bundles:
        valid = [candidate for candidate in bundle.candidates if candidate.store_id in selected_store_ids]
        if not valid:
            missing_items.append(bundle.item_key)
            continue

        chosen = min(valid, key=lambda candidate: (candidate.price, -candidate.match_score))

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

    active_store_ids = {product.store_id for product in included_products}
    active_stores = [store for store in open_stores if store.store_id in active_store_ids]

    route, travel_distance_miles = compute_best_route(
        active_stores,
        start_lat,
        start_lng,
        end_lat,
        end_lng,
    )

    travel_cost = round((travel_distance_miles / max(vehicle_mpg, 1)) * gas_price_per_gallon, 2)
    visit_penalty_minutes = sum(store.visit_penalty_minutes for store in active_stores)
    travel_time_minutes = round((travel_distance_miles / 30.0) * 60.0 + visit_penalty_minutes, 1)
    total_item_cost = round(sum(product.price for product in included_products), 2)
    match_score_avg = round(
        sum(product.match_score for product in included_products) / len(included_products), 3
        if included_products
        else 0.0,
        3,
    )
    total_cost = round(total_item_cost + travel_cost, 2)
    coverage_ratio = round(
        len(included_products) / len(candidate_bundles) if candidate_bundles else 0.0,
        3,
    )

    summary = (
        f"{len(active_stores)} open store(s), {len(included_products)} item(s), "
        f"${total_item_cost:.2f} items, ${travel_cost:.2f} gas"
    )

    return RouteCategory(
        category=category,
        summary=summary,
        stores=[
            {
                "store_id": store.store_id,
                "name": store.name,
                "vendor": store.vendor,
                "lat": store.lat,
                "lon": store.lon,
                "open_time": store.open_time,
                "close_time": store.close_time,
                "visit_penalty_minutes": store.visit_penalty_minutes,
            }
            for store in active_stores
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


def find_best_cheapest_plan(
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
) -> RouteCategory:
    best_plan: RouteCategory | None = None
    best_score = None

    for size in range(1, min(max_store_count, len(stores)) + 1):
        for combo in combinations(stores, size):
            plan = build_plan_for_store_subset(
                category="cheapest",
                candidate_bundles=candidate_bundles,
                selected_stores=list(combo),
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                trip_start_time=trip_start_time,
                vehicle_mpg=vehicle_mpg,
                gas_price_per_gallon=gas_price_per_gallon,
            )

            score = (
                plan.metrics["items_missing"],
                plan.metrics["total_cost"],
                plan.metrics["travel_distance_miles"],
                plan.metrics["store_count"],
            )

            if best_plan is None or score < best_score:
                best_plan = plan
                best_score = score

    return best_plan or RouteCategory(
        category="cheapest",
        summary="No feasible cheapest plan found",
        stores=[],
        route=[
            {"type": "start", "lat": start_lat, "lon": start_lng},
            {"type": "end", "lat": end_lat, "lon": end_lng},
        ],
        included_products=[],
        missing_items=[bundle.item_key for bundle in candidate_bundles],
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


def find_best_shortest_plan(
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
) -> RouteCategory:
    best_plan: RouteCategory | None = None
    best_score = None

    for size in range(1, min(max_store_count, len(stores)) + 1):
        for combo in combinations(stores, size):
            plan = build_plan_for_store_subset(
                category="shortest",
                candidate_bundles=candidate_bundles,
                selected_stores=list(combo),
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                trip_start_time=trip_start_time,
                vehicle_mpg=vehicle_mpg,
                gas_price_per_gallon=gas_price_per_gallon,
            )

            score = (
                plan.metrics["items_missing"],
                plan.metrics["travel_distance_miles"],
                plan.metrics["travel_time_minutes"],
                plan.metrics["total_cost"],
                plan.metrics["store_count"],
            )

            if best_plan is None or score < best_score:
                best_plan = plan
                best_score = score

    return best_plan or RouteCategory(
        category="shortest",
        summary="No feasible shortest plan found",
        stores=[],
        route=[
            {"type": "start", "lat": start_lat, "lon": start_lng},
            {"type": "end", "lat": end_lat, "lon": end_lng},
        ],
        included_products=[],
        missing_items=[bundle.item_key for bundle in candidate_bundles],
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
    cheapest = find_best_cheapest_plan(
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
    )

    shortest = find_best_shortest_plan(
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
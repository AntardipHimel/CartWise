import math
from itertools import combinations
from app.models.schemas import Store, StorePlan


def haversine_miles(lat1, lng1, lat2, lng2):
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def estimate_travel(user_lat, user_lng, stores, gas_price=3.50, mpg=25.0):
    if not stores:
        return {"distance_miles": 0, "cost": 0, "time_minutes": 0}
    visited = []
    remaining = list(stores)
    current_lat, current_lng = user_lat, user_lng
    total_distance = 0
    while remaining:
        nearest = min(remaining, key=lambda s: haversine_miles(current_lat, current_lng, s.latitude, s.longitude))
        dist = haversine_miles(current_lat, current_lng, nearest.latitude, nearest.longitude)
        total_distance += dist
        current_lat, current_lng = nearest.latitude, nearest.longitude
        visited.append(nearest)
        remaining.remove(nearest)
    total_distance += haversine_miles(current_lat, current_lng, user_lat, user_lng)
    road_distance = total_distance * 1.3
    gas_cost = (road_distance / mpg) * gas_price
    time_minutes = (road_distance * 2) + (len(stores) * 5)
    return {"distance_miles": round(road_distance, 1), "cost": round(gas_cost, 2), "time_minutes": round(time_minutes, 0)}


def find_best_single_store(item_store_rankings, stores, user_lat, user_lng, gas_price, mpg):
    best_plan = None
    best_total = float("inf")
    for store in stores:
        total_item_cost = 0
        items_available = []
        for item_name, rankings in item_store_rankings.items():
            store_entry = next((r for r in rankings if r["store_id"] == store.id), None)
            if store_entry:
                total_item_cost += store_entry["price"]
                items_available.append(item_name)
            else:
                total_item_cost += 999
        travel = estimate_travel(user_lat, user_lng, [store], gas_price, mpg)
        total_cost = total_item_cost + travel["cost"]
        if total_cost < best_total:
            best_total = total_cost
            best_plan = StorePlan(
                stores=[store], items_per_store={store.id: items_available},
                total_item_cost=round(total_item_cost, 2), travel_cost=travel["cost"],
                travel_time_minutes=travel["time_minutes"], travel_distance_miles=travel["distance_miles"],
                net_savings=0)
    return best_plan


def find_best_multi_store(item_store_rankings, stores, user_lat, user_lng, gas_price, mpg, max_stores=3):
    best_plan = None
    best_total = float("inf")
    for num_stores in range(2, min(max_stores + 1, len(stores) + 1)):
        for combo in combinations(stores, num_stores):
            combo_ids = {s.id for s in combo}
            total_item_cost = 0
            items_per_store = {s.id: [] for s in combo}
            for item_name, rankings in item_store_rankings.items():
                best_entry = next((r for r in rankings if r["store_id"] in combo_ids), None)
                if best_entry:
                    total_item_cost += best_entry["price"]
                    items_per_store[best_entry["store_id"]].append(item_name)
                else:
                    total_item_cost += 999
            active_stores = [s for s in combo if items_per_store[s.id]]
            if len(active_stores) < 2:
                continue
            travel = estimate_travel(user_lat, user_lng, active_stores, gas_price, mpg)
            total_cost = total_item_cost + travel["cost"]
            if total_cost < best_total:
                best_total = total_cost
                best_plan = StorePlan(
                    stores=active_stores,
                    items_per_store={sid: items for sid, items in items_per_store.items() if items},
                    total_item_cost=round(total_item_cost, 2), travel_cost=travel["cost"],
                    travel_time_minutes=travel["time_minutes"], travel_distance_miles=travel["distance_miles"],
                    net_savings=0)
    return best_plan


def optimize(item_store_rankings, stores, user_lat, user_lng, gas_price=3.50, mpg=25.0, convenience_weight=0.5):
    single = find_best_single_store(item_store_rankings, stores, user_lat, user_lng, gas_price, mpg)
    multi = find_best_multi_store(item_store_rankings, stores, user_lat, user_lng, gas_price, mpg)
    if not multi:
        multi = single
    single_total = single.total_item_cost + single.travel_cost
    multi_total = multi.total_item_cost + multi.travel_cost
    single.net_savings = round(multi_total - single_total, 2)
    multi.net_savings = round(single_total - multi_total, 2)
    time_penalty = ((multi.travel_time_minutes - single.travel_time_minutes) * convenience_weight * 0.50)
    adjusted_multi_total = multi_total + time_penalty
    if adjusted_multi_total < single_total:
        recommended = "multi"
        savings = round(single_total - multi_total, 2)
        reason = f"Visiting {len(multi.stores)} stores saves you ${savings:.2f} after gas costs."
    else:
        recommended = "single"
        reason = f"One-stop at {single.stores[0].name} is your best bet. Multi-store savings don't justify the extra driving."
    return {"single_store_plan": single, "multi_store_plan": multi, "recommended": recommended, "recommendation_reason": reason}

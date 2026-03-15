from collections import Counter
from datetime import datetime, timedelta

from app.db import get_db


async def save_trip(user_email: str, trip_data: dict):
    db = get_db()
    user = await db.users.find_one({"email": user_email})
    if not user:
        return {"error": "User not found"}

    user_id = str(user["_id"])

    trip = {
        "user_id": user_id,
        "trip_date": datetime.utcnow(),
        "plan_chosen": trip_data.get("plan_chosen", trip_data.get("category", "cheapest")),
        "items_purchased": trip_data.get("items_purchased", []),
        "stores_visited": trip_data.get("stores_visited", []),
        "route_taken": trip_data.get("route_taken", {}),
        "total_spent": trip_data.get("total_spent", 0),
        "total_saved": trip_data.get("total_saved", 0),
        "saved_at": trip_data.get("saved_at"),
    }

    await db.shopping_trips.insert_one(trip)
    await db.users.update_one(
        {"email": user_email},
        {"$set": {"last_active": datetime.utcnow()}},
    )

    return {"message": "Trip saved", "items_tracked": len(trip["items_purchased"])}


async def get_smart_recommendations(user_email: str):
    db = get_db()
    user = await db.users.find_one({"email": user_email})
    if not user:
        return {"error": "User not found"}

    user_id = str(user["_id"])
    trips = await db.shopping_trips.find({"user_id": user_id}).sort("trip_date", -1).to_list(20)

    item_counter = Counter()
    recent_item_counter = Counter()

    for trip in trips:
        items = trip.get("items_purchased", [])
        for item in items:
            key = item.get("item_key") or item.get("query")
            if key:
                item_counter[str(key).lower()] += 1

        trip_date = trip.get("trip_date")
        if isinstance(trip_date, datetime) and trip_date >= datetime.utcnow() - timedelta(days=14):
            for item in items:
                key = item.get("item_key") or item.get("query")
                if key:
                    recent_item_counter[str(key).lower()] += 1

    regular_list = [
        {"item": key, "count": count}
        for key, count in item_counter.most_common(10)
    ]

    restock_soon = [
        {"item": key, "count": count}
        for key, count in recent_item_counter.most_common(5)
    ]

    return {
        "restock_soon": restock_soon,
        "price_alerts": [],
        "regular_list": regular_list,
        "total_patterns": len(regular_list),
    }
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
        "plan_chosen": trip_data.get("plan_chosen", "single"),
        "items_purchased": trip_data.get("items_purchased", []),
        "stores_visited": trip_data.get("stores_visited", []),
        "route_taken": trip_data.get("route_taken", {}),
        "total_spent": trip_data.get("total_spent", 0),
        "total_saved": trip_data.get("total_saved", 0),
    }
    await db.shopping_trips.insert_one(trip)

    for item in trip_data.get("items_purchased", []):
        await update_item_pattern(db, user_id, item)
        await update_price_history(db, item)

    await update_user_regulars(db, user_email, trip_data.get("items_purchased", []))

    return {"message": "Trip saved and patterns updated", "items_tracked": len(trip["items_purchased"])}


async def update_item_pattern(db, user_id: str, item: dict):
    query = item.get("query", "").lower()
    if not query:
        return

    existing = await db.item_patterns.find_one({
        "user_id": user_id,
        "item_query": query,
    })

    if existing:
        count = existing.get("purchase_count", 0) + 1
        old_avg = existing.get("avg_price_paid", 0)
        new_avg = ((old_avg * (count - 1)) + item.get("price", 0)) / count

        days_since = (datetime.utcnow() - existing.get("last_purchased", datetime.utcnow())).days
        old_avg_days = existing.get("avg_days_between", 0)
        if old_avg_days > 0 and days_since > 0:
            new_avg_days = ((old_avg_days * (count - 2)) + days_since) / (count - 1) if count > 1 else days_since
        else:
            new_avg_days = days_since if days_since > 0 else 14

        next_expected = datetime.utcnow() + timedelta(days=new_avg_days)

        await db.item_patterns.update_one(
            {"user_id": user_id, "item_query": query},
            {"$set": {
                "preferred_brand": item.get("brand", existing.get("preferred_brand", "")),
                "preferred_size": f"{item.get('unit_size', '')}{item.get('unit_type', '')}",
                "preferred_store": item.get("store_id", existing.get("preferred_store", "")),
                "avg_price_paid": round(new_avg, 2),
                "purchase_count": count,
                "avg_days_between": round(new_avg_days, 1),
                "last_purchased": datetime.utcnow(),
                "next_expected": next_expected,
            }}
        )
    else:
        await db.item_patterns.insert_one({
            "user_id": user_id,
            "item_query": query,
            "preferred_brand": item.get("brand", ""),
            "preferred_size": f"{item.get('unit_size', '')}{item.get('unit_type', '')}",
            "preferred_store": item.get("store_id", ""),
            "avg_price_paid": item.get("price", 0),
            "purchase_count": 1,
            "avg_days_between": 14,
            "last_purchased": datetime.utcnow(),
            "next_expected": datetime.utcnow() + timedelta(days=14),
        })


async def update_price_history(db, item: dict):
    product_name = item.get("product_name", "")
    store_id = item.get("store_id", "")
    price = item.get("price", 0)

    if not product_name or not store_id or price <= 0:
        return

    existing = await db.price_history.find_one({
        "product_name": product_name,
        "store_id": store_id,
    })

    new_entry = {"price": price, "date": datetime.utcnow()}

    if existing:
        prices = existing.get("prices", [])
        prices.append(new_entry)
        prices = prices[-20:]

        price_values = [p["price"] for p in prices]
        avg_price = round(sum(price_values) / len(price_values), 2)
        lowest = round(min(price_values), 2)

        if len(price_values) >= 3:
            recent = price_values[-3:]
            if recent[-1] < recent[0]:
                trend = "dropping"
            elif recent[-1] > recent[0]:
                trend = "rising"
            else:
                trend = "stable"
        else:
            trend = "stable"

        await db.price_history.update_one(
            {"product_name": product_name, "store_id": store_id},
            {"$set": {
                "prices": [{"price": p["price"], "date": p["date"]} for p in prices],
                "trend": trend,
                "lowest_seen": lowest,
                "avg_price": avg_price,
            }}
        )
    else:
        await db.price_history.insert_one({
            "product_name": product_name,
            "store_id": store_id,
            "prices": [new_entry],
            "trend": "stable",
            "lowest_seen": price,
            "avg_price": price,
        })


async def update_user_regulars(db, email: str, items: list):
    user = await db.users.find_one({"email": email})
    if not user:
        return

    user_id = str(user["_id"])
    regulars = user.get("regular_items", [])

    patterns = await db.item_patterns.find({
        "user_id": user_id,
        "purchase_count": {"$gte": 3}
    }).to_list(50)

    for pattern in patterns:
        item = pattern.get("item_query", "")
        if item and item not in regulars:
            regulars.append(item)

    await db.users.update_one(
        {"email": email},
        {"$set": {"regular_items": regulars, "last_active": datetime.utcnow()}}
    )


async def get_smart_recommendations(user_email: str):
    db = get_db()
    user = await db.users.find_one({"email": user_email})
    if not user:
        return {"error": "User not found"}

    user_id = str(user["_id"])
    patterns = await db.item_patterns.find({"user_id": user_id}).to_list(50)

    restock_soon = []
    price_alerts = []
    regular_list = []

    for pattern in patterns:
        item_query = pattern.get("item_query", "")
        next_expected = pattern.get("next_expected")
        avg_price = pattern.get("avg_price_paid", 0)

        if next_expected and next_expected <= datetime.utcnow() + timedelta(days=3):
            restock_soon.append({
                "item": item_query,
                "last_purchased": str(pattern.get("last_purchased")),
                "avg_days_between": pattern.get("avg_days_between"),
                "preferred_brand": pattern.get("preferred_brand"),
                "preferred_store": pattern.get("preferred_store"),
            })

        price_record = await db.price_history.find_one({
            "store_id": pattern.get("preferred_store", ""),
            "product_name": {"$regex": item_query, "$options": "i"},
        })

        if price_record:
            current_prices = price_record.get("prices", [])
            if current_prices:
                latest_price = current_prices[-1]["price"]
                if latest_price < avg_price * 0.85:
                    price_alerts.append({
                        "item": item_query,
                        "product_name": price_record.get("product_name"),
                        "store_id": price_record.get("store_id"),
                        "current_price": latest_price,
                        "avg_price": avg_price,
                        "savings_pct": round((1 - latest_price / avg_price) * 100, 1),
                        "trend": price_record.get("trend"),
                    })

        if pattern.get("purchase_count", 0) >= 2:
            regular_list.append({
                "item": item_query,
                "brand": pattern.get("preferred_brand"),
                "store": pattern.get("preferred_store"),
                "avg_price": avg_price,
                "frequency_days": pattern.get("avg_days_between"),
            })

    return {
        "restock_soon": restock_soon,
        "price_alerts": price_alerts,
        "regular_list": regular_list,
        "total_patterns": len(patterns),
    }
from fastapi import APIRouter
from datetime import datetime
from app.db import get_db
from app.models.documents import UserProfile, ShoppingTrip

router = APIRouter()


@router.post("/users")
async def create_user(data: dict):
    db = get_db()
    user = UserProfile(
        username=data.get("username", ""),
        email=data.get("email", ""),
        zip_code=data.get("zip_code", ""),
        preferred_stores=data.get("preferred_stores", []),
        regular_items=data.get("regular_items", []),
        brand_preferences=data.get("brand_preferences", {}),
        vehicle_mpg=data.get("vehicle_mpg", 25.0),
    )
    result = await db.users.insert_one(user.model_dump())
    return {"user_id": str(result.inserted_id), "message": "Profile created"}


@router.get("/users/{email}")
async def get_user(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User not found"}
    user["_id"] = str(user["_id"])
    return user


@router.put("/users/{email}/regulars")
async def update_regular_items(email: str, data: dict):
    db = get_db()
    items = data.get("regular_items", [])
    await db.users.update_one(
        {"email": email},
        {"$set": {"regular_items": items, "last_active": datetime.utcnow()}}
    )
    return {"message": "Regular items updated", "regular_items": items}


@router.put("/users/{email}/preferences")
async def update_brand_preferences(email: str, data: dict):
    db = get_db()
    prefs = data.get("brand_preferences", {})
    await db.users.update_one(
        {"email": email},
        {"$set": {"brand_preferences": prefs, "last_active": datetime.utcnow()}}
    )
    return {"message": "Brand preferences updated", "brand_preferences": prefs}


@router.post("/users/{email}/trips")
async def save_shopping_trip(email: str, data: dict):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User not found"}

    trip = ShoppingTrip(
        user_id=str(user["_id"]),
        items_purchased=data.get("items_purchased", []),
        stores_visited=data.get("stores_visited", []),
        total_spent=data.get("total_spent", 0),
        total_saved=data.get("total_saved", 0),
    )
    await db.shopping_trips.insert_one(trip.model_dump())

    item_names = [item.get("name", "") for item in data.get("items_purchased", [])]
    if item_names:
        existing = user.get("regular_items", [])
        for item in item_names:
            if item not in existing:
                existing.append(item)
        await db.users.update_one(
            {"email": email},
            {"$set": {"regular_items": existing, "last_active": datetime.utcnow()}}
        )

    return {"message": "Trip saved", "items_tracked": len(item_names)}


@router.get("/users/{email}/recommendations")
async def get_recommendations(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User not found"}

    regular_items = user.get("regular_items", [])
    brand_prefs = user.get("brand_preferences", {})

    trips = await db.shopping_trips.find(
        {"user_id": str(user["_id"])}
    ).sort("trip_date", -1).limit(5).to_list(5)

    item_frequency = {}
    for trip in trips:
        for item in trip.get("items_purchased", []):
            name = item.get("name", "")
            if name:
                item_frequency[name] = item_frequency.get(name, 0) + 1

    frequent_items = sorted(item_frequency.items(), key=lambda x: x[1], reverse=True)
    suggested = [item for item, count in frequent_items if count >= 2 and item not in regular_items]

    return {
        "regular_items": regular_items,
        "brand_preferences": brand_prefs,
        "suggested_additions": suggested[:5],
        "recent_trips": len(trips),
        "message": "Based on your shopping history"
    }
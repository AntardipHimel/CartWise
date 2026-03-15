from fastapi import APIRouter
from datetime import datetime
from app.db import get_db
from app.models.documents import User
from app.services.trip_tracker import save_trip, get_smart_recommendations

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
    """
    Save a completed trip. This triggers:
    - Item pattern updates (frequency, brand, store preference)
    - Price history tracking (trends, alerts)
    - Auto-learn regular items (3+ purchases = regular)
    """
    result = await save_trip(email, data)
    return result


@router.get("/users/{email}/recommendations")
async def get_recommendations(email: str):
    """
    Smart recommendations based on purchase history:
    - Items due for restock soon
    - Price drops on items you buy
    - Your regular shopping list with patterns
    """
    result = await get_smart_recommendations(email)
    return result
from fastapi import APIRouter
from app.db import get_db
from app.models.documents import User
from app.services.trip_tracker import save_trip, get_smart_recommendations

router = APIRouter()


@router.post("/users")
async def create_user(data: dict):
    db = get_db()
    existing = await db.users.find_one({"email": data.get("email", "")})
    if existing:
        return {"error": "User already exists", "user_id": str(existing["_id"])}

    user = User(
        name=data.get("name", ""),
        email=data.get("email", ""),
        password_hash=data.get("password", ""),
        zip_code=data.get("zip_code", ""),
        latitude=data.get("latitude", 0.0),
        longitude=data.get("longitude", 0.0),
        max_drive_miles=data.get("max_drive_miles", 15.0),
        vehicle_mpg=data.get("vehicle_mpg", 25.0),
        gas_price=data.get("gas_price", 3.50),
        brand_preferences=data.get("brand_preferences", {}),
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


@router.put("/users/{email}")
async def update_user(email: str, data: dict):
    db = get_db()
    update_fields = {}
    allowed = [
        "name",
        "zip_code",
        "latitude",
        "longitude",
        "max_drive_miles",
        "vehicle_mpg",
        "gas_price",
        "brand_preferences",
    ]

    for key in allowed:
        if key in data:
            update_fields[key] = data[key]

    if not update_fields:
        return {"error": "No valid fields to update"}

    await db.users.update_one({"email": email}, {"$set": update_fields})
    return {"message": "Profile updated", "updated_fields": list(update_fields.keys())}


@router.post("/users/{email}/trips")
async def save_shopping_trip(email: str, data: dict):
    result = await save_trip(email, data)
    return result


@router.get("/users/{email}/recommendations")
async def get_recommendations(email: str):
    result = await get_smart_recommendations(email)
    return result
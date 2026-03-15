from fastapi import APIRouter

from app.db import get_db
from app.models.documents import User
from app.services.trip_tracker import get_smart_recommendations, save_trip

router = APIRouter()


@router.post("/users")
async def create_user(data: dict):
    db = get_db()
    email = data.get("email", "").lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        return {"error": "User already exists", "user_id": str(existing["_id"])}

    user = User(
        name=data.get("name", ""),
        email=email,
        password_hash=data.get("password", ""),
        zip_code=data.get("zip_code", ""),
        latitude=float(data.get("latitude", 0.0)),
        longitude=float(data.get("longitude", 0.0)),
        destination_latitude=float(data.get("destination_latitude", data.get("latitude", 0.0))),
        destination_longitude=float(data.get("destination_longitude", data.get("longitude", 0.0))),
        max_drive_miles=float(data.get("max_drive_miles", 15.0)),
        max_store_count=int(data.get("max_store_count", 3)),
        vehicle_mpg=float(data.get("vehicle_mpg", 25.0)),
        gas_price=float(data.get("gas_price", 3.50)),
        brand_preferences=data.get("brand_preferences", {}),
    )
    result = await db.users.insert_one(user.model_dump())
    return {
        "user_id": str(result.inserted_id),
        "email": user.email,
        "name": user.name,
        "message": "Profile created",
    }


@router.post("/login")
async def login(data: dict):
    db = get_db()
    email = data.get("email", "").lower()
    password = data.get("password", "")

    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "Invalid email or password"}

    if user.get("password_hash", "") != password:
        return {"error": "Invalid email or password"}

    return {
        "message": "Login successful",
        "user": {
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "zip_code": user.get("zip_code", ""),
            "latitude": user.get("latitude", 0.0),
            "longitude": user.get("longitude", 0.0),
            "destination_latitude": user.get("destination_latitude", user.get("latitude", 0.0)),
            "destination_longitude": user.get("destination_longitude", user.get("longitude", 0.0)),
            "max_drive_miles": user.get("max_drive_miles", 15.0),
            "max_store_count": user.get("max_store_count", 3),
            "vehicle_mpg": user.get("vehicle_mpg", 25.0),
            "gas_price": user.get("gas_price", 3.50),
            "brand_preferences": user.get("brand_preferences", {}),
        },
    }


@router.get("/users/{email}")
async def get_user(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email.lower()})
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
        "destination_latitude",
        "destination_longitude",
        "max_drive_miles",
        "max_store_count",
        "vehicle_mpg",
        "gas_price",
        "brand_preferences",
    ]

    for key in allowed:
        if key in data:
            update_fields[key] = data[key]

    if not update_fields:
        return {"error": "No valid fields to update"}

    await db.users.update_one({"email": email.lower()}, {"$set": update_fields})
    return {"message": "Profile updated", "updated_fields": list(update_fields.keys())}


@router.get("/users/{email}/trips")
async def get_user_trips(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        return {"error": "User not found"}

    user_id = str(user["_id"])
    trips = await db.shopping_trips.find({"user_id": user_id}).sort("trip_date", -1).to_list(20)

    normalized = []
    for trip in trips:
        trip["_id"] = str(trip["_id"])
        normalized.append(trip)

    return {"trips": normalized, "total": len(normalized)}


@router.post("/users/{email}/trips")
async def save_shopping_trip(email: str, data: dict):
    return await save_trip(email.lower(), data)


@router.get("/users/{email}/recommendations")
async def get_recommendations(email: str):
    return await get_smart_recommendations(email.lower())
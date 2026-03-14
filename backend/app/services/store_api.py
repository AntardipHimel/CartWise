import httpx
import os
from datetime import datetime, timedelta
from app.db import get_db
from app.models.documents import ProductCandidate, PriceCache


KROGER_BASE_URL = "https://api.kroger.com/v1"
KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID", "")
KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET", "")

kroger_token = None
kroger_token_expires = None


async def get_kroger_token():
    global kroger_token, kroger_token_expires
    if kroger_token and kroger_token_expires and datetime.utcnow() < kroger_token_expires:
        return kroger_token

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.kroger.com/v1/connect/oauth2/token",
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(KROGER_CLIENT_ID, KROGER_CLIENT_SECRET),
        )
        if response.status_code == 200:
            data = response.json()
            kroger_token = data["access_token"]
            kroger_token_expires = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 1800))
            return kroger_token
    return None


async def search_kroger_products(query: str, location_id: str = None, limit: int = 10):
    token = await get_kroger_token()
    if not token:
        return []

    params = {"filter.term": query, "filter.limit": limit}
    if location_id:
        params["filter.locationId"] = location_id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KROGER_BASE_URL}/products",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            params=params,
        )
        if response.status_code != 200:
            return []

        data = response.json()
        candidates = []
        for item in data.get("data", []):
            price = 0.0
            price_info = item.get("items", [{}])[0]
            if price_info.get("price", {}).get("regular"):
                price = price_info["price"]["regular"]

            size_str = price_info.get("size", "1")
            try:
                unit_size = float("".join(c for c in size_str if c.isdigit() or c == ".") or "1")
            except ValueError:
                unit_size = 1.0

            unit_type = "oz"
            size_lower = size_str.lower()
            if "lb" in size_lower:
                unit_type = "lb"
            elif "gal" in size_lower:
                unit_type = "gal"
            elif "fl oz" in size_lower:
                unit_type = "fl_oz"
            elif "ct" in size_lower or "count" in size_lower:
                unit_type = "count"
            elif "ml" in size_lower:
                unit_type = "ml"
            elif "l" in size_lower:
                unit_type = "l"

            image_url = ""
            images = item.get("images", [])
            if images:
                sizes = images[0].get("sizes", [])
                if sizes:
                    image_url = sizes[0].get("url", "")

            candidates.append(ProductCandidate(
                name=item.get("description", query),
                brand=item.get("brand", ""),
                store_id="kroger",
                store_name="Kroger",
                price=price,
                unit_size=unit_size,
                unit_type=unit_type,
                category=item.get("categories", [""])[0] if item.get("categories") else "",
                image_url=image_url,
                upc=item.get("upc", ""),
                in_stock=price_info.get("inventory", {}).get("stockLevel", "") != "TEMPORARILY_OUT_OF_STOCK",
            ))
        return candidates


async def search_walmart_products(query: str, limit: int = 10):
    """
    Walmart product search.
    Using mock data for now - swap with real API when partner access is approved.
    Structure is ready for Blue Cart API or Walmart Affiliate API.
    """
    walmart_mock = {
        "milk": [
            ProductCandidate(name="Great Value Whole Milk", brand="Great Value", store_id="walmart", store_name="Walmart", price=3.48, unit_size=128, unit_type="fl_oz", category="Dairy", in_stock=True),
            ProductCandidate(name="Fairlife Whole Milk", brand="Fairlife", store_id="walmart", store_name="Walmart", price=5.98, unit_size=52, unit_type="fl_oz", category="Dairy", in_stock=True),
        ],
        "eggs": [
            ProductCandidate(name="Great Value Large Eggs", brand="Great Value", store_id="walmart", store_name="Walmart", price=3.12, unit_size=12, unit_type="count", category="Dairy", in_stock=True),
            ProductCandidate(name="Egglands Best Large Eggs", brand="Egglands Best", store_id="walmart", store_name="Walmart", price=4.98, unit_size=12, unit_type="count", category="Dairy", in_stock=True),
        ],
        "bread": [
            ProductCandidate(name="Great Value White Bread", brand="Great Value", store_id="walmart", store_name="Walmart", price=2.48, unit_size=20, unit_type="oz", category="Bakery", in_stock=True),
            ProductCandidate(name="Natures Own Whole Wheat", brand="Natures Own", store_id="walmart", store_name="Walmart", price=4.28, unit_size=20, unit_type="oz", category="Bakery", in_stock=True),
        ],
        "rice": [
            ProductCandidate(name="Great Value Long Grain Rice", brand="Great Value", store_id="walmart", store_name="Walmart", price=3.98, unit_size=5, unit_type="lb", category="Grains", in_stock=True),
            ProductCandidate(name="Mahatma Enriched Rice", brand="Mahatma", store_id="walmart", store_name="Walmart", price=4.47, unit_size=5, unit_type="lb", category="Grains", in_stock=True),
        ],
        "chicken breast": [
            ProductCandidate(name="Great Value Chicken Breast", brand="Great Value", store_id="walmart", store_name="Walmart", price=8.47, unit_size=3, unit_type="lb", category="Meat", in_stock=True),
            ProductCandidate(name="Tyson Chicken Breast", brand="Tyson", store_id="walmart", store_name="Walmart", price=11.98, unit_size=2.5, unit_type="lb", category="Meat", in_stock=True),
        ],
        "olive oil": [
            ProductCandidate(name="Great Value Extra Virgin Olive Oil", brand="Great Value", store_id="walmart", store_name="Walmart", price=5.97, unit_size=17, unit_type="fl_oz", category="Cooking", in_stock=True),
            ProductCandidate(name="Bertolli Extra Virgin Olive Oil", brand="Bertolli", store_id="walmart", store_name="Walmart", price=8.47, unit_size=17, unit_type="fl_oz", category="Cooking", in_stock=True),
        ],
        "pasta": [
            ProductCandidate(name="Great Value Spaghetti", brand="Great Value", store_id="walmart", store_name="Walmart", price=1.28, unit_size=16, unit_type="oz", category="Grains", in_stock=True),
            ProductCandidate(name="Barilla Spaghetti", brand="Barilla", store_id="walmart", store_name="Walmart", price=1.98, unit_size=16, unit_type="oz", category="Grains", in_stock=True),
        ],
        "cereal": [
            ProductCandidate(name="Great Value Toasted Oats", brand="Great Value", store_id="walmart", store_name="Walmart", price=3.98, unit_size=18, unit_type="oz", category="Breakfast", in_stock=True),
            ProductCandidate(name="Cheerios", brand="General Mills", store_id="walmart", store_name="Walmart", price=5.48, unit_size=18, unit_type="oz", category="Breakfast", in_stock=True),
        ],
        "bananas": [
            ProductCandidate(name="Bananas", brand="", store_id="walmart", store_name="Walmart", price=0.62, unit_size=1, unit_type="lb", category="Produce", in_stock=True),
        ],
        "laundry detergent": [
            ProductCandidate(name="Tide Original Detergent", brand="Tide", store_id="walmart", store_name="Walmart", price=11.97, unit_size=92, unit_type="fl_oz", category="Household", in_stock=True),
            ProductCandidate(name="Great Value Detergent", brand="Great Value", store_id="walmart", store_name="Walmart", price=5.97, unit_size=64, unit_type="fl_oz", category="Household", in_stock=True),
        ],
    }

    query_lower = query.lower().strip()
    results = walmart_mock.get(query_lower, [])

    if not results:
        for key, items in walmart_mock.items():
            if query_lower in key or key in query_lower:
                results = items
                break

    return results[:limit]


async def fetch_candidates(query: str, limit: int = 10):
    """
    Fetch product candidates from all store APIs.
    Checks cache first, fetches fresh if expired.
    """
    db = get_db()
    if db is not None:
        cache = await db.price_cache.find_one({
            "item_query": query.lower(),
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if cache:
            return [ProductCandidate(**c) for c in cache["candidates"]]

    kroger_results = await search_kroger_products(query, limit=limit)
    walmart_results = await search_walmart_products(query, limit=limit)

    all_candidates = kroger_results + walmart_results

    if db is not None and all_candidates:
        cache_doc = {
            "item_query": query.lower(),
            "candidates": [c.model_dump() for c in all_candidates],
            "fetched_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=30),
        }
        await db.price_cache.update_one(
            {"item_query": query.lower()},
            {"$set": cache_doc},
            upsert=True,
        )

    return all_candidates
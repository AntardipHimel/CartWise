import httpx
import os
from datetime import datetime, timedelta
from app.db import get_db


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


async def fetch_kroger_and_save(query: str, limit: int = 10):
    token = await get_kroger_token()
    if not token:
        return 0

    params = {"filter.term": query, "filter.limit": limit}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KROGER_BASE_URL}/products",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            params=params,
        )
        if response.status_code != 200:
            return 0

        data = response.json()
        db = get_db()
        count = 0

        for item in data.get("data", []):
            price_info = item.get("items", [{}])[0]
            price = 0.0
            if price_info.get("price", {}).get("regular"):
                price = price_info["price"]["regular"]

            if price <= 0:
                continue

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

            image_url = ""
            images = item.get("images", [])
            if images:
                sizes = images[0].get("sizes", [])
                if sizes:
                    image_url = sizes[0].get("url", "")

            product = {
                "store_id": "kroger-mv-01",
                "product_name": item.get("description", query),
                "generic_name": query.lower(),
                "brand": item.get("brand", ""),
                "price": price,
                "unit_size": unit_size,
                "unit_type": unit_type,
                "category": "",
                "upc": item.get("upc", ""),
                "image_url": image_url,
                "in_stock": price_info.get("inventory", {}).get("stockLevel", "") != "TEMPORARILY_OUT_OF_STOCK",
                "last_updated": datetime.utcnow(),
            }

            await db.products.update_one(
                {"store_id": product["store_id"], "upc": product["upc"]},
                {"$set": product},
                upsert=True,
            )
            count += 1

        return count
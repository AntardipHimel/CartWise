from app.db import get_db
from app.services.value_scorer import normalize_to_standard_unit


async def search_autocomplete(prefix: str, limit: int = 10):
    db = get_db()
    results = await db.products.distinct(
        "generic_name",
        {"generic_name": {"$regex": f"^{prefix.lower()}", "$options": "i"}}
    )
    return results[:limit]


async def get_candidates(
    generic_name: str,
    brand: str = None,
    min_size: float = None,
    max_size: float = None,
    max_price: float = None,
    sort_by: str = "value",
    limit: int = 15,
):
    """
    Get candidates for a single item with optional filters.
    
    Filters:
    - brand: "Kirkland", "Great Value", etc.
    - min_size / max_size: filter by package size
    - max_price: max user wants to spend on this item
    - sort_by: "value" (best deal), "price" (cheapest), "size" (biggest)
    - limit: max results (default 15)
    """
    db = get_db()

    query = {"generic_name": generic_name.lower()}

    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}

    if min_size is not None or max_size is not None:
        size_filter = {}
        if min_size is not None:
            size_filter["$gte"] = min_size
        if max_size is not None:
            size_filter["$lte"] = max_size
        query["unit_size"] = size_filter

    if max_price is not None:
        query["price"] = {"$lte": max_price}

    products = await db.products.find(query).to_list(100)

    if not products:
        return {
            "item": generic_name,
            "filters_applied": {
                "brand": brand,
                "min_size": min_size,
                "max_size": max_size,
                "max_price": max_price,
            },
            "candidate_products": [],
            "best_value": None,
            "cheapest": None,
            "total_found": 0,
        }

    candidates = []
    for p in products:
        price = p.get("price", 0)
        if price <= 0:
            continue

        unit_size = p.get("unit_size", 1)
        unit_type = p.get("unit_type", "oz")
        unit_price = round(price / unit_size, 2) if unit_size > 0 else 0

        store = await db.stores.find_one({"store_id": p.get("store_id")})
        store_name = store.get("name", "") if store else ""
        store_rating = store.get("rating", 4.0) if store else 4.0

        standard_qty = normalize_to_standard_unit(unit_size, unit_type)
        rating_weight = 0.8 + (store_rating / 5.0) * 0.4
        in_stock = p.get("in_stock", True)
        stock_penalty = 1.0 if in_stock else 0.3
        value_score = round((standard_qty / price) * rating_weight * stock_penalty, 4)

        candidates.append({
            "store_id": p.get("store_id", ""),
            "store_name": store_name,
            "product_id": str(p.get("_id", "")),
            "product_name": p.get("product_name", ""),
            "brand": p.get("brand", ""),
            "price": price,
            "size": f"{unit_size} {unit_type}",
            "unit_size": unit_size,
            "unit_type": unit_type,
            "unit_price": unit_price,
            "unit_price_label": f"${unit_price}/{unit_type}",
            "value_score": value_score,
            "category": p.get("category", ""),
            "in_stock": in_stock,
        })

    if sort_by == "price":
        candidates.sort(key=lambda x: x["price"])
    elif sort_by == "size":
        candidates.sort(key=lambda x: x["unit_size"], reverse=True)
    else:
        candidates.sort(key=lambda x: x["value_score"], reverse=True)

    candidates = candidates[:limit]

    return {
        "item": generic_name,
        "filters_applied": {
            "brand": brand,
            "min_size": min_size,
            "max_size": max_size,
            "max_price": max_price,
            "sort_by": sort_by,
        },
        "candidate_products": candidates,
        "best_value": max(candidates, key=lambda x: x["value_score"]) if candidates else None,
        "cheapest": min(candidates, key=lambda x: x["price"]) if candidates else None,
        "largest": max(candidates, key=lambda x: x["unit_size"]) if candidates else None,
        "total_found": len(candidates),
    }


async def get_multi_candidates(items: list[dict]):
    """
    Multiple items with individual filters.
    Input: [
        {"name": "rice", "max_price": 5.00, "brand": "Great Value"},
        {"name": "milk"},
        {"name": "eggs", "max_price": 4.00}
    ]
    """
    results = {}
    for item in items:
        name = item if isinstance(item, str) else item.get("name", "")
        brand = None if isinstance(item, str) else item.get("brand")
        min_size = None if isinstance(item, str) else item.get("min_size")
        max_size = None if isinstance(item, str) else item.get("max_size")
        max_price = None if isinstance(item, str) else item.get("max_price")
        sort_by = "value" if isinstance(item, str) else item.get("sort_by", "value")

        result = await get_candidates(
            generic_name=name,
            brand=brand,
            min_size=min_size,
            max_size=max_size,
            max_price=max_price,
            sort_by=sort_by,
        )
        results[name] = result

    return results


async def build_smart_list(items: list[str], user_email: str = None):
    """
    Auto-select best value product for each item.
    Respects user brand preferences.
    """
    db = get_db()
    user_prefs = {}
    if user_email:
        user = await db.users.find_one({"email": user_email})
        if user:
            user_prefs = user.get("brand_preferences", {})

    smart_list = []
    for item_name in items:
        if isinstance(item_name, dict):
            name = item_name.get("name", "")
            brand = item_name.get("brand") or user_prefs.get(name.lower())
            result = await get_candidates(
                generic_name=name,
                brand=brand,
                max_price=item_name.get("max_price"),
                min_size=item_name.get("min_size"),
                max_size=item_name.get("max_size"),
            )
        else:
            name = item_name
            brand = user_prefs.get(name.lower())
            result = await get_candidates(generic_name=name, brand=brand)

        if not result["candidate_products"]:
            continue

        selected = result["candidate_products"][0]

        smart_list.append({
            "item_name": name,
            "selected": selected,
            "alternatives": result["candidate_products"][1:5],
        })

    return smart_list
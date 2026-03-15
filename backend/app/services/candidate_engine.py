from app.db import get_db
from app.services.value_scorer import normalize_to_standard_unit


async def search_autocomplete(prefix: str, limit: int = 10):
    db = get_db()
    results = await db.products.distinct(
        "generic_name",
        {"generic_name": {"$regex": f"^{prefix.lower()}", "$options": "i"}}
    )
    return results[:limit]


async def get_candidates(generic_name: str, user_email: str = None, sort_by: str = "value"):
    db = get_db()

    products = await db.products.find(
        {"generic_name": generic_name.lower()}
    ).to_list(50)

    if not products:
        return {"query": generic_name, "best_pick": None, "candidates": [], "total_found": 0}

    user_prefs = {}
    if user_email:
        user = await db.users.find_one({"email": user_email})
        if user:
            user_prefs = user.get("brand_preferences", {})

    scored = []
    for p in products:
        price = p.get("price", 0)
        if price <= 0:
            continue

        standard_qty = normalize_to_standard_unit(p.get("unit_size", 1), p.get("unit_type", "oz"))
        unit_price = price / standard_qty if standard_qty > 0 else 999

        store = await db.stores.find_one({"store_id": p.get("store_id")})
        store_name = store.get("name", "") if store else ""
        store_rating = store.get("rating", 4.0) if store else 4.0

        rating_weight = 0.8 + (store_rating / 5.0) * 0.4
        in_stock = p.get("in_stock", True)
        stock_penalty = 1.0 if in_stock else 0.3
        value_score = (standard_qty / price) * rating_weight * stock_penalty

        is_preferred = False
        if generic_name.lower() in user_prefs:
            if user_prefs[generic_name.lower()].lower() in p.get("brand", "").lower():
                is_preferred = True
                value_score *= 1.15

        scored.append({
            "product_name": p.get("product_name", ""),
            "generic_name": p.get("generic_name", ""),
            "brand": p.get("brand", ""),
            "store_id": p.get("store_id", ""),
            "store_name": store_name,
            "price": price,
            "unit_size": p.get("unit_size", 0),
            "unit_type": p.get("unit_type", ""),
            "unit_price": round(unit_price, 4),
            "value_score": round(value_score, 4),
            "category": p.get("category", ""),
            "image_url": p.get("image_url", ""),
            "in_stock": in_stock,
            "is_preferred": is_preferred,
        })

    if sort_by == "price":
        scored.sort(key=lambda x: x["price"])
    else:
        scored.sort(key=lambda x: x["value_score"], reverse=True)

    best_pick = scored[0] if scored else None

    return {
        "query": generic_name,
        "best_pick": best_pick,
        "candidates": scored,
        "total_found": len(scored),
    }


async def build_smart_list(items: list[str], user_email: str = None):
    smart_list = []
    for item_name in items:
        result = await get_candidates(item_name, user_email)
        if not result["best_pick"]:
            continue
        smart_list.append({
            "item_name": item_name,
            "selected": result["best_pick"],
            "alternatives": result["candidates"][1:5],
        })
    return smart_list
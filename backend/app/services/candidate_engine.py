from app.services.store_api import fetch_candidates
from app.services.value_scorer import normalize_to_standard_unit


async def score_candidates(query: str, limit: int = 10, sort_by: str = "value"):
    """
    Fetch candidates from all stores, score them, and rank.
    sort_by: "value" (best bang for buck), "price" (cheapest), "brand"
    """
    candidates = await fetch_candidates(query, limit=20)

    scored = []
    for c in candidates:
        if c.price <= 0:
            continue

        standard_qty = normalize_to_standard_unit(c.unit_size, c.unit_type)
        unit_price = c.price / standard_qty if standard_qty > 0 else 999

        stock_penalty = 1.0 if c.in_stock else 0.3
        value_score = (standard_qty / c.price) * stock_penalty

        scored.append({
            "name": c.name,
            "brand": c.brand,
            "store_id": c.store_id,
            "store_name": c.store_name,
            "price": c.price,
            "unit_size": c.unit_size,
            "unit_type": c.unit_type,
            "unit_price": round(unit_price, 4),
            "value_score": round(value_score, 4),
            "category": c.category,
            "image_url": c.image_url,
            "in_stock": c.in_stock,
            "stock_confidence": c.stock_confidence,
        })

    if sort_by == "price":
        scored.sort(key=lambda x: x["price"])
    elif sort_by == "brand":
        scored.sort(key=lambda x: x["brand"].lower())
    else:
        scored.sort(key=lambda x: x["value_score"], reverse=True)

    best_pick = scored[0] if scored else None

    return {
        "query": query,
        "best_pick": best_pick,
        "candidates": scored[:limit],
        "total_found": len(scored),
    }


async def build_smart_list(items: list[str], user_preferences: dict = None):
    """
    Take a list of generic item names, auto-select best candidate for each.
    Returns a ready-to-optimize list with real prices and store assignments.
    """
    smart_list = []

    for item_name in items:
        result = await score_candidates(item_name, limit=5)

        if not result["best_pick"]:
            continue

        pick = result["best_pick"]

        if user_preferences and item_name.lower() in user_preferences.get("brand_preferences", {}):
            preferred_brand = user_preferences["brand_preferences"][item_name.lower()]
            brand_match = next(
                (c for c in result["candidates"] if preferred_brand.lower() in c["brand"].lower()),
                None,
            )
            if brand_match:
                pick = brand_match

        smart_list.append({
            "item_name": item_name,
            "selected": pick,
            "alternatives": [c for c in result["candidates"] if c != pick][:4],
        })

    return smart_list
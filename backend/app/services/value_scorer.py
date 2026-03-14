from app.models.schemas import PriceEntry, Store

UNIT_CONVERSIONS = {
    "oz": 1.0,
    "lb": 16.0,
    "g": 0.03527,
    "kg": 35.274,
    "fl_oz": 1.0,
    "ml": 0.03381,
    "l": 33.814,
    "gal": 128.0,
    "count": 1.0,
    "pack": 1.0,
}


def normalize_to_standard_unit(size, unit_type):
    multiplier = UNIT_CONVERSIONS.get(unit_type.lower(), 1.0)
    return size * multiplier


def compute_value_score(entry, store, brand_pref_match=False):
    if entry.price <= 0:
        return 0.0
    standard_qty = normalize_to_standard_unit(entry.unit_size, entry.unit_type)
    per_unit_value = standard_qty / entry.price
    rating_weight = 0.8 + (store.rating / 5.0) * 0.4
    brand_bonus = 1.15 if brand_pref_match else 1.0
    sale_bonus = 1.10 if entry.on_sale else 1.0
    return per_unit_value * rating_weight * brand_bonus * sale_bonus


def rank_items_by_store(items, price_entries, stores):
    store_map = {s.id: s for s in stores}
    rankings = {}
    for item_name in items:
        item_entries = [e for e in price_entries if e.item_name.lower() == item_name.lower()]
        scored = []
        for entry in item_entries:
            store = store_map.get(entry.store_id)
            if not store:
                continue
            score = compute_value_score(entry, store)
            standard_qty = normalize_to_standard_unit(entry.unit_size, entry.unit_type)
            unit_price = entry.price / standard_qty if standard_qty > 0 else 999
            scored.append({
                "store_id": entry.store_id,
                "store_name": store.name,
                "price": entry.price,
                "unit_size": entry.unit_size,
                "unit_type": entry.unit_type,
                "unit_price": round(unit_price, 4),
                "value_score": round(score, 4),
                "on_sale": entry.on_sale,
                "brand": entry.brand,
            })
        scored.sort(key=lambda x: x["value_score"], reverse=True)
        rankings[item_name] = scored
    return rankings

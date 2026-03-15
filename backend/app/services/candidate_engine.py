import math
from collections import defaultdict

from app.db import get_db
from app.models.schemas import CandidateBundle, CandidateProduct, ShoppingItem, StoreNode


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


async def suggest_item_keys(prefix: str, limit: int = 12) -> list[str]:
    db = get_db()
    if not prefix.strip():
        return []

    pipeline = [
        {
            "$match": {
                "item_key": {"$regex": f"^{prefix.strip().lower()}", "$options": "i"},
                "in_stock": True,
            }
        },
        {"$group": {"_id": "$item_key"}},
        {"$sort": {"_id": 1}},
        {"$limit": limit},
    ]
    docs = await db.products.aggregate(pipeline).to_list(length=limit)
    return [doc["_id"] for doc in docs]


async def get_item_filter_values(item_key: str) -> dict:
    db = get_db()
    products = await db.products.find(
        {"item_key": item_key.lower(), "in_stock": True},
        {
            "_id": 0,
            "brand": 1,
            "package_size": 1,
            "package_unit": 1,
        },
    ).to_list(length=500)

    brand_values = sorted(
        {
            str(product.get("brand", "")).strip()
            for product in products
            if str(product.get("brand", "")).strip()
        }
    )

    size_values = sorted(
        {
            (
                float(product.get("package_size", 0)),
                str(product.get("package_unit", "")).strip(),
            )
            for product in products
            if product.get("package_size") not in [None, 0, 0.0]
            and str(product.get("package_unit", "")).strip()
        },
        key=lambda value: (value[1], value[0]),
    )

    return {
        "item_key": item_key.lower(),
        "brands": brand_values,
        "sizes": [
            {
                "package_size": size,
                "package_unit": unit,
                "label": f"{size:g} {unit}",
            }
            for size, unit in size_values
        ],
    }


async def build_candidate_bundles(
    items: list[ShoppingItem],
    start_lat: float,
    start_lng: float,
    max_radius_miles: float,
    candidate_limit_per_item: int = 30,
) -> tuple[list[CandidateBundle], list[StoreNode]]:
    db = get_db()

    store_docs = await db.stores.find(
        {"is_active": True},
        {
            "_id": 0,
            "store_id": 1,
            "vendor": 1,
            "name": 1,
            "latitude": 1,
            "longitude": 1,
            "open_time": 1,
            "close_time": 1,
            "visit_penalty_minutes": 1,
        },
    ).to_list(length=500)

    nearby_stores: list[StoreNode] = []
    nearby_store_ids: set[str] = set()

    for store in store_docs:
        lat = float(store.get("latitude", 0))
        lon = float(store.get("longitude", 0))
        distance = haversine_miles(start_lat, start_lng, lat, lon)
        if distance <= max_radius_miles:
            nearby_store_ids.add(store["store_id"])
            nearby_stores.append(
                StoreNode(
                    store_id=store["store_id"],
                    lat=lat,
                    lon=lon,
                    name=store.get("name"),
                    vendor=store.get("vendor"),
                    open_time=store.get("open_time", "08:00"),
                    close_time=store.get("close_time", "22:00"),
                    visit_penalty_minutes=int(store.get("visit_penalty_minutes", 10)),
                )
            )

    store_map = {store.store_id: store for store in nearby_stores}
    bundles: list[CandidateBundle] = []

    for item in items:
        query: dict = {
            "item_key": item.item_key.lower(),
            "in_stock": True,
            "store_id": {"$in": list(nearby_store_ids)},
        }

        if item.filters.brand:
            query["brand"] = item.filters.brand

        if item.filters.package_size is not None:
            query["package_size"] = item.filters.package_size

        if item.filters.package_unit:
            query["package_unit"] = item.filters.package_unit

        if item.filters.max_price is not None:
            query["price"] = {"$lte": item.filters.max_price}

        projection = {
            "_id": 0,
            "product_id": 1,
            "store_id": 1,
            "vendor": 1,
            "item_name": 1,
            "brand": 1,
            "package_size": 1,
            "package_unit": 1,
            "price": 1,
            "match_score": 1,
        }

        raw_products = await db.products.find(query, projection).sort(
            [("match_score", -1), ("price", 1)]
        ).to_list(length=300)

        if not raw_products and item.filters.allow_substitutes:
            relaxed_query = {
                "item_key": item.item_key.lower(),
                "in_stock": True,
                "store_id": {"$in": list(nearby_store_ids)},
            }
            if item.filters.max_price is not None:
                relaxed_query["price"] = {"$lte": item.filters.max_price}

            raw_products = await db.products.find(relaxed_query, projection).sort(
                [("match_score", -1), ("price", 1)]
            ).to_list(length=300)

        deduped: dict[tuple, CandidateProduct] = {}
        per_store_counter: defaultdict[str, int] = defaultdict(int)

        for product in raw_products:
            store_id = product["store_id"]
            if store_id not in store_map:
                continue
            if per_store_counter[store_id] >= candidate_limit_per_item:
                continue

            key = (product.get("product_id"), store_id)
            if key in deduped:
                continue

            deduped[key] = CandidateProduct(
                store_id=store_id,
                product_id=product.get("product_id", ""),
                price=float(product.get("price", 0)),
                match_score=float(product.get("match_score", 1.0)),
                brand=product.get("brand"),
                package_size=product.get("package_size"),
                package_unit=product.get("package_unit"),
                item_name=product.get("item_name"),
                vendor=product.get("vendor"),
            )
            per_store_counter[store_id] += 1

        ranked = sorted(
            deduped.values(),
            key=lambda candidate: (-candidate.match_score, candidate.price),
        )[:candidate_limit_per_item]

        bundles.append(
            CandidateBundle(
                item_key=item.item_key.lower(),
                filters=item.filters,
                candidates=ranked,
            )
        )

    return bundles, nearby_stores
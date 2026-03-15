"""
Quick fix: Move 5 Toledo stores near University of Toledo campus.
Run: cd backend && python -m app.fix_toledo_stores
"""
import asyncio
from app.db import connect_db, get_db

# University of Toledo campus center
UT_LAT = 41.6578
UT_LNG = -83.6145

# 5 stores within ~1-3 miles of campus
RELOCATIONS = [
    {"filter": {"store_id": "walmart-toledo-0001"}, "lat": 41.6520, "lon": -83.6050, "name": "Walmart Secor Rd #1"},
    {"filter": {"store_id": "kroger-toledo-0002"}, "lat": 41.6635, "lon": -83.6220, "name": "Kroger W Bancroft #2"},
    {"filter": {"store_id": "target-toledo-0003"}, "lat": 41.6490, "lon": -83.6280, "name": "Target Talmadge Rd #3"},
    {"filter": {"store_id": "costco-toledo-0004"}, "lat": 41.6610, "lon": -83.5980, "name": "Costco Monroe St #4"},
    {"filter": {"store_id": "traderjoes-toledo-0005"}, "lat": 41.6550, "lon": -83.6350, "name": "Trader Joe's Campus #5"},
]


async def fix():
    await connect_db()
    db = get_db()

    # ── Delete 10k products from non-Toledo general stores to free space ──
    print("Deleting 10,000 products from general US stores...")
    pipeline = [
        {"$match": {"store_id": {"$regex": "^.*-us-"}}},
        {"$sample": {"size": 100_000}},
        {"$project": {"_id": 1}},
    ]
    cursor = db.products.aggregate(pipeline)
    ids_to_delete = [doc["_id"] async for doc in cursor]

    if ids_to_delete:
        result = await db.products.delete_many({"_id": {"$in": ids_to_delete}})
        print(f"  ✓ Deleted {result.deleted_count:,} products")
    else:
        print("  ✗ No general US products found to delete")

    before = await db.products.count_documents({})
    print(f"  Products remaining in DB: {before:,}")

    # ── Move 5 Toledo stores near UT campus ──
    print("\nRelocating 5 stores near University of Toledo...")

    for r in RELOCATIONS:
        result = await db.stores.update_one(
            r["filter"],
            {"$set": {"latitude": r["lat"], "longitude": r["lon"], "name": r["name"]}},
        )
        if result.modified_count:
            print(f"  ✓ Moved {r['filter']['store_id']} → ({r['lat']}, {r['lon']}) {r['name']}")
        else:
            print(f"  ✗ {r['filter']['store_id']} not found — skipped")

    # Verify products exist for these stores
    for r in RELOCATIONS:
        sid = r["filter"]["store_id"]
        count = await db.products.count_documents({"store_id": sid})
        print(f"    {sid}: {count} products")

    print("\nDone! These 5 stores are now within 1-3 mi of University of Toledo.")
    print(f"Set your demo start location to: lat={UT_LAT}, lng={UT_LNG}")


if __name__ == "__main__":
    asyncio.run(fix())
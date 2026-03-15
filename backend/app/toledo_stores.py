"""
ALL-IN-ONE: Fix candidate_engine limit + seed UT-area products with strategic pricing.
Run: cd backend && python -m app.seed_ut_final

This script:
1. Patches candidate_engine.py to_list(length=500) → to_list(length=50000)
2. Deletes old products for 5 UT stores
3. Seeds fresh products with STRATEGIC pricing so the optimizer produces interesting routes:
   - Kroger W Bancroft: cheapest for milk, eggs, bread, bananas (single-store winner)
   - Walmart Secor: cheapest for chicken, ground beef, rice, laundry detergent
   - Target Talmadge: cheapest for yogurt, cheese, coffee, cereal
   - Trader Joe's Campus: cheapest for pasta, olive oil, nuts, frozen pizza
   - Costco Monroe: cheapest per-unit on bulk items (water, toilet paper, trash bags)
4. Prints test scenarios you can run in the demo
"""
import asyncio
import os
import random
from datetime import datetime
from pathlib import Path

from app.db import connect_db, get_db


# ---------------------------------------------------------------------------
# Store config
# ---------------------------------------------------------------------------

STORES = [
    {
        "store_id": "walmart-toledo-0001",
        "name": "Walmart Secor Rd #1",
        "vendor": "walmart",
        "lat": 41.6520, "lon": -83.6050,
        "open_time": "06:00", "close_time": "23:00",
        "visit_penalty_minutes": 14,
        "store_brand": "Great Value",
        "price_mult": 0.95,
        # Cheapest for these items (price override to be lowest)
        "wins": ["chicken breast", "ground beef", "rice", "laundry detergent", "trash bags", "paper towels", "diapers", "batteries"],
    },
    {
        "store_id": "kroger-toledo-0002",
        "name": "Kroger W Bancroft #2",
        "vendor": "kroger",
        "lat": 41.6635, "lon": -83.6220,
        "open_time": "06:00", "close_time": "23:00",
        "visit_penalty_minutes": 12,
        "store_brand": "Kroger",
        "price_mult": 1.0,
        # Cheapest for staples — makes it the "single store" winner for a basic list
        "wins": ["milk", "eggs", "bread", "bananas", "butter", "apples", "potatoes", "onions", "lettuce", "carrots"],
    },
    {
        "store_id": "target-toledo-0003",
        "name": "Target Talmadge Rd #3",
        "vendor": "target",
        "lat": 41.6490, "lon": -83.6280,
        "open_time": "08:00", "close_time": "22:00",
        "visit_penalty_minutes": 12,
        "store_brand": "Good & Gather",
        "price_mult": 1.08,
        "wins": ["yogurt", "cheese", "coffee", "cereal", "shampoo", "toothpaste", "granola bars", "cream cheese"],
    },
    {
        "store_id": "costco-toledo-0004",
        "name": "Costco Monroe St #4",
        "vendor": "costco",
        "lat": 41.6610, "lon": -83.5980,
        "open_time": "10:00", "close_time": "20:30",
        "visit_penalty_minutes": 18,
        "store_brand": "Kirkland",
        "price_mult": 1.40,
        # Cheapest per-unit on bulk
        "wins": ["water", "toilet paper", "soda", "chips", "olive oil", "salmon", "dog food"],
    },
    {
        "store_id": "traderjoes-toledo-0005",
        "name": "Trader Joe's Campus #5",
        "vendor": "traderjoes",
        "lat": 41.6550, "lon": -83.6350,
        "open_time": "08:00", "close_time": "21:00",
        "visit_penalty_minutes": 10,
        "store_brand": "Trader Joe's",
        "price_mult": 1.03,
        "wins": ["pasta", "frozen pizza", "nuts", "tortillas", "hummus", "tea", "sparkling water", "ice cream", "frozen vegetables"],
    },
]

# ---------------------------------------------------------------------------
# Full product catalog with realistic base prices
# ---------------------------------------------------------------------------

CATALOG = [
    # Dairy
    {"k": "milk", "d": "Whole Milk", "brands": ["Great Value", "Kroger", "Fairlife", "Organic Valley"], "sizes": [(128, "fl_oz"), (64, "fl_oz")], "base": 3.89},
    {"k": "eggs", "d": "Large Eggs", "brands": ["Great Value", "Kroger", "Eggland's Best", "Good & Gather"], "sizes": [(12, "count"), (18, "count")], "base": 3.49},
    {"k": "butter", "d": "Butter", "brands": ["Land O Lakes", "Kroger", "Great Value", "Kerrygold"], "sizes": [(16, "oz")], "base": 4.79},
    {"k": "yogurt", "d": "Greek Yogurt", "brands": ["Chobani", "Oikos", "Fage", "Kroger"], "sizes": [(5.3, "oz"), (32, "oz")], "base": 1.29},
    {"k": "cheese", "d": "Shredded Cheese", "brands": ["Kraft", "Sargento", "Kroger", "Tillamook"], "sizes": [(8, "oz"), (16, "oz")], "base": 3.99},
    {"k": "cream cheese", "d": "Cream Cheese", "brands": ["Philadelphia", "Kroger", "Great Value"], "sizes": [(8, "oz")], "base": 2.99},
    {"k": "sour cream", "d": "Sour Cream", "brands": ["Daisy", "Kroger"], "sizes": [(16, "oz")], "base": 2.49},
    {"k": "almond milk", "d": "Almond Milk", "brands": ["Silk", "Almond Breeze", "Kroger"], "sizes": [(64, "fl_oz")], "base": 3.79},
    {"k": "oat milk", "d": "Oat Milk", "brands": ["Oatly", "Planet Oat"], "sizes": [(64, "fl_oz")], "base": 4.49},

    # Produce
    {"k": "bananas", "d": "Bananas", "brands": ["Dole", "Chiquita", ""], "sizes": [(1, "lb"), (3, "lb")], "base": 0.65},
    {"k": "apples", "d": "Apples", "brands": ["Gala", "Fuji", "Honeycrisp", "Granny Smith"], "sizes": [(1, "lb"), (3, "lb")], "base": 1.89},
    {"k": "oranges", "d": "Oranges", "brands": ["Navel", "Cara Cara"], "sizes": [(3, "lb"), (4, "lb")], "base": 4.49},
    {"k": "strawberries", "d": "Strawberries", "brands": ["Driscoll's", ""], "sizes": [(16, "oz"), (32, "oz")], "base": 3.99},
    {"k": "blueberries", "d": "Blueberries", "brands": ["Driscoll's", ""], "sizes": [(6, "oz")], "base": 3.49},
    {"k": "grapes", "d": "Grapes", "brands": ["Red", "Green"], "sizes": [(2, "lb")], "base": 4.99},
    {"k": "lettuce", "d": "Romaine Lettuce", "brands": ["", "Dole"], "sizes": [(1, "count"), (3, "count")], "base": 1.99},
    {"k": "tomatoes", "d": "Tomatoes", "brands": ["", "Roma", "On the Vine"], "sizes": [(1, "lb")], "base": 2.49},
    {"k": "onions", "d": "Yellow Onions", "brands": [""], "sizes": [(3, "lb")], "base": 2.99},
    {"k": "potatoes", "d": "Russet Potatoes", "brands": ["Russet", "Gold"], "sizes": [(5, "lb"), (10, "lb")], "base": 4.49},
    {"k": "carrots", "d": "Baby Carrots", "brands": ["", "Organic"], "sizes": [(1, "lb"), (2, "lb")], "base": 1.79},
    {"k": "broccoli", "d": "Broccoli Crown", "brands": [""], "sizes": [(1, "lb")], "base": 1.99},
    {"k": "spinach", "d": "Baby Spinach", "brands": ["Fresh Express", "Organic Girl"], "sizes": [(5, "oz"), (10, "oz")], "base": 3.49},
    {"k": "cucumber", "d": "Cucumber", "brands": [""], "sizes": [(1, "count")], "base": 0.99},

    # Bakery / Grains
    {"k": "bread", "d": "Whole Wheat Bread", "brands": ["Nature's Own", "Sara Lee", "Great Value", "Dave's Killer"], "sizes": [(20, "oz"), (24, "oz")], "base": 3.49},
    {"k": "rice", "d": "Long Grain Rice", "brands": ["Great Value", "Mahatma", "Royal", "Jasmine"], "sizes": [(2, "lb"), (5, "lb"), (10, "lb")], "base": 3.99},
    {"k": "pasta", "d": "Spaghetti", "brands": ["Barilla", "Ronzoni", "Kroger", "De Cecco"], "sizes": [(16, "oz"), (32, "oz")], "base": 1.69},
    {"k": "tortillas", "d": "Flour Tortillas", "brands": ["Mission", "Guerrero"], "sizes": [(10, "count"), (20, "count")], "base": 3.29},
    {"k": "bagels", "d": "Plain Bagels", "brands": ["Thomas", "Kroger"], "sizes": [(6, "count")], "base": 3.79},
    {"k": "cereal", "d": "Cheerios", "brands": ["Cheerios", "General Mills", "Kellogg's", "Kroger"], "sizes": [(12, "oz"), (18, "oz")], "base": 4.29},
    {"k": "oatmeal", "d": "Rolled Oats", "brands": ["Quaker", "Bob's Red Mill"], "sizes": [(42, "oz")], "base": 4.99},
    {"k": "flour", "d": "All Purpose Flour", "brands": ["Gold Medal", "King Arthur"], "sizes": [(5, "lb")], "base": 3.99},
    {"k": "sugar", "d": "Granulated Sugar", "brands": ["Domino", "C&H"], "sizes": [(4, "lb")], "base": 3.99},

    # Meat / Seafood
    {"k": "chicken breast", "d": "Boneless Chicken Breast", "brands": ["Tyson", "Perdue", "Great Value"], "sizes": [(2, "lb"), (3, "lb"), (5, "lb")], "base": 6.99},
    {"k": "ground beef", "d": "Ground Beef 80/20", "brands": ["80/20", "90/10", "Kroger"], "sizes": [(1, "lb"), (2, "lb"), (3, "lb")], "base": 5.99},
    {"k": "salmon", "d": "Atlantic Salmon", "brands": ["Atlantic", "Wild Caught"], "sizes": [(1, "lb")], "base": 9.99},
    {"k": "bacon", "d": "Bacon", "brands": ["Oscar Mayer", "Wright", "Hormel"], "sizes": [(16, "oz")], "base": 6.49},
    {"k": "hot dogs", "d": "Beef Hot Dogs", "brands": ["Oscar Mayer", "Hebrew National", "Ball Park"], "sizes": [(8, "count")], "base": 4.49},

    # Pantry
    {"k": "peanut butter", "d": "Creamy Peanut Butter", "brands": ["Jif", "Skippy", "Kroger"], "sizes": [(16, "oz"), (28, "oz")], "base": 3.99},
    {"k": "jelly", "d": "Grape Jelly", "brands": ["Smucker's", "Welch's"], "sizes": [(18, "oz")], "base": 3.29},
    {"k": "olive oil", "d": "Extra Virgin Olive Oil", "brands": ["Bertolli", "Pompeian", "Great Value"], "sizes": [(17, "fl_oz"), (34, "fl_oz")], "base": 6.49},
    {"k": "pasta sauce", "d": "Marinara Sauce", "brands": ["Prego", "Ragu", "Barilla"], "sizes": [(24, "oz")], "base": 2.99},
    {"k": "canned beans", "d": "Black Beans", "brands": ["Bush's", "Goya", "Kroger"], "sizes": [(15, "oz")], "base": 1.29},
    {"k": "canned tomatoes", "d": "Diced Tomatoes", "brands": ["Hunt's", "Del Monte", "Muir Glen"], "sizes": [(14.5, "oz"), (28, "oz")], "base": 1.49},
    {"k": "canned tuna", "d": "Chunk Light Tuna", "brands": ["StarKist", "Bumble Bee"], "sizes": [(5, "oz")], "base": 1.39},
    {"k": "canned soup", "d": "Chicken Noodle Soup", "brands": ["Campbell's", "Progresso"], "sizes": [(10.75, "oz")], "base": 1.99},
    {"k": "ketchup", "d": "Ketchup", "brands": ["Heinz", "Hunt's"], "sizes": [(20, "oz"), (38, "oz")], "base": 3.79},
    {"k": "honey", "d": "Honey", "brands": ["Sue Bee", "Nature Nate's"], "sizes": [(12, "oz")], "base": 5.99},
    {"k": "hummus", "d": "Classic Hummus", "brands": ["Sabra", "Cedar's"], "sizes": [(10, "oz")], "base": 3.99},

    # Beverages
    {"k": "coffee", "d": "Ground Coffee", "brands": ["Folgers", "Starbucks", "Dunkin"], "sizes": [(12, "oz"), (24, "oz")], "base": 8.99},
    {"k": "tea", "d": "Green Tea Bags", "brands": ["Bigelow", "Twinings", "Tazo"], "sizes": [(20, "count"), (40, "count")], "base": 3.99},
    {"k": "juice", "d": "Orange Juice", "brands": ["Tropicana", "Simply", "Minute Maid"], "sizes": [(52, "fl_oz")], "base": 4.29},
    {"k": "water", "d": "Bottled Water Pack", "brands": ["Dasani", "Aquafina", "Pure Life"], "sizes": [(24, "count"), (40, "count")], "base": 5.49},
    {"k": "soda", "d": "Coca-Cola", "brands": ["Coca-Cola", "Pepsi", "Dr Pepper"], "sizes": [(12, "count"), (24, "count")], "base": 6.99},
    {"k": "sparkling water", "d": "Sparkling Water", "brands": ["LaCroix", "Bubly", "Topo Chico"], "sizes": [(12, "count")], "base": 4.99},
    {"k": "energy drink", "d": "Energy Drink", "brands": ["Red Bull", "Monster", "Celsius"], "sizes": [(4, "count")], "base": 6.99},

    # Snacks
    {"k": "chips", "d": "Potato Chips", "brands": ["Lay's", "Ruffles", "Pringles", "Kettle Brand"], "sizes": [(7.75, "oz"), (13, "oz")], "base": 4.29},
    {"k": "cookies", "d": "Chocolate Chip Cookies", "brands": ["Oreo", "Chips Ahoy", "Pepperidge Farm"], "sizes": [(14, "oz")], "base": 4.49},
    {"k": "granola bars", "d": "Granola Bars", "brands": ["Nature Valley", "Kind", "Quaker"], "sizes": [(6, "count"), (12, "count")], "base": 3.99},
    {"k": "nuts", "d": "Mixed Nuts", "brands": ["Planters", "Blue Diamond"], "sizes": [(16, "oz")], "base": 8.49},
    {"k": "tortilla chips", "d": "Tortilla Chips", "brands": ["Tostitos", "Doritos", "Late July"], "sizes": [(13, "oz")], "base": 4.29},
    {"k": "popcorn", "d": "Microwave Popcorn", "brands": ["Orville Redenbacher", "Act II"], "sizes": [(6, "count")], "base": 3.99},

    # Frozen
    {"k": "frozen pizza", "d": "Frozen Pizza", "brands": ["DiGiorno", "Red Baron", "Totino's"], "sizes": [(12, "oz"), (28, "oz")], "base": 5.99},
    {"k": "ice cream", "d": "Ice Cream", "brands": ["Ben & Jerry's", "Breyers", "Haagen-Dazs"], "sizes": [(16, "fl_oz"), (48, "fl_oz")], "base": 5.49},
    {"k": "frozen vegetables", "d": "Frozen Mixed Vegetables", "brands": ["Birds Eye", "Green Giant"], "sizes": [(12, "oz"), (16, "oz")], "base": 2.49},

    # Household
    {"k": "laundry detergent", "d": "Laundry Detergent", "brands": ["Tide", "Gain", "All", "Arm & Hammer"], "sizes": [(92, "fl_oz"), (128, "fl_oz")], "base": 11.99},
    {"k": "dish soap", "d": "Dish Soap", "brands": ["Dawn", "Palmolive"], "sizes": [(19.4, "fl_oz")], "base": 3.79},
    {"k": "toilet paper", "d": "Toilet Paper", "brands": ["Charmin", "Scott", "Cottonelle"], "sizes": [(12, "count"), (24, "count")], "base": 11.99},
    {"k": "paper towels", "d": "Paper Towels", "brands": ["Bounty", "Viva", "Brawny"], "sizes": [(6, "count")], "base": 9.49},
    {"k": "trash bags", "d": "Tall Kitchen Trash Bags", "brands": ["Glad", "Hefty"], "sizes": [(40, "count")], "base": 8.99},

    # Personal Care
    {"k": "shampoo", "d": "Shampoo", "brands": ["Pantene", "Head & Shoulders", "Dove"], "sizes": [(12, "fl_oz"), (20, "fl_oz")], "base": 5.99},
    {"k": "toothpaste", "d": "Toothpaste", "brands": ["Colgate", "Crest", "Sensodyne"], "sizes": [(5.5, "oz")], "base": 4.29},
    {"k": "soap", "d": "Bar Soap", "brands": ["Dove", "Irish Spring", "Dial"], "sizes": [(6, "count")], "base": 5.49},
    {"k": "batteries", "d": "AA Batteries", "brands": ["Energizer", "Duracell"], "sizes": [(8, "count"), (24, "count")], "base": 7.99},
    {"k": "diapers", "d": "Diapers Size 3", "brands": ["Huggies", "Pampers", "Luvs"], "sizes": [(52, "count")], "base": 24.99},

    # Pet
    {"k": "dog food", "d": "Dog Food", "brands": ["Purina", "Blue Buffalo", "Pedigree"], "sizes": [(15, "lb"), (30, "lb")], "base": 19.99},
]


# ---------------------------------------------------------------------------
# Patch candidate_engine.py
# ---------------------------------------------------------------------------

def patch_candidate_engine():
    engine_path = Path(__file__).parent / "services" / "candidate_engine.py"
    if not engine_path.exists():
        print("  ⚠ candidate_engine.py not found, skipping patch")
        return False

    content = engine_path.read_text()
    old = ").to_list(length=500)"
    new = ").to_list(length=50000)"

    if old in content:
        content = content.replace(old, new)
        engine_path.write_text(content)
        print("  ✓ Patched candidate_engine.py: to_list(length=500) → to_list(length=50000)")
        return True
    elif new in content:
        print("  ✓ candidate_engine.py already patched")
        return True
    else:
        print("  ⚠ Could not find to_list pattern in candidate_engine.py")
        return False


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

async def seed():
    await connect_db()
    db = get_db()
    rng = random.Random(2026)

    # Step 0: Patch candidate_engine
    print("=" * 60)
    print("Step 0: Patching candidate_engine.py")
    print("=" * 60)
    patch_candidate_engine()

    # Step 1: Ensure stores exist with correct coordinates
    print("\n" + "=" * 60)
    print("Step 1: Upserting 5 stores near University of Toledo")
    print("=" * 60)

    for s in STORES:
        await db.stores.update_one(
            {"store_id": s["store_id"]},
            {"$set": {
                "store_id": s["store_id"],
                "vendor": s["vendor"],
                "name": s["name"],
                "latitude": s["lat"],
                "longitude": s["lon"],
                "open_time": s["open_time"],
                "close_time": s["close_time"],
                "visit_penalty_minutes": s["visit_penalty_minutes"],
                "is_active": True,
            }},
            upsert=True,
        )
        print(f"  ✓ {s['store_id']} → {s['name']} ({s['lat']}, {s['lon']})")

    # Step 2: Delete old products for these stores
    print("\n" + "=" * 60)
    print("Step 2: Clearing old products for these stores")
    print("=" * 60)

    for s in STORES:
        r = await db.products.delete_many({"store_id": s["store_id"]})
        print(f"  Cleared {r.deleted_count:,} from {s['store_id']}")

    # Step 3: Generate strategically-priced products
    print("\n" + "=" * 60)
    print("Step 3: Generating products with strategic pricing")
    print("=" * 60)

    all_products: list[dict] = []
    pid = 0

    for store in STORES:
        sid = store["store_id"]
        vendor = store["vendor"]
        store_brand = store["store_brand"]
        base_mult = store["price_mult"]
        win_items = set(store["wins"])

        for item in CATALOG:
            ik = item["k"]

            # This store is the cheapest for this item
            is_winner = ik in win_items

            # Generate 2-4 variants per item
            brands_to_use = [store_brand] + item["brands"][:3]
            seen: set[str] = set()

            for brand in brands_to_use:
                if brand in seen:
                    continue
                seen.add(brand)

                for size, unit in item["sizes"]:
                    pid += 1
                    actual_size = size
                    price = item["base"]

                    # Costco: bigger sizes
                    if vendor == "costco":
                        actual_size = round(size * 2, 2)
                        price = price * 1.6  # higher sticker but cheaper per unit

                    # Apply store multiplier
                    price *= base_mult

                    # If this store WINS this item, make it clearly cheapest
                    if is_winner:
                        price *= rng.uniform(0.72, 0.82)  # 18-28% cheaper
                    else:
                        price *= rng.uniform(0.98, 1.15)  # normal-to-expensive

                    price = round(max(0.49, price), 2)
                    actual_size = round(actual_size, 2)

                    name = f"{brand} {item['d']} {actual_size:g} {unit}".strip()

                    all_products.append({
                        "product_id": f"{sid}-ut-{pid:06d}",
                        "store_id": sid,
                        "vendor": vendor,
                        "item_key": ik,
                        "item_name": name,
                        "brand": brand,
                        "package_size": actual_size,
                        "package_unit": unit,
                        "price": price,
                        "match_score": round(0.95 if is_winner else rng.uniform(0.85, 0.98), 3),
                        "in_stock": True,
                        "last_updated": datetime.utcnow(),
                    })

    print(f"  Generated {len(all_products):,} products")

    # Insert in batches
    batch = 2000
    for i in range(0, len(all_products), batch):
        chunk = all_products[i:i + batch]
        await db.products.insert_many(chunk)

    print(f"  ✓ Inserted {len(all_products):,} products")

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("Step 4: Verification")
    print("=" * 60)

    for s in STORES:
        count = await db.products.count_documents({"store_id": s["store_id"]})
        milk_count = await db.products.count_documents({"store_id": s["store_id"], "item_key": "milk"})
        print(f"  {s['name']}: {count:,} products (milk: {milk_count})")

    total = await db.products.count_documents({})
    total_stores = await db.stores.count_documents({})
    print(f"\n  Total DB: {total:,} products, {total_stores:,} stores")

    # Step 5: Print pricing winners
    print("\n" + "=" * 60)
    print("Step 5: Price check (cheapest store per item)")
    print("=" * 60)

    test_items = ["milk", "eggs", "bread", "bananas", "chicken breast", "pasta", "rice", "coffee"]
    for ik in test_items:
        pipeline = [
            {"$match": {"item_key": ik, "store_id": {"$in": [s["store_id"] for s in STORES]}, "in_stock": True}},
            {"$sort": {"price": 1}},
            {"$limit": 1},
        ]
        docs = await db.products.aggregate(pipeline).to_list(length=1)
        if docs:
            d = docs[0]
            print(f"  {ik:20s} → ${d['price']:.2f} at {d['store_id']} ({d['brand']} {d.get('package_size', '')} {d.get('package_unit', '')})")
        else:
            print(f"  {ik:20s} → NOT FOUND")

    # Step 6: Test scenarios
    print("\n" + "=" * 60)
    print("DEMO TEST SCENARIOS")
    print("=" * 60)
    print("""
    Location: lat=41.6578, lng=-83.6145 (University of Toledo)
    Radius: 5 miles
    Trip start: 18:00

    TEST 1 — Single Store Winner (Kroger dominates)
    Items: milk, eggs, bread, bananas, apples, butter
    Expected: Route 1 should be Kroger-only (cheapest for all 6)
              Other routes should be multi-store but more expensive

    TEST 2 — Multi-Store Savings
    Items: milk, eggs, chicken breast, pasta, coffee, yogurt
    Expected: Best balanced = multi-store (Kroger + Walmart + Target)
              because no single store is cheapest for all items

    TEST 3 — Full Grocery Run (10 items)
    Items: milk, eggs, bread, rice, chicken breast, pasta, bananas,
           cereal, olive oil, laundry detergent
    Expected: 10 diverse routes with different store combos
              Balanced pick should be 2-3 stores

    TEST 4 — Bulk Shopping (Costco advantage)
    Items: water, toilet paper, trash bags, chips, soda
    Expected: Costco should appear in cheapest routes
              despite higher visit penalty (18 min)

    TEST 5 — Quick Campus Run (Trader Joe's)
    Items: pasta, frozen pizza, nuts, hummus, sparkling water
    Expected: Trader Joe's single-store route should win
              (closest to campus + cheapest for all 5)

    TEST 6 — Edge Case: Everything
    Items: milk, eggs, bread, chicken breast, rice, pasta, bananas,
           cereal, coffee, laundry detergent, toilet paper, shampoo
    Expected: No single store wins all 12. Interesting multi-store routes.
    """)


if __name__ == "__main__":
    asyncio.run(seed())
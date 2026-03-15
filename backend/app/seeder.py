"""
seed_expansion.py — Additive seeder
Adds ~7000 new stores + ~900k products on top of existing data.
Includes 20 dense stores around Toledo, OH with ~100k products total.

Usage:
    cd backend
    python -m app.seed_expansion
"""

import asyncio
import random
from datetime import datetime

from app.db import connect_db, get_db

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BATCH_SIZE = 10_000  # MongoDB insert batch size
RNG_SEED = 2026

# 20 Toledo stores, each gets 5000 products → 100k total for Toledo
TOLEDO_STORE_COUNT = 20
TOLEDO_PRODUCTS_PER_STORE = 5000

# Remaining stores spread across US cities
# Total new stores = 7000. Toledo takes 20, rest = 6980
GENERAL_STORE_COUNT = 6980
# ~800k products spread across 6980 stores → ~115 products per store
GENERAL_PRODUCTS_PER_STORE = 115

VENDOR_CONFIG = {
    "walmart": {
        "name_prefix": "Walmart",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 14,
    },
    "kroger": {
        "name_prefix": "Kroger",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 12,
    },
    "target": {
        "name_prefix": "Target",
        "open_time": "08:00",
        "close_time": "22:00",
        "visit_penalty_minutes": 12,
    },
    "costco": {
        "name_prefix": "Costco",
        "open_time": "10:00",
        "close_time": "20:30",
        "visit_penalty_minutes": 18,
    },
    "traderjoes": {
        "name_prefix": "Trader Joe's",
        "open_time": "08:00",
        "close_time": "21:00",
        "visit_penalty_minutes": 10,
    },
    "aldis": {
        "name_prefix": "Aldi",
        "open_time": "09:00",
        "close_time": "20:00",
        "visit_penalty_minutes": 8,
    },
    "meijer": {
        "name_prefix": "Meijer",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 14,
    },
    "publix": {
        "name_prefix": "Publix",
        "open_time": "07:00",
        "close_time": "22:00",
        "visit_penalty_minutes": 10,
    },
    "heb": {
        "name_prefix": "H-E-B",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 12,
    },
    "safeway": {
        "name_prefix": "Safeway",
        "open_time": "06:00",
        "close_time": "23:00",
        "visit_penalty_minutes": 11,
    },
}

# Toledo area neighborhoods (lat/lon around Toledo, OH)
TOLEDO_CENTERS = [
    ("Toledo Downtown", "43604", 41.6528, -83.5379),
    ("Toledo West", "43607", 41.6400, -83.5800),
    ("Oregon OH", "43616", 41.6440, -83.4870),
    ("Sylvania", "43560", 41.7120, -83.7130),
    ("Maumee", "43537", 41.5628, -83.6534),
    ("Perrysburg", "43551", 41.5570, -83.6271),
    ("Holland", "43528", 41.6200, -83.7100),
    ("Rossford", "43460", 41.5100, -83.5650),
    ("Northwood", "43619", 41.6000, -83.4800),
    ("Waterville", "43566", 41.5000, -83.7200),
]

# 120 US metro areas for the 6980 general stores
US_AREA_CENTERS = [
    # Ohio
    ("Toledo", "43604", 41.6528, -83.5379),
    ("Columbus OH", "43215", 39.9612, -82.9988),
    ("Cleveland", "44114", 41.4993, -81.6944),
    ("Cincinnati", "45202", 39.1031, -84.5120),
    ("Dayton", "45402", 39.7589, -84.1916),
    ("Akron", "44308", 41.0814, -81.5190),
    # Michigan
    ("Detroit", "48226", 42.3314, -83.0458),
    ("Ann Arbor", "48104", 42.2808, -83.7430),
    ("Grand Rapids", "49503", 42.9634, -85.6681),
    ("Lansing", "48933", 42.7325, -84.5555),
    # Northeast
    ("New York", "10001", 40.7484, -73.9967),
    ("Boston", "02108", 42.3601, -71.0589),
    ("Philadelphia", "19103", 39.9526, -75.1652),
    ("Pittsburgh", "15222", 40.4406, -79.9959),
    ("Buffalo", "14202", 42.8864, -78.8784),
    ("Hartford", "06103", 41.7658, -72.6734),
    ("Providence", "02903", 41.8240, -71.4128),
    ("Newark", "07102", 40.7357, -74.1724),
    ("Baltimore", "21201", 39.2904, -76.6122),
    ("Washington DC", "20001", 38.9072, -77.0369),
    # Southeast
    ("Atlanta", "30303", 33.7490, -84.3880),
    ("Miami", "33101", 25.7617, -80.1918),
    ("Tampa", "33602", 27.9506, -82.4572),
    ("Orlando", "32801", 28.5383, -81.3792),
    ("Charlotte", "28202", 35.2271, -80.8431),
    ("Raleigh", "27601", 35.7796, -78.6382),
    ("Nashville", "37203", 36.1627, -86.7816),
    ("Memphis", "38103", 35.1495, -90.0490),
    ("Jacksonville", "32202", 30.3322, -81.6557),
    ("Richmond", "23219", 37.5407, -77.4360),
    ("Charleston SC", "29401", 32.7765, -79.9311),
    ("Savannah", "31401", 32.0809, -81.0912),
    ("Birmingham", "35203", 33.5186, -86.8104),
    ("New Orleans", "70112", 29.9511, -90.0715),
    # Midwest
    ("Chicago", "60601", 41.8781, -87.6298),
    ("Indianapolis", "46204", 39.7684, -86.1581),
    ("Milwaukee", "53202", 43.0389, -87.9065),
    ("Minneapolis", "55401", 44.9778, -93.2650),
    ("St. Louis", "63101", 38.6270, -90.1994),
    ("Kansas City", "64106", 39.0997, -94.5786),
    ("Omaha", "68102", 41.2565, -95.9345),
    ("Des Moines", "50309", 41.5868, -93.6250),
    ("Madison", "53703", 43.0731, -89.4012),
    ("Louisville", "40202", 38.2527, -85.7585),
    # Southwest
    ("Dallas", "75201", 32.7767, -96.7970),
    ("Houston", "77002", 29.7604, -95.3698),
    ("San Antonio", "78205", 29.4241, -98.4936),
    ("Austin", "78701", 30.2672, -97.7431),
    ("Phoenix", "85004", 33.4484, -112.0740),
    ("Tucson", "85701", 32.2226, -110.9747),
    ("El Paso", "79901", 31.7619, -106.4850),
    ("Albuquerque", "87102", 35.0844, -106.6504),
    ("Oklahoma City", "73102", 35.4676, -97.5164),
    ("Tulsa", "74103", 36.1540, -95.9928),
    # West Coast
    ("Los Angeles", "90012", 34.0522, -118.2437),
    ("San Francisco", "94102", 37.7749, -122.4194),
    ("San Diego", "92101", 32.7157, -117.1611),
    ("San Jose", "95113", 37.3382, -121.8863),
    ("Seattle", "98101", 47.6062, -122.3321),
    ("Portland OR", "97204", 45.5152, -122.6784),
    ("Sacramento", "95814", 38.5816, -121.4944),
    ("Las Vegas", "89101", 36.1699, -115.1398),
    ("Denver", "80202", 39.7392, -104.9903),
    ("Salt Lake City", "84101", 40.7608, -111.8910),
    ("Boise", "83702", 43.6150, -116.2023),
    ("Spokane", "99201", 47.6588, -117.4260),
    # Mountain / Plains
    ("Colorado Springs", "80903", 38.8339, -104.8214),
    ("Wichita", "67202", 37.6872, -97.3301),
    ("Little Rock", "72201", 34.7465, -92.2896),
    ("Fargo", "58102", 46.8772, -96.7898),
    ("Sioux Falls", "57104", 43.5460, -96.7313),
    ("Billings", "59101", 45.7833, -108.5007),
    # More cities to spread data
    ("Fresno", "93721", 36.7378, -119.7871),
    ("Riverside", "92501", 33.9533, -117.3962),
    ("Bakersfield", "93301", 35.3733, -119.0187),
    ("Stockton", "95202", 37.9577, -121.2908),
    ("Spokane", "99201", 47.6588, -117.4260),
    ("Tacoma", "98402", 47.2529, -122.4443),
    ("Reno", "89501", 39.5296, -119.8138),
    ("Knoxville", "37902", 35.9606, -83.9207),
    ("Chattanooga", "37402", 35.0456, -85.3097),
    ("Huntsville", "35801", 34.7304, -86.5861),
    ("Mobile", "36602", 30.6954, -88.0399),
    ("Baton Rouge", "70801", 30.4515, -91.1871),
    ("Shreveport", "71101", 32.5252, -93.7502),
    ("Jackson MS", "39201", 32.2988, -90.1848),
    ("Montgomery", "36104", 32.3792, -86.3077),
    ("Lexington KY", "40507", 38.0406, -84.5037),
    ("Norfolk", "23510", 36.8508, -76.2859),
    ("Greensboro", "27401", 36.0726, -79.7920),
    ("Durham", "27701", 35.9940, -78.8986),
    ("Columbia SC", "29201", 34.0007, -81.0348),
    ("Augusta GA", "30901", 33.4735, -81.9748),
    ("Tallahassee", "32301", 30.4383, -84.2807),
    ("Fort Wayne", "46802", 41.0793, -85.1394),
    ("South Bend", "46601", 41.6764, -86.2520),
    ("Evansville", "47708", 37.9716, -87.5711),
    ("Cedar Rapids", "52401", 41.9779, -91.6656),
    ("Davenport", "52801", 41.5236, -90.5776),
    ("Springfield IL", "62701", 39.7817, -89.6501),
    ("Peoria", "61602", 40.6936, -89.5890),
    ("Rockford", "61101", 42.2711, -89.0940),
    ("Green Bay", "54301", 44.5133, -88.0133),
    ("Appleton", "54911", 44.2619, -88.4154),
    ("Duluth", "55802", 46.7867, -92.1005),
    ("Rochester MN", "55901", 44.0121, -92.4802),
    ("St. Paul", "55101", 44.9537, -93.0900),
    ("Lincoln", "68508", 40.8136, -96.7026),
    ("Topeka", "66603", 39.0473, -95.6752),
    ("Springfield MO", "65806", 37.2090, -93.2923),
    ("Columbia MO", "65201", 38.9517, -92.3341),
    ("Amarillo", "79101", 35.2220, -101.8313),
    ("Lubbock", "79401", 33.5779, -101.8552),
    ("Corpus Christi", "78401", 27.8006, -97.3964),
    ("Laredo", "78040", 27.5036, -99.5076),
    ("Anchorage", "99501", 61.2181, -149.9003),
    ("Honolulu", "96813", 21.3069, -157.8583),
]

# Expanded item catalog — 120 items for more product variety
ITEM_CATALOG = [
    {"item_key": "milk", "display_name": "Whole Milk", "category": "Dairy", "brands": ["Great Value", "Kroger", "Good & Gather", "Organic Valley", "Fairlife", "Hood", "Borden"], "sizes": [(1, "gallon"), (64, "fl_oz"), (128, "fl_oz")], "base_price": 3.50},
    {"item_key": "eggs", "display_name": "Large Eggs", "category": "Dairy", "brands": ["Great Value", "Kroger", "Good & Gather", "Eggland's Best", "Happy Egg Co"], "sizes": [(12, "count"), (18, "count"), (24, "count"), (36, "count")], "base_price": 3.20},
    {"item_key": "bread", "display_name": "Bread", "category": "Bakery", "brands": ["Great Value", "Kroger", "Nature's Own", "Good & Gather", "Sara Lee", "Dave's Killer"], "sizes": [(20, "oz"), (24, "oz"), (27, "oz")], "base_price": 3.00},
    {"item_key": "rice", "display_name": "Rice", "category": "Grains", "brands": ["Great Value", "Kroger", "Royal", "Mahatma", "Uncle Ben's", "Jasmine"], "sizes": [(2, "lb"), (5, "lb"), (10, "lb"), (20, "lb")], "base_price": 0.90},
    {"item_key": "chicken breast", "display_name": "Chicken Breast", "category": "Meat", "brands": ["Great Value", "Kroger", "Tyson", "Good & Gather", "Perdue"], "sizes": [(1.5, "lb"), (2, "lb"), (2.5, "lb"), (3, "lb"), (5, "lb")], "base_price": 3.20},
    {"item_key": "olive oil", "display_name": "Olive Oil", "category": "Cooking", "brands": ["Great Value", "Kroger", "Good & Gather", "Bertolli", "Pompeian", "Filippo Berio"], "sizes": [(16.9, "fl_oz"), (17, "fl_oz"), (34, "fl_oz"), (67.6, "fl_oz")], "base_price": 0.35},
    {"item_key": "bananas", "display_name": "Bananas", "category": "Produce", "brands": ["Dole", "Chiquita", "Del Monte", ""], "sizes": [(1, "lb"), (3, "lb"), (1, "count")], "base_price": 0.60},
    {"item_key": "cereal", "display_name": "Cereal", "category": "Breakfast", "brands": ["Great Value", "Kroger", "Cheerios", "Good & Gather", "General Mills", "Kellogg's", "Post"], "sizes": [(12, "oz"), (18, "oz"), (24, "oz"), (36, "oz")], "base_price": 0.22},
    {"item_key": "pasta", "display_name": "Pasta", "category": "Grains", "brands": ["Great Value", "Kroger", "Barilla", "Good & Gather", "Ronzoni", "De Cecco"], "sizes": [(12, "oz"), (16, "oz"), (32, "oz")], "base_price": 0.09},
    {"item_key": "laundry detergent", "display_name": "Laundry Detergent", "category": "Household", "brands": ["Tide", "Great Value", "Kroger", "Gain", "All", "Persil", "Arm & Hammer"], "sizes": [(64, "fl_oz"), (92, "fl_oz"), (128, "fl_oz"), (170, "fl_oz")], "base_price": 0.13},
    {"item_key": "broccoli", "display_name": "Broccoli", "category": "Produce", "brands": ["", "Organic"], "sizes": [(1, "count"), (12, "oz"), (1, "lb"), (2, "lb")], "base_price": 1.80},
    {"item_key": "apples", "display_name": "Apples", "category": "Produce", "brands": ["Gala", "Fuji", "Honeycrisp", "Granny Smith", "Pink Lady"], "sizes": [(2, "lb"), (3, "lb"), (5, "lb")], "base_price": 1.60},
    {"item_key": "oranges", "display_name": "Oranges", "category": "Produce", "brands": ["Navel", "Cara Cara", "Valencia"], "sizes": [(2, "lb"), (3, "lb"), (4, "lb")], "base_price": 1.40},
    {"item_key": "yogurt", "display_name": "Greek Yogurt", "category": "Dairy", "brands": ["Chobani", "Oikos", "Kroger", "Great Value", "Fage", "Siggi's"], "sizes": [(5.3, "oz"), (32, "oz")], "base_price": 0.18},
    {"item_key": "cheese", "display_name": "Cheese", "category": "Dairy", "brands": ["Kraft", "Kroger", "Great Value", "Sargento", "Tillamook", "Cabot"], "sizes": [(8, "oz"), (16, "oz"), (32, "oz")], "base_price": 0.38},
    {"item_key": "butter", "display_name": "Butter", "category": "Dairy", "brands": ["Kroger", "Great Value", "Land O Lakes", "Kerrygold", "Challenge"], "sizes": [(16, "oz"), (32, "oz")], "base_price": 0.28},
    {"item_key": "coffee", "display_name": "Coffee", "category": "Beverages", "brands": ["Folgers", "Maxwell House", "Kroger", "Starbucks", "Dunkin", "Lavazza", "Peet's"], "sizes": [(12, "oz"), (24, "oz"), (40, "oz")], "base_price": 0.40},
    {"item_key": "tea", "display_name": "Tea Bags", "category": "Beverages", "brands": ["Lipton", "Kroger", "Bigelow", "Twinings", "Celestial Seasonings", "Tazo"], "sizes": [(20, "count"), (40, "count"), (80, "count"), (100, "count")], "base_price": 0.06},
    {"item_key": "juice", "display_name": "Orange Juice", "category": "Beverages", "brands": ["Tropicana", "Simply", "Kroger", "Great Value", "Florida's Natural", "Minute Maid"], "sizes": [(52, "fl_oz"), (89, "fl_oz")], "base_price": 0.06},
    {"item_key": "water", "display_name": "Bottled Water", "category": "Beverages", "brands": ["Pure Life", "Dasani", "Kroger", "Great Value", "Poland Spring", "Aquafina"], "sizes": [(24, "count"), (32, "count"), (40, "count")], "base_price": 0.16},
    {"item_key": "chips", "display_name": "Potato Chips", "category": "Snacks", "brands": ["Lay's", "Kroger", "Great Value", "Ruffles", "Kettle Brand", "Cape Cod", "Pringles"], "sizes": [(7.75, "oz"), (9, "oz"), (13, "oz")], "base_price": 0.40},
    {"item_key": "cookies", "display_name": "Cookies", "category": "Snacks", "brands": ["Oreo", "Chips Ahoy", "Kroger", "Great Value", "Pepperidge Farm", "Nutter Butter"], "sizes": [(10, "oz"), (14, "oz"), (20, "oz")], "base_price": 0.28},
    {"item_key": "crackers", "display_name": "Crackers", "category": "Snacks", "brands": ["Ritz", "Kroger", "Great Value", "Triscuit", "Wheat Thins", "Cheez-It"], "sizes": [(10, "oz"), (13.7, "oz"), (21, "oz")], "base_price": 0.30},
    {"item_key": "soda", "display_name": "Soda", "category": "Beverages", "brands": ["Coca-Cola", "Pepsi", "Sprite", "Dr Pepper", "Mountain Dew", "Fanta"], "sizes": [(12, "count"), (24, "count"), (36, "count")], "base_price": 0.40},
    {"item_key": "sparkling water", "display_name": "Sparkling Water", "category": "Beverages", "brands": ["LaCroix", "Bubly", "Kroger", "Topo Chico", "Perrier", "San Pellegrino"], "sizes": [(8, "count"), (12, "count"), (24, "count")], "base_price": 0.50},
    {"item_key": "toilet paper", "display_name": "Toilet Paper", "category": "Household", "brands": ["Charmin", "Scott", "Kroger", "Great Value", "Cottonelle", "Angel Soft"], "sizes": [(6, "count"), (12, "count"), (24, "count"), (48, "count")], "base_price": 0.65},
    {"item_key": "paper towels", "display_name": "Paper Towels", "category": "Household", "brands": ["Bounty", "Kroger", "Great Value", "Viva", "Brawny", "Sparkle"], "sizes": [(2, "count"), (6, "count"), (12, "count")], "base_price": 1.20},
    {"item_key": "dish soap", "display_name": "Dish Soap", "category": "Household", "brands": ["Dawn", "Palmolive", "Kroger", "Ajax", "Method"], "sizes": [(19.4, "fl_oz"), (28, "fl_oz"), (38, "fl_oz")], "base_price": 0.14},
    {"item_key": "shampoo", "display_name": "Shampoo", "category": "Personal Care", "brands": ["Pantene", "Head & Shoulders", "Tresemme", "Suave", "Dove", "Garnier"], "sizes": [(12, "fl_oz"), (20, "fl_oz"), (28, "fl_oz")], "base_price": 0.28},
    {"item_key": "toothpaste", "display_name": "Toothpaste", "category": "Personal Care", "brands": ["Colgate", "Crest", "Sensodyne", "Arm & Hammer"], "sizes": [(3.5, "oz"), (5.5, "oz"), (8, "oz")], "base_price": 0.65},
    {"item_key": "soap", "display_name": "Bar Soap", "category": "Personal Care", "brands": ["Dove", "Irish Spring", "Dial", "Ivory", "Safeguard"], "sizes": [(6, "count"), (8, "count"), (10, "count")], "base_price": 0.70},
    {"item_key": "frozen pizza", "display_name": "Frozen Pizza", "category": "Frozen", "brands": ["DiGiorno", "Totino's", "Kroger", "Red Baron", "Jack's", "Tombstone"], "sizes": [(12, "oz"), (20, "oz"), (28, "oz")], "base_price": 0.30},
    {"item_key": "ice cream", "display_name": "Ice Cream", "category": "Frozen", "brands": ["Ben & Jerry's", "Breyers", "Kroger", "Blue Bunny", "Haagen-Dazs", "Turkey Hill"], "sizes": [(16, "fl_oz"), (48, "fl_oz"), (128, "fl_oz")], "base_price": 0.10},
    {"item_key": "frozen vegetables", "display_name": "Frozen Vegetables", "category": "Frozen", "brands": ["Birds Eye", "Kroger", "Great Value", "Green Giant", "Pictsweet"], "sizes": [(10, "oz"), (12, "oz"), (16, "oz"), (32, "oz")], "base_price": 0.14},
    {"item_key": "ground beef", "display_name": "Ground Beef", "category": "Meat", "brands": ["Kroger", "Great Value", "Simple Truth", "Laura's Lean", "80/20", "90/10"], "sizes": [(1, "lb"), (2, "lb"), (3, "lb"), (5, "lb")], "base_price": 4.50},
    {"item_key": "salmon", "display_name": "Salmon", "category": "Seafood", "brands": ["Kroger", "Great Value", "Atlantic", "Wild Caught", "Fresh Market"], "sizes": [(12, "oz"), (1, "lb"), (2, "lb")], "base_price": 7.00},
    {"item_key": "shrimp", "display_name": "Shrimp", "category": "Seafood", "brands": ["Kroger", "Great Value", "SeaPak", "Aqua Star"], "sizes": [(12, "oz"), (16, "oz"), (2, "lb")], "base_price": 0.55},
    {"item_key": "lettuce", "display_name": "Lettuce", "category": "Produce", "brands": ["", "Organic", "Dole", "Fresh Express"], "sizes": [(1, "count"), (10, "oz"), (12, "oz")], "base_price": 1.60},
    {"item_key": "tomatoes", "display_name": "Tomatoes", "category": "Produce", "brands": ["", "Roma", "On the Vine", "Organic"], "sizes": [(1, "lb"), (2, "lb")], "base_price": 2.20},
    {"item_key": "onions", "display_name": "Onions", "category": "Produce", "brands": ["", "Yellow", "Red", "Sweet"], "sizes": [(2, "lb"), (3, "lb"), (5, "lb")], "base_price": 0.80},
    {"item_key": "potatoes", "display_name": "Potatoes", "category": "Produce", "brands": ["Russet", "Gold", "Red", "Fingerling"], "sizes": [(3, "lb"), (5, "lb"), (10, "lb")], "base_price": 0.70},
    {"item_key": "carrots", "display_name": "Carrots", "category": "Produce", "brands": ["", "Baby", "Organic"], "sizes": [(1, "lb"), (2, "lb"), (5, "lb")], "base_price": 1.00},
    {"item_key": "spinach", "display_name": "Spinach", "category": "Produce", "brands": ["Simple Truth", "Organic Girl", "Fresh Express", "Dole"], "sizes": [(5, "oz"), (10, "oz"), (16, "oz")], "base_price": 0.45},
    {"item_key": "cucumber", "display_name": "Cucumber", "category": "Produce", "brands": ["", "English", "Organic"], "sizes": [(1, "count"), (3, "count")], "base_price": 0.90},
    {"item_key": "strawberries", "display_name": "Strawberries", "category": "Produce", "brands": ["", "Driscoll's", "Organic"], "sizes": [(16, "oz"), (32, "oz")], "base_price": 0.22},
    {"item_key": "blueberries", "display_name": "Blueberries", "category": "Produce", "brands": ["", "Driscoll's", "Organic"], "sizes": [(6, "oz"), (18, "oz")], "base_price": 0.50},
    {"item_key": "grapes", "display_name": "Grapes", "category": "Produce", "brands": ["", "Red", "Green", "Cotton Candy"], "sizes": [(1, "lb"), (2, "lb"), (3, "lb")], "base_price": 2.50},
    {"item_key": "bagels", "display_name": "Bagels", "category": "Bakery", "brands": ["Thomas", "Kroger", "Great Value", "Dave's Killer"], "sizes": [(5, "count"), (6, "count")], "base_price": 0.60},
    {"item_key": "muffins", "display_name": "Muffins", "category": "Bakery", "brands": ["Kroger", "Great Value", "Otis Spunkmeyer"], "sizes": [(4, "count"), (6, "count")], "base_price": 0.75},
    {"item_key": "peanut butter", "display_name": "Peanut Butter", "category": "Pantry", "brands": ["Jif", "Skippy", "Kroger", "Great Value", "Peter Pan"], "sizes": [(16, "oz"), (28, "oz"), (40, "oz")], "base_price": 0.18},
    {"item_key": "jelly", "display_name": "Jelly", "category": "Pantry", "brands": ["Smucker's", "Kroger", "Great Value", "Welch's"], "sizes": [(18, "oz"), (30, "oz")], "base_price": 0.16},
    {"item_key": "flour", "display_name": "Flour", "category": "Baking", "brands": ["Gold Medal", "Kroger", "Great Value", "King Arthur", "Pillsbury"], "sizes": [(2, "lb"), (5, "lb"), (10, "lb")], "base_price": 0.40},
    {"item_key": "sugar", "display_name": "Sugar", "category": "Baking", "brands": ["Domino", "Kroger", "Great Value", "C&H"], "sizes": [(2, "lb"), (4, "lb"), (10, "lb")], "base_price": 0.50},
    {"item_key": "salt", "display_name": "Salt", "category": "Spices", "brands": ["Morton", "Kroger", "Himalayan Pink"], "sizes": [(26, "oz"), (48, "oz")], "base_price": 0.06},
    {"item_key": "black pepper", "display_name": "Black Pepper", "category": "Spices", "brands": ["McCormick", "Kroger", "Simply Organic"], "sizes": [(3, "oz"), (6, "oz")], "base_price": 1.20},
    {"item_key": "ketchup", "display_name": "Ketchup", "category": "Condiments", "brands": ["Heinz", "Hunt's", "Great Value", "French's"], "sizes": [(20, "oz"), (32, "oz"), (38, "oz")], "base_price": 0.12},
    {"item_key": "mustard", "display_name": "Mustard", "category": "Condiments", "brands": ["French's", "Grey Poupon", "Heinz", "Kroger"], "sizes": [(8, "oz"), (12, "oz"), (20, "oz")], "base_price": 0.14},
    {"item_key": "mayonnaise", "display_name": "Mayonnaise", "category": "Condiments", "brands": ["Hellmann's", "Duke's", "Kraft", "Great Value"], "sizes": [(15, "oz"), (30, "oz")], "base_price": 0.18},
    {"item_key": "soy sauce", "display_name": "Soy Sauce", "category": "Condiments", "brands": ["Kikkoman", "La Choy", "Kroger"], "sizes": [(10, "fl_oz"), (15, "fl_oz")], "base_price": 0.20},
    {"item_key": "hot sauce", "display_name": "Hot Sauce", "category": "Condiments", "brands": ["Frank's", "Tabasco", "Cholula", "Sriracha"], "sizes": [(5, "fl_oz"), (12, "fl_oz")], "base_price": 0.38},
    {"item_key": "salsa", "display_name": "Salsa", "category": "Condiments", "brands": ["Pace", "Tostitos", "Great Value", "Kroger"], "sizes": [(16, "oz"), (24, "oz")], "base_price": 0.16},
    {"item_key": "canned tomatoes", "display_name": "Canned Tomatoes", "category": "Canned", "brands": ["Hunt's", "Muir Glen", "Great Value", "Del Monte"], "sizes": [(14.5, "oz"), (28, "oz")], "base_price": 0.07},
    {"item_key": "canned beans", "display_name": "Canned Beans", "category": "Canned", "brands": ["Bush's", "Great Value", "Kroger", "Goya"], "sizes": [(15, "oz"), (28, "oz")], "base_price": 0.07},
    {"item_key": "canned tuna", "display_name": "Canned Tuna", "category": "Canned", "brands": ["StarKist", "Bumble Bee", "Kroger", "Great Value"], "sizes": [(5, "oz"), (12, "oz")], "base_price": 0.22},
    {"item_key": "canned soup", "display_name": "Canned Soup", "category": "Canned", "brands": ["Campbell's", "Progresso", "Kroger", "Great Value"], "sizes": [(10.75, "oz"), (18, "oz"), (22, "oz")], "base_price": 0.12},
    {"item_key": "pasta sauce", "display_name": "Pasta Sauce", "category": "Pantry", "brands": ["Prego", "Ragu", "Barilla", "Kroger", "Bertolli"], "sizes": [(24, "oz"), (32, "oz")], "base_price": 0.11},
    {"item_key": "maple syrup", "display_name": "Maple Syrup", "category": "Pantry", "brands": ["Mrs. Butterworth", "Log Cabin", "Kroger", "Great Value"], "sizes": [(12, "fl_oz"), (24, "fl_oz")], "base_price": 0.25},
    {"item_key": "honey", "display_name": "Honey", "category": "Pantry", "brands": ["Sue Bee", "Kroger", "Great Value", "Nature Nate's"], "sizes": [(12, "oz"), (24, "oz"), (32, "oz")], "base_price": 0.30},
    {"item_key": "oatmeal", "display_name": "Oatmeal", "category": "Breakfast", "brands": ["Quaker", "Kroger", "Great Value", "Bob's Red Mill"], "sizes": [(18, "oz"), (42, "oz")], "base_price": 0.10},
    {"item_key": "granola bars", "display_name": "Granola Bars", "category": "Snacks", "brands": ["Nature Valley", "Kind", "Quaker", "Kroger", "Great Value"], "sizes": [(6, "count"), (12, "count"), (24, "count")], "base_price": 0.42},
    {"item_key": "nuts", "display_name": "Mixed Nuts", "category": "Snacks", "brands": ["Planters", "Kroger", "Great Value", "Blue Diamond"], "sizes": [(8, "oz"), (16, "oz"), (26, "oz")], "base_price": 0.55},
    {"item_key": "trail mix", "display_name": "Trail Mix", "category": "Snacks", "brands": ["Planters", "Kroger", "Great Value", "Archer Farms"], "sizes": [(10, "oz"), (26, "oz")], "base_price": 0.38},
    {"item_key": "popcorn", "display_name": "Microwave Popcorn", "category": "Snacks", "brands": ["Orville Redenbacher", "Act II", "Kroger", "Pop Secret"], "sizes": [(3, "count"), (6, "count"), (12, "count")], "base_price": 0.75},
    {"item_key": "tortillas", "display_name": "Tortillas", "category": "Bakery", "brands": ["Mission", "Guerrero", "Kroger", "Great Value"], "sizes": [(10, "count"), (20, "count")], "base_price": 0.22},
    {"item_key": "tortilla chips", "display_name": "Tortilla Chips", "category": "Snacks", "brands": ["Tostitos", "Doritos", "Kroger", "Great Value", "Late July"], "sizes": [(10, "oz"), (13, "oz"), (16, "oz")], "base_price": 0.32},
    {"item_key": "hummus", "display_name": "Hummus", "category": "Deli", "brands": ["Sabra", "Cedar's", "Kroger", "Good & Gather"], "sizes": [(10, "oz"), (17, "oz")], "base_price": 0.36},
    {"item_key": "deli turkey", "display_name": "Deli Turkey", "category": "Deli", "brands": ["Oscar Mayer", "Hillshire", "Kroger", "Boar's Head"], "sizes": [(8, "oz"), (16, "oz")], "base_price": 0.55},
    {"item_key": "bacon", "display_name": "Bacon", "category": "Meat", "brands": ["Oscar Mayer", "Wright", "Kroger", "Great Value", "Hormel"], "sizes": [(12, "oz"), (16, "oz"), (24, "oz")], "base_price": 0.45},
    {"item_key": "sausage", "display_name": "Sausage", "category": "Meat", "brands": ["Johnsonville", "Jimmy Dean", "Kroger", "Great Value"], "sizes": [(12, "oz"), (16, "oz")], "base_price": 0.35},
    {"item_key": "hot dogs", "display_name": "Hot Dogs", "category": "Meat", "brands": ["Oscar Mayer", "Hebrew National", "Kroger", "Ball Park"], "sizes": [(8, "count"), (14, "count")], "base_price": 0.45},
    {"item_key": "ham", "display_name": "Sliced Ham", "category": "Deli", "brands": ["Smithfield", "Kroger", "Great Value", "Hillshire"], "sizes": [(8, "oz"), (16, "oz")], "base_price": 0.48},
    {"item_key": "cream cheese", "display_name": "Cream Cheese", "category": "Dairy", "brands": ["Philadelphia", "Kroger", "Great Value"], "sizes": [(8, "oz"), (16, "oz")], "base_price": 0.35},
    {"item_key": "sour cream", "display_name": "Sour Cream", "category": "Dairy", "brands": ["Daisy", "Kroger", "Great Value"], "sizes": [(8, "oz"), (16, "oz")], "base_price": 0.22},
    {"item_key": "almond milk", "display_name": "Almond Milk", "category": "Dairy", "brands": ["Silk", "Almond Breeze", "Kroger", "Great Value", "Califia"], "sizes": [(64, "fl_oz"), (96, "fl_oz")], "base_price": 0.05},
    {"item_key": "oat milk", "display_name": "Oat Milk", "category": "Dairy", "brands": ["Oatly", "Planet Oat", "Chobani", "Kroger", "Silk"], "sizes": [(64, "fl_oz")], "base_price": 0.06},
    {"item_key": "energy drink", "display_name": "Energy Drink", "category": "Beverages", "brands": ["Red Bull", "Monster", "Celsius", "Bang", "Reign"], "sizes": [(4, "count"), (12, "count")], "base_price": 2.00},
    {"item_key": "sports drink", "display_name": "Sports Drink", "category": "Beverages", "brands": ["Gatorade", "Powerade", "BodyArmor", "Kroger"], "sizes": [(8, "count"), (12, "count")], "base_price": 1.10},
    {"item_key": "protein bars", "display_name": "Protein Bars", "category": "Snacks", "brands": ["Clif", "Quest", "Kind", "RX Bar", "Pure Protein"], "sizes": [(5, "count"), (12, "count")], "base_price": 1.60},
    {"item_key": "vitamins", "display_name": "Multivitamin", "category": "Health", "brands": ["One A Day", "Centrum", "Kroger", "Nature Made"], "sizes": [(60, "count"), (100, "count"), (200, "count")], "base_price": 0.08},
    {"item_key": "bandages", "display_name": "Bandages", "category": "Health", "brands": ["Band-Aid", "Curad", "Kroger"], "sizes": [(25, "count"), (50, "count"), (100, "count")], "base_price": 0.08},
    {"item_key": "aluminum foil", "display_name": "Aluminum Foil", "category": "Household", "brands": ["Reynolds", "Kroger", "Great Value"], "sizes": [(75, "sqft"), (200, "sqft")], "base_price": 0.06},
    {"item_key": "plastic wrap", "display_name": "Plastic Wrap", "category": "Household", "brands": ["Saran", "Glad", "Kroger", "Great Value"], "sizes": [(200, "sqft"), (400, "sqft")], "base_price": 0.01},
    {"item_key": "trash bags", "display_name": "Trash Bags", "category": "Household", "brands": ["Glad", "Hefty", "Kroger", "Great Value"], "sizes": [(20, "count"), (40, "count"), (80, "count")], "base_price": 0.22},
    {"item_key": "ziplock bags", "display_name": "Ziplock Bags", "category": "Household", "brands": ["Ziploc", "Glad", "Kroger", "Great Value"], "sizes": [(24, "count"), (50, "count")], "base_price": 0.10},
    {"item_key": "cat food", "display_name": "Cat Food", "category": "Pet", "brands": ["Purina", "Meow Mix", "Fancy Feast", "Friskies", "Blue Buffalo"], "sizes": [(3, "lb"), (7, "lb"), (16, "lb")], "base_price": 1.20},
    {"item_key": "dog food", "display_name": "Dog Food", "category": "Pet", "brands": ["Purina", "Pedigree", "Blue Buffalo", "Iams", "Rachel Ray"], "sizes": [(4, "lb"), (15, "lb"), (30, "lb")], "base_price": 0.80},
    {"item_key": "baby wipes", "display_name": "Baby Wipes", "category": "Baby", "brands": ["Huggies", "Pampers", "Kroger", "Great Value"], "sizes": [(72, "count"), (168, "count"), (400, "count")], "base_price": 0.02},
    {"item_key": "diapers", "display_name": "Diapers", "category": "Baby", "brands": ["Huggies", "Pampers", "Kroger", "Luvs"], "sizes": [(24, "count"), (52, "count"), (96, "count")], "base_price": 0.25},
    {"item_key": "baby formula", "display_name": "Baby Formula", "category": "Baby", "brands": ["Enfamil", "Similac", "Kroger", "Earth's Best"], "sizes": [(12.5, "oz"), (23.2, "oz"), (30.4, "oz")], "base_price": 1.10},
    {"item_key": "batteries", "display_name": "Batteries AA", "category": "Household", "brands": ["Energizer", "Duracell", "Kroger", "Great Value"], "sizes": [(4, "count"), (8, "count"), (24, "count")], "base_price": 0.45},
    {"item_key": "light bulbs", "display_name": "LED Light Bulbs", "category": "Household", "brands": ["GE", "Philips", "Kroger", "Great Value"], "sizes": [(4, "count"), (8, "count")], "base_price": 1.60},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def jitter(lat: float, lon: float, rng: random.Random, spread: float = 0.08) -> tuple[float, float]:
    return (
        round(lat + rng.uniform(-spread, spread), 6),
        round(lon + rng.uniform(-spread, spread), 6),
    )


def format_item_name(brand: str, display_name: str, package_size: float, package_unit: str) -> str:
    size_text = f"{package_size:g} {package_unit}"
    if brand:
        return f"{brand} {display_name} {size_text}"
    return f"{display_name} {size_text}"


def vendor_brand_adjustment(vendor: str, brands: list[str], rng: random.Random) -> list[str]:
    if vendor == "costco":
        return ["Kirkland"] + brands[:2]
    if vendor == "traderjoes":
        return ["Trader Joe's"] + brands[:2]
    if vendor == "aldis":
        return ["Simply Nature", "Specially Selected"] + brands[:1]
    if vendor == "meijer":
        return ["Meijer", "True Goodness"] + brands[:2]
    if vendor == "publix":
        return ["Publix", "GreenWise"] + brands[:2]
    if vendor == "heb":
        return ["H-E-B", "Hill Country Fare"] + brands[:2]
    if vendor == "safeway":
        return ["Signature Select", "O Organics"] + brands[:2]
    return brands


def build_products_for_store(store: dict, count: int, rng: random.Random, id_offset: int) -> list[dict]:
    products: list[dict] = []
    catalog = ITEM_CATALOG

    for i in range(count):
        item = catalog[i % len(catalog)] if i < len(catalog) else rng.choice(catalog)
        adjusted_brands = vendor_brand_adjustment(store["vendor"], item["brands"], rng)
        brand = rng.choice(adjusted_brands)
        package_size, package_unit = rng.choice(item["sizes"])

        base = item.get("base_price", 1.0)
        price = max(0.49, package_size * base * rng.uniform(0.8, 1.5))

        # Vendor price adjustments
        v = store["vendor"]
        if v == "costco":
            price *= 1.4
            package_size *= 2 if package_unit in {"count", "oz", "fl_oz"} else 1.5
        elif v == "traderjoes":
            price *= 1.05
        elif v in ("walmart", "aldis"):
            price *= 0.93
        elif v == "heb":
            price *= 0.95

        products.append({
            "product_id": f"{store['store_id']}-p{id_offset + i + 1:06d}",
            "store_id": store["store_id"],
            "vendor": store["vendor"],
            "item_key": item["item_key"],
            "item_name": format_item_name(brand, item["display_name"], round(package_size, 2), package_unit),
            "brand": brand,
            "package_size": round(package_size, 2),
            "package_unit": package_unit,
            "price": round(price, 2),
            "match_score": round(rng.uniform(0.82, 1.0), 3),
            "in_stock": rng.random() > 0.07,
            "last_updated": datetime.utcnow(),
        })

    return products


# ---------------------------------------------------------------------------
# Main seeder
# ---------------------------------------------------------------------------

async def seed_expansion():
    await connect_db()
    db = get_db()

    rng = random.Random(RNG_SEED)
    vendors = list(VENDOR_CONFIG.keys())
    global_product_offset = 0
    total_stores_inserted = 0
    total_products_inserted = 0

    # ── Phase 1: Toledo cluster (20 stores, 100k products) ──
    print("=" * 60)
    print("Phase 1: Seeding 20 Toledo-area stores with 100k products...")
    print("=" * 60)

    toledo_stores: list[dict] = []
    for i in range(TOLEDO_STORE_COUNT):
        vendor = vendors[i % len(vendors)]
        center = TOLEDO_CENTERS[i % len(TOLEDO_CENTERS)]
        city_name, zip_code, base_lat, base_lon = center
        lat, lon = jitter(base_lat, base_lon, rng, spread=0.05)
        vmeta = VENDOR_CONFIG[vendor]

        toledo_stores.append({
            "store_id": f"{vendor}-toledo-{i + 1:04d}",
            "vendor": vendor,
            "name": f"{vmeta['name_prefix']} {city_name} #{i + 1}",
            "address": f"{100 + rng.randint(0, 9000)} {city_name} Blvd",
            "zip_code": zip_code,
            "latitude": lat,
            "longitude": lon,
            "open_time": vmeta["open_time"],
            "close_time": vmeta["close_time"],
            "visit_penalty_minutes": vmeta["visit_penalty_minutes"],
            "is_active": True,
        })

    await db.stores.insert_many(toledo_stores)
    total_stores_inserted += len(toledo_stores)
    print(f"  Inserted {len(toledo_stores)} Toledo stores")

    product_buffer: list[dict] = []
    for store in toledo_stores:
        products = build_products_for_store(store, TOLEDO_PRODUCTS_PER_STORE, rng, global_product_offset)
        global_product_offset += len(products)
        product_buffer.extend(products)

        while len(product_buffer) >= BATCH_SIZE:
            batch = product_buffer[:BATCH_SIZE]
            product_buffer = product_buffer[BATCH_SIZE:]
            await db.products.insert_many(batch)
            total_products_inserted += len(batch)
            print(f"  Products batch inserted: {total_products_inserted:,} total so far")

    if product_buffer:
        await db.products.insert_many(product_buffer)
        total_products_inserted += len(product_buffer)
        product_buffer = []
        print(f"  Toledo products done: {total_products_inserted:,} total")

    # ── Phase 2: General US stores (6980 stores, ~800k products) ──
    print()
    print("=" * 60)
    print(f"Phase 2: Seeding {GENERAL_STORE_COUNT} US stores with ~{GENERAL_STORE_COUNT * GENERAL_PRODUCTS_PER_STORE:,} products...")
    print("=" * 60)

    store_buffer: list[dict] = []

    for i in range(GENERAL_STORE_COUNT):
        vendor = vendors[i % len(vendors)]
        center = US_AREA_CENTERS[i % len(US_AREA_CENTERS)]
        city_name, zip_code, base_lat, base_lon = center
        lat, lon = jitter(base_lat, base_lon, rng, spread=0.12)
        vmeta = VENDOR_CONFIG[vendor]

        store_buffer.append({
            "store_id": f"{vendor}-us-{i + 1:05d}",
            "vendor": vendor,
            "name": f"{vmeta['name_prefix']} {city_name} #{i + 1}",
            "address": f"{100 + rng.randint(0, 9000)} {city_name} St",
            "zip_code": zip_code,
            "latitude": lat,
            "longitude": lon,
            "open_time": vmeta["open_time"],
            "close_time": vmeta["close_time"],
            "visit_penalty_minutes": vmeta["visit_penalty_minutes"],
            "is_active": True,
        })

    # Insert stores in batches
    for s in range(0, len(store_buffer), 2000):
        batch = store_buffer[s:s + 2000]
        await db.stores.insert_many(batch)
        total_stores_inserted += len(batch)
        print(f"  Stores inserted: {total_stores_inserted:,}")

    # Insert products for general stores
    product_buffer = []
    for si, store in enumerate(store_buffer):
        products = build_products_for_store(store, GENERAL_PRODUCTS_PER_STORE, rng, global_product_offset)
        global_product_offset += len(products)
        product_buffer.extend(products)

        while len(product_buffer) >= BATCH_SIZE:
            batch = product_buffer[:BATCH_SIZE]
            product_buffer = product_buffer[BATCH_SIZE:]
            await db.products.insert_many(batch)
            total_products_inserted += len(batch)
            if total_products_inserted % 50_000 < BATCH_SIZE:
                print(f"  Products: {total_products_inserted:,} total")

    if product_buffer:
        await db.products.insert_many(product_buffer)
        total_products_inserted += len(product_buffer)

    # ── Summary ──
    print()
    print("=" * 60)
    print("Expansion seed complete!")
    print(f"  New stores:   {total_stores_inserted:,}")
    print(f"  New products: {total_products_inserted:,}")
    print()

    existing_stores = await db.stores.count_documents({})
    existing_products = await db.products.count_documents({})
    print(f"  Total stores in DB:   {existing_stores:,}")
    print(f"  Total products in DB: {existing_products:,}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_expansion())
import asyncio
import random
from datetime import datetime, timedelta
from app.db import connect_db, get_db

random.seed(42)

# Real US store chains with multiple locations
STORE_CHAINS = {
    "walmart": {"name": "Walmart Supercenter", "rating_range": (3.4, 4.0), "price_factor": 0.92},
    "kroger": {"name": "Kroger", "rating_range": (3.6, 4.2), "price_factor": 0.95},
    "costco": {"name": "Costco Wholesale", "rating_range": (4.2, 4.6), "price_factor": 0.85},
    "traderjoes": {"name": "Trader Joe's", "rating_range": (4.3, 4.7), "price_factor": 1.0},
    "target": {"name": "Target", "rating_range": (3.8, 4.3), "price_factor": 1.05},
    "aldi": {"name": "ALDI", "rating_range": (4.0, 4.5), "price_factor": 0.88},
    "publix": {"name": "Publix", "rating_range": (4.3, 4.7), "price_factor": 1.10},
    "heb": {"name": "H-E-B", "rating_range": (4.4, 4.8), "price_factor": 0.93},
    "safeway": {"name": "Safeway", "rating_range": (3.5, 4.1), "price_factor": 1.02},
    "wholefoods": {"name": "Whole Foods Market", "rating_range": (4.0, 4.5), "price_factor": 1.25},
}

LOCATIONS = [
    {"city": "Mountain View", "state": "CA", "zip": "94040", "lat": 37.3861, "lng": -122.0839},
    {"city": "Palo Alto", "state": "CA", "zip": "94301", "lat": 37.4419, "lng": -122.1430},
    {"city": "Sunnyvale", "state": "CA", "zip": "94086", "lat": 37.3688, "lng": -122.0363},
    {"city": "San Jose", "state": "CA", "zip": "95112", "lat": 37.3382, "lng": -121.8863},
    {"city": "Cupertino", "state": "CA", "zip": "95014", "lat": 37.3230, "lng": -122.0322},
    {"city": "Santa Clara", "state": "CA", "zip": "95050", "lat": 37.3541, "lng": -121.9552},
    {"city": "Fremont", "state": "CA", "zip": "94536", "lat": 37.5485, "lng": -121.9886},
    {"city": "Redwood City", "state": "CA", "zip": "94063", "lat": 37.4852, "lng": -122.2364},
    {"city": "Milpitas", "state": "CA", "zip": "95035", "lat": 37.4323, "lng": -121.8996},
    {"city": "Newark", "state": "CA", "zip": "94560", "lat": 37.5297, "lng": -122.0402},
    {"city": "San Francisco", "state": "CA", "zip": "94102", "lat": 37.7749, "lng": -122.4194},
    {"city": "Oakland", "state": "CA", "zip": "94612", "lat": 37.8044, "lng": -122.2712},
    {"city": "Berkeley", "state": "CA", "zip": "94704", "lat": 37.8716, "lng": -122.2727},
    {"city": "Hayward", "state": "CA", "zip": "94541", "lat": 37.6688, "lng": -122.0808},
    {"city": "San Mateo", "state": "CA", "zip": "94401", "lat": 37.5630, "lng": -122.3255},
    {"city": "Daly City", "state": "CA", "zip": "94015", "lat": 37.6879, "lng": -122.4702},
    {"city": "Concord", "state": "CA", "zip": "94520", "lat": 37.9780, "lng": -122.0311},
    {"city": "Walnut Creek", "state": "CA", "zip": "94596", "lat": 37.9101, "lng": -122.0652},
    {"city": "Pleasanton", "state": "CA", "zip": "94566", "lat": 37.6624, "lng": -121.8747},
    {"city": "Dublin", "state": "CA", "zip": "94568", "lat": 37.7022, "lng": -121.9358},
    {"city": "Livermore", "state": "CA", "zip": "94550", "lat": 37.6819, "lng": -121.7680},
    {"city": "Union City", "state": "CA", "zip": "94587", "lat": 37.5934, "lng": -122.0439},
    {"city": "San Leandro", "state": "CA", "zip": "94577", "lat": 37.7249, "lng": -122.1561},
    {"city": "Alameda", "state": "CA", "zip": "94501", "lat": 37.7652, "lng": -122.2416},
    {"city": "Campbell", "state": "CA", "zip": "95008", "lat": 37.2872, "lng": -121.9500},
    {"city": "Los Gatos", "state": "CA", "zip": "95030", "lat": 37.2358, "lng": -121.9624},
    {"city": "Saratoga", "state": "CA", "zip": "95070", "lat": 37.2638, "lng": -122.0230},
    {"city": "Morgan Hill", "state": "CA", "zip": "95037", "lat": 37.1305, "lng": -121.6544},
    {"city": "Gilroy", "state": "CA", "zip": "95020", "lat": 37.0058, "lng": -121.5683},
    {"city": "Foster City", "state": "CA", "zip": "94404", "lat": 37.5585, "lng": -122.2711},
]

# Realistic product catalog with USDA-based price ranges
PRODUCT_CATALOG = [
    # DAIRY
    {"generic": "milk", "category": "Dairy", "variants": [
        {"name": "Whole Milk 1 Gallon", "size": 128, "unit": "fl_oz", "base_price": 3.69},
        {"name": "2% Reduced Fat Milk 1 Gallon", "size": 128, "unit": "fl_oz", "base_price": 3.59},
        {"name": "Skim Milk 1 Gallon", "size": 128, "unit": "fl_oz", "base_price": 3.49},
        {"name": "Whole Milk Half Gallon", "size": 64, "unit": "fl_oz", "base_price": 2.49},
        {"name": "Organic Whole Milk 1 Gallon", "size": 128, "unit": "fl_oz", "base_price": 5.99},
        {"name": "Oat Milk 64oz", "size": 64, "unit": "fl_oz", "base_price": 4.29},
        {"name": "Almond Milk 64oz", "size": 64, "unit": "fl_oz", "base_price": 3.49},
    ]},
    {"generic": "eggs", "category": "Dairy", "variants": [
        {"name": "Large Eggs 12ct", "size": 12, "unit": "count", "base_price": 3.29},
        {"name": "Large Eggs 18ct", "size": 18, "unit": "count", "base_price": 4.59},
        {"name": "Large Eggs 36ct", "size": 36, "unit": "count", "base_price": 7.99},
        {"name": "Organic Free Range Eggs 12ct", "size": 12, "unit": "count", "base_price": 5.49},
        {"name": "Cage Free Eggs 12ct", "size": 12, "unit": "count", "base_price": 4.29},
        {"name": "Egg Whites 16oz", "size": 16, "unit": "fl_oz", "base_price": 3.99},
    ]},
    {"generic": "butter", "category": "Dairy", "variants": [
        {"name": "Salted Butter 1lb", "size": 16, "unit": "oz", "base_price": 4.49},
        {"name": "Unsalted Butter 1lb", "size": 16, "unit": "oz", "base_price": 4.49},
        {"name": "Organic Butter 1lb", "size": 16, "unit": "oz", "base_price": 6.29},
    ]},
    {"generic": "cheese", "category": "Dairy", "variants": [
        {"name": "Cheddar Cheese Block 8oz", "size": 8, "unit": "oz", "base_price": 3.49},
        {"name": "Shredded Mozzarella 8oz", "size": 8, "unit": "oz", "base_price": 3.29},
        {"name": "American Cheese Slices 16ct", "size": 16, "unit": "count", "base_price": 3.99},
        {"name": "Cream Cheese 8oz", "size": 8, "unit": "oz", "base_price": 2.49},
        {"name": "Parmesan Cheese Grated 8oz", "size": 8, "unit": "oz", "base_price": 4.99},
        {"name": "Swiss Cheese Slices 8oz", "size": 8, "unit": "oz", "base_price": 3.99},
    ]},
    {"generic": "yogurt", "category": "Dairy", "variants": [
        {"name": "Greek Yogurt Plain 32oz", "size": 32, "unit": "oz", "base_price": 4.99},
        {"name": "Greek Yogurt Vanilla 5.3oz", "size": 5.3, "unit": "oz", "base_price": 1.29},
        {"name": "Yogurt Strawberry 6oz", "size": 6, "unit": "oz", "base_price": 0.89},
        {"name": "Yogurt Variety Pack 12ct", "size": 12, "unit": "count", "base_price": 6.99},
    ]},
    # BREAD & BAKERY
    {"generic": "bread", "category": "Bakery", "variants": [
        {"name": "White Bread 20oz", "size": 20, "unit": "oz", "base_price": 2.79},
        {"name": "Whole Wheat Bread 20oz", "size": 20, "unit": "oz", "base_price": 3.29},
        {"name": "Sourdough Bread 24oz", "size": 24, "unit": "oz", "base_price": 3.99},
        {"name": "Multigrain Bread 22oz", "size": 22, "unit": "oz", "base_price": 3.49},
        {"name": "Brioche Bread 15oz", "size": 15, "unit": "oz", "base_price": 4.49},
    ]},
    {"generic": "bagels", "category": "Bakery", "variants": [
        {"name": "Plain Bagels 6ct", "size": 6, "unit": "count", "base_price": 3.49},
        {"name": "Everything Bagels 6ct", "size": 6, "unit": "count", "base_price": 3.49},
        {"name": "Blueberry Bagels 6ct", "size": 6, "unit": "count", "base_price": 3.79},
    ]},
    {"generic": "tortillas", "category": "Bakery", "variants": [
        {"name": "Flour Tortillas 10ct", "size": 10, "unit": "count", "base_price": 2.99},
        {"name": "Corn Tortillas 30ct", "size": 30, "unit": "count", "base_price": 2.49},
        {"name": "Whole Wheat Tortillas 8ct", "size": 8, "unit": "count", "base_price": 3.29},
    ]},
    # GRAINS & PASTA
    {"generic": "rice", "category": "Grains", "variants": [
        {"name": "Long Grain White Rice 5lb", "size": 5, "unit": "lb", "base_price": 4.29},
        {"name": "Jasmine Rice 5lb", "size": 5, "unit": "lb", "base_price": 5.49},
        {"name": "Brown Rice 2lb", "size": 2, "unit": "lb", "base_price": 2.99},
        {"name": "Basmati Rice 5lb", "size": 5, "unit": "lb", "base_price": 6.49},
        {"name": "Long Grain White Rice 10lb", "size": 10, "unit": "lb", "base_price": 7.99},
        {"name": "Jasmine Rice 25lb", "size": 25, "unit": "lb", "base_price": 18.99},
        {"name": "Instant Rice 14oz", "size": 14, "unit": "oz", "base_price": 2.49},
    ]},
    {"generic": "pasta", "category": "Grains", "variants": [
        {"name": "Spaghetti 16oz", "size": 16, "unit": "oz", "base_price": 1.49},
        {"name": "Penne 16oz", "size": 16, "unit": "oz", "base_price": 1.49},
        {"name": "Macaroni 16oz", "size": 16, "unit": "oz", "base_price": 1.29},
        {"name": "Fettuccine 16oz", "size": 16, "unit": "oz", "base_price": 1.49},
        {"name": "Angel Hair 16oz", "size": 16, "unit": "oz", "base_price": 1.49},
        {"name": "Whole Wheat Spaghetti 16oz", "size": 16, "unit": "oz", "base_price": 1.99},
        {"name": "Lasagna Sheets 16oz", "size": 16, "unit": "oz", "base_price": 2.29},
        {"name": "Rotini 16oz", "size": 16, "unit": "oz", "base_price": 1.49},
    ]},
    {"generic": "cereal", "category": "Breakfast", "variants": [
        {"name": "Toasted Oats 18oz", "size": 18, "unit": "oz", "base_price": 4.29},
        {"name": "Corn Flakes 18oz", "size": 18, "unit": "oz", "base_price": 3.99},
        {"name": "Frosted Flakes 13.5oz", "size": 13.5, "unit": "oz", "base_price": 4.49},
        {"name": "Granola 16oz", "size": 16, "unit": "oz", "base_price": 4.99},
        {"name": "Raisin Bran 18.7oz", "size": 18.7, "unit": "oz", "base_price": 4.29},
        {"name": "Honey Nut Oats 15.4oz", "size": 15.4, "unit": "oz", "base_price": 4.49},
    ]},
    {"generic": "oatmeal", "category": "Breakfast", "variants": [
        {"name": "Old Fashioned Oats 42oz", "size": 42, "unit": "oz", "base_price": 4.49},
        {"name": "Instant Oatmeal Variety 10ct", "size": 10, "unit": "count", "base_price": 3.49},
        {"name": "Steel Cut Oats 24oz", "size": 24, "unit": "oz", "base_price": 3.99},
    ]},
    # MEAT & PROTEIN
    {"generic": "chicken breast", "category": "Meat", "variants": [
        {"name": "Boneless Skinless Chicken Breast 2.5lb", "size": 2.5, "unit": "lb", "base_price": 8.99},
        {"name": "Boneless Skinless Chicken Breast 3lb", "size": 3, "unit": "lb", "base_price": 10.49},
        {"name": "Organic Chicken Breast 1.5lb", "size": 1.5, "unit": "lb", "base_price": 8.99},
        {"name": "Chicken Breast Tenderloins 2.5lb", "size": 2.5, "unit": "lb", "base_price": 9.49},
    ]},
    {"generic": "ground beef", "category": "Meat", "variants": [
        {"name": "Ground Beef 80/20 1lb", "size": 1, "unit": "lb", "base_price": 5.49},
        {"name": "Ground Beef 90/10 1lb", "size": 1, "unit": "lb", "base_price": 6.49},
        {"name": "Ground Beef 93/7 1lb", "size": 1, "unit": "lb", "base_price": 7.29},
        {"name": "Organic Ground Beef 1lb", "size": 1, "unit": "lb", "base_price": 8.99},
        {"name": "Ground Beef 80/20 3lb", "size": 3, "unit": "lb", "base_price": 14.99},
    ]},
    {"generic": "chicken thighs", "category": "Meat", "variants": [
        {"name": "Bone-In Chicken Thighs 3lb", "size": 3, "unit": "lb", "base_price": 5.99},
        {"name": "Boneless Chicken Thighs 2lb", "size": 2, "unit": "lb", "base_price": 6.99},
    ]},
    {"generic": "pork chops", "category": "Meat", "variants": [
        {"name": "Bone-In Pork Chops 2lb", "size": 2, "unit": "lb", "base_price": 6.49},
        {"name": "Boneless Pork Chops 1.5lb", "size": 1.5, "unit": "lb", "base_price": 5.99},
    ]},
    {"generic": "bacon", "category": "Meat", "variants": [
        {"name": "Bacon Regular 16oz", "size": 16, "unit": "oz", "base_price": 6.49},
        {"name": "Turkey Bacon 12oz", "size": 12, "unit": "oz", "base_price": 4.49},
        {"name": "Center Cut Bacon 12oz", "size": 12, "unit": "oz", "base_price": 5.99},
    ]},
    {"generic": "salmon", "category": "Seafood", "variants": [
        {"name": "Atlantic Salmon Fillets 1lb", "size": 1, "unit": "lb", "base_price": 9.99},
        {"name": "Wild Caught Salmon 1lb", "size": 1, "unit": "lb", "base_price": 12.99},
        {"name": "Salmon Portions 1.25lb", "size": 1.25, "unit": "lb", "base_price": 11.99},
    ]},
    {"generic": "shrimp", "category": "Seafood", "variants": [
        {"name": "Raw Shrimp 16/20ct 1lb", "size": 1, "unit": "lb", "base_price": 8.99},
        {"name": "Cooked Shrimp 26/30ct 1lb", "size": 1, "unit": "lb", "base_price": 9.99},
        {"name": "Raw Shrimp 2lb Bag", "size": 2, "unit": "lb", "base_price": 14.99},
    ]},
    {"generic": "tofu", "category": "Protein", "variants": [
        {"name": "Extra Firm Tofu 14oz", "size": 14, "unit": "oz", "base_price": 2.29},
        {"name": "Silken Tofu 12oz", "size": 12, "unit": "oz", "base_price": 1.99},
        {"name": "Organic Firm Tofu 14oz", "size": 14, "unit": "oz", "base_price": 2.99},
    ]},
    # PRODUCE
    {"generic": "bananas", "category": "Produce", "variants": [
        {"name": "Bananas per lb", "size": 1, "unit": "lb", "base_price": 0.65},
        {"name": "Organic Bananas per lb", "size": 1, "unit": "lb", "base_price": 0.79},
    ]},
    {"generic": "apples", "category": "Produce", "variants": [
        {"name": "Gala Apples per lb", "size": 1, "unit": "lb", "base_price": 1.69},
        {"name": "Fuji Apples per lb", "size": 1, "unit": "lb", "base_price": 1.79},
        {"name": "Honeycrisp Apples per lb", "size": 1, "unit": "lb", "base_price": 2.99},
        {"name": "Granny Smith Apples per lb", "size": 1, "unit": "lb", "base_price": 1.59},
        {"name": "Organic Gala Apples per lb", "size": 1, "unit": "lb", "base_price": 2.49},
    ]},
    {"generic": "tomatoes", "category": "Produce", "variants": [
        {"name": "Roma Tomatoes per lb", "size": 1, "unit": "lb", "base_price": 1.49},
        {"name": "Cherry Tomatoes 10oz", "size": 10, "unit": "oz", "base_price": 2.99},
        {"name": "Vine Tomatoes per lb", "size": 1, "unit": "lb", "base_price": 1.99},
        {"name": "Organic Tomatoes per lb", "size": 1, "unit": "lb", "base_price": 2.99},
    ]},
    {"generic": "potatoes", "category": "Produce", "variants": [
        {"name": "Russet Potatoes 5lb", "size": 5, "unit": "lb", "base_price": 3.99},
        {"name": "Red Potatoes 3lb", "size": 3, "unit": "lb", "base_price": 3.49},
        {"name": "Gold Potatoes 3lb", "size": 3, "unit": "lb", "base_price": 3.49},
        {"name": "Sweet Potatoes per lb", "size": 1, "unit": "lb", "base_price": 1.29},
        {"name": "Russet Potatoes 10lb", "size": 10, "unit": "lb", "base_price": 6.49},
    ]},
    {"generic": "onions", "category": "Produce", "variants": [
        {"name": "Yellow Onions 3lb", "size": 3, "unit": "lb", "base_price": 2.49},
        {"name": "Red Onions per lb", "size": 1, "unit": "lb", "base_price": 1.29},
        {"name": "White Onions per lb", "size": 1, "unit": "lb", "base_price": 1.19},
        {"name": "Green Onions Bunch", "size": 1, "unit": "count", "base_price": 0.99},
    ]},
    {"generic": "lettuce", "category": "Produce", "variants": [
        {"name": "Iceberg Lettuce Head", "size": 1, "unit": "count", "base_price": 1.49},
        {"name": "Romaine Hearts 3ct", "size": 3, "unit": "count", "base_price": 2.99},
        {"name": "Spring Mix 5oz", "size": 5, "unit": "oz", "base_price": 3.49},
        {"name": "Baby Spinach 5oz", "size": 5, "unit": "oz", "base_price": 3.49},
    ]},
    {"generic": "avocados", "category": "Produce", "variants": [
        {"name": "Hass Avocados Each", "size": 1, "unit": "count", "base_price": 1.25},
        {"name": "Hass Avocados 4ct Bag", "size": 4, "unit": "count", "base_price": 3.99},
        {"name": "Organic Avocados Each", "size": 1, "unit": "count", "base_price": 1.79},
    ]},
    {"generic": "carrots", "category": "Produce", "variants": [
        {"name": "Carrots 2lb Bag", "size": 2, "unit": "lb", "base_price": 1.99},
        {"name": "Baby Carrots 1lb", "size": 1, "unit": "lb", "base_price": 1.99},
        {"name": "Organic Carrots 2lb", "size": 2, "unit": "lb", "base_price": 2.49},
    ]},
    {"generic": "bell peppers", "category": "Produce", "variants": [
        {"name": "Green Bell Pepper Each", "size": 1, "unit": "count", "base_price": 0.99},
        {"name": "Red Bell Pepper Each", "size": 1, "unit": "count", "base_price": 1.49},
        {"name": "Bell Pepper 3ct Pack", "size": 3, "unit": "count", "base_price": 3.49},
    ]},
    {"generic": "cucumbers", "category": "Produce", "variants": [
        {"name": "Cucumber Each", "size": 1, "unit": "count", "base_price": 0.79},
        {"name": "English Cucumber Each", "size": 1, "unit": "count", "base_price": 1.49},
        {"name": "Mini Cucumbers 1lb", "size": 1, "unit": "lb", "base_price": 2.99},
    ]},
    {"generic": "strawberries", "category": "Produce", "variants": [
        {"name": "Strawberries 1lb", "size": 1, "unit": "lb", "base_price": 3.49},
        {"name": "Organic Strawberries 1lb", "size": 1, "unit": "lb", "base_price": 4.99},
        {"name": "Strawberries 2lb", "size": 2, "unit": "lb", "base_price": 5.99},
    ]},
    {"generic": "blueberries", "category": "Produce", "variants": [
        {"name": "Blueberries 6oz", "size": 6, "unit": "oz", "base_price": 3.49},
        {"name": "Organic Blueberries 6oz", "size": 6, "unit": "oz", "base_price": 4.99},
        {"name": "Blueberries 18oz", "size": 18, "unit": "oz", "base_price": 6.99},
    ]},
    {"generic": "grapes", "category": "Produce", "variants": [
        {"name": "Red Grapes per lb", "size": 1, "unit": "lb", "base_price": 2.49},
        {"name": "Green Grapes per lb", "size": 1, "unit": "lb", "base_price": 2.49},
        {"name": "Cotton Candy Grapes per lb", "size": 1, "unit": "lb", "base_price": 3.99},
    ]},
    {"generic": "oranges", "category": "Produce", "variants": [
        {"name": "Navel Oranges per lb", "size": 1, "unit": "lb", "base_price": 1.49},
        {"name": "Navel Oranges 4lb Bag", "size": 4, "unit": "lb", "base_price": 4.99},
        {"name": "Mandarins 3lb Bag", "size": 3, "unit": "lb", "base_price": 4.99},
    ]},
    {"generic": "lemons", "category": "Produce", "variants": [
        {"name": "Lemons Each", "size": 1, "unit": "count", "base_price": 0.59},
        {"name": "Lemons 2lb Bag", "size": 2, "unit": "lb", "base_price": 2.99},
    ]},
    # COOKING & CONDIMENTS
    {"generic": "olive oil", "category": "Cooking", "variants": [
        {"name": "Extra Virgin Olive Oil 17oz", "size": 17, "unit": "fl_oz", "base_price": 6.49},
        {"name": "Extra Virgin Olive Oil 25.5oz", "size": 25.5, "unit": "fl_oz", "base_price": 8.99},
        {"name": "Organic Extra Virgin Olive Oil 17oz", "size": 17, "unit": "fl_oz", "base_price": 8.49},
        {"name": "Light Olive Oil 17oz", "size": 17, "unit": "fl_oz", "base_price": 5.99},
    ]},
    {"generic": "vegetable oil", "category": "Cooking", "variants": [
        {"name": "Vegetable Oil 48oz", "size": 48, "unit": "fl_oz", "base_price": 4.29},
        {"name": "Canola Oil 48oz", "size": 48, "unit": "fl_oz", "base_price": 4.49},
        {"name": "Coconut Oil 14oz", "size": 14, "unit": "fl_oz", "base_price": 5.99},
    ]},
    {"generic": "ketchup", "category": "Condiments", "variants": [
        {"name": "Ketchup 20oz", "size": 20, "unit": "oz", "base_price": 2.99},
        {"name": "Ketchup 38oz", "size": 38, "unit": "oz", "base_price": 4.49},
        {"name": "Organic Ketchup 20oz", "size": 20, "unit": "oz", "base_price": 3.99},
    ]},
    {"generic": "mustard", "category": "Condiments", "variants": [
        {"name": "Yellow Mustard 14oz", "size": 14, "unit": "oz", "base_price": 1.49},
        {"name": "Dijon Mustard 12oz", "size": 12, "unit": "oz", "base_price": 3.29},
        {"name": "Honey Mustard 12oz", "size": 12, "unit": "oz", "base_price": 2.99},
    ]},
    {"generic": "mayonnaise", "category": "Condiments", "variants": [
        {"name": "Mayonnaise 30oz", "size": 30, "unit": "oz", "base_price": 4.99},
        {"name": "Light Mayonnaise 30oz", "size": 30, "unit": "oz", "base_price": 4.99},
        {"name": "Avocado Oil Mayo 12oz", "size": 12, "unit": "oz", "base_price": 5.49},
    ]},
    {"generic": "soy sauce", "category": "Condiments", "variants": [
        {"name": "Soy Sauce 15oz", "size": 15, "unit": "fl_oz", "base_price": 2.99},
        {"name": "Low Sodium Soy Sauce 15oz", "size": 15, "unit": "fl_oz", "base_price": 3.29},
    ]},
    {"generic": "hot sauce", "category": "Condiments", "variants": [
        {"name": "Hot Sauce 5oz", "size": 5, "unit": "fl_oz", "base_price": 1.99},
        {"name": "Sriracha 17oz", "size": 17, "unit": "fl_oz", "base_price": 3.49},
    ]},
    {"generic": "pasta sauce", "category": "Condiments", "variants": [
        {"name": "Marinara Sauce 24oz", "size": 24, "unit": "oz", "base_price": 2.99},
        {"name": "Tomato Basil Sauce 24oz", "size": 24, "unit": "oz", "base_price": 3.29},
        {"name": "Alfredo Sauce 15oz", "size": 15, "unit": "oz", "base_price": 2.99},
        {"name": "Organic Marinara 25oz", "size": 25, "unit": "oz", "base_price": 4.49},
    ]},
    {"generic": "salad dressing", "category": "Condiments", "variants": [
        {"name": "Ranch Dressing 16oz", "size": 16, "unit": "fl_oz", "base_price": 3.49},
        {"name": "Italian Dressing 16oz", "size": 16, "unit": "fl_oz", "base_price": 2.99},
        {"name": "Caesar Dressing 12oz", "size": 12, "unit": "fl_oz", "base_price": 3.29},
        {"name": "Balsamic Vinaigrette 16oz", "size": 16, "unit": "fl_oz", "base_price": 3.49},
    ]},
    # CANNED & PANTRY
    {"generic": "canned tomatoes", "category": "Canned", "variants": [
        {"name": "Diced Tomatoes 14.5oz", "size": 14.5, "unit": "oz", "base_price": 1.29},
        {"name": "Crushed Tomatoes 28oz", "size": 28, "unit": "oz", "base_price": 1.99},
        {"name": "Tomato Paste 6oz", "size": 6, "unit": "oz", "base_price": 0.99},
        {"name": "Whole Peeled Tomatoes 28oz", "size": 28, "unit": "oz", "base_price": 2.29},
    ]},
    {"generic": "canned beans", "category": "Canned", "variants": [
        {"name": "Black Beans 15oz", "size": 15, "unit": "oz", "base_price": 1.09},
        {"name": "Kidney Beans 15oz", "size": 15, "unit": "oz", "base_price": 1.09},
        {"name": "Chickpeas 15oz", "size": 15, "unit": "oz", "base_price": 1.09},
        {"name": "Pinto Beans 15oz", "size": 15, "unit": "oz", "base_price": 1.09},
        {"name": "Refried Beans 16oz", "size": 16, "unit": "oz", "base_price": 1.49},
    ]},
    {"generic": "canned tuna", "category": "Canned", "variants": [
        {"name": "Chunk Light Tuna 5oz", "size": 5, "unit": "oz", "base_price": 1.29},
        {"name": "Albacore Tuna 5oz", "size": 5, "unit": "oz", "base_price": 2.29},
        {"name": "Chunk Light Tuna 4pk", "size": 4, "unit": "count", "base_price": 4.49},
    ]},
    {"generic": "canned soup", "category": "Canned", "variants": [
        {"name": "Chicken Noodle Soup 10.75oz", "size": 10.75, "unit": "oz", "base_price": 1.49},
        {"name": "Tomato Soup 10.75oz", "size": 10.75, "unit": "oz", "base_price": 1.29},
        {"name": "Cream of Mushroom Soup 10.5oz", "size": 10.5, "unit": "oz", "base_price": 1.49},
    ]},
    {"generic": "peanut butter", "category": "Pantry", "variants": [
        {"name": "Creamy Peanut Butter 16oz", "size": 16, "unit": "oz", "base_price": 3.49},
        {"name": "Crunchy Peanut Butter 16oz", "size": 16, "unit": "oz", "base_price": 3.49},
        {"name": "Natural Peanut Butter 16oz", "size": 16, "unit": "oz", "base_price": 4.29},
        {"name": "Peanut Butter 40oz", "size": 40, "unit": "oz", "base_price": 6.99},
    ]},
    {"generic": "jelly", "category": "Pantry", "variants": [
        {"name": "Grape Jelly 18oz", "size": 18, "unit": "oz", "base_price": 2.99},
        {"name": "Strawberry Jam 18oz", "size": 18, "unit": "oz", "base_price": 3.29},
        {"name": "Raspberry Preserves 12oz", "size": 12, "unit": "oz", "base_price": 3.49},
    ]},
    {"generic": "honey", "category": "Pantry", "variants": [
        {"name": "Honey Bear 12oz", "size": 12, "unit": "oz", "base_price": 4.99},
        {"name": "Raw Honey 16oz", "size": 16, "unit": "oz", "base_price": 7.99},
        {"name": "Organic Honey 12oz", "size": 12, "unit": "oz", "base_price": 6.99},
    ]},
    {"generic": "flour", "category": "Baking", "variants": [
        {"name": "All Purpose Flour 5lb", "size": 5, "unit": "lb", "base_price": 3.29},
        {"name": "Bread Flour 5lb", "size": 5, "unit": "lb", "base_price": 3.99},
        {"name": "Whole Wheat Flour 5lb", "size": 5, "unit": "lb", "base_price": 3.79},
    ]},
    {"generic": "sugar", "category": "Baking", "variants": [
        {"name": "Granulated Sugar 4lb", "size": 4, "unit": "lb", "base_price": 3.49},
        {"name": "Brown Sugar 2lb", "size": 2, "unit": "lb", "base_price": 2.99},
        {"name": "Powdered Sugar 2lb", "size": 2, "unit": "lb", "base_price": 2.79},
        {"name": "Granulated Sugar 10lb", "size": 10, "unit": "lb", "base_price": 6.99},
    ]},
    # BEVERAGES
    {"generic": "water", "category": "Beverages", "variants": [
        {"name": "Purified Water 24pk 16.9oz", "size": 24, "unit": "count", "base_price": 3.99},
        {"name": "Spring Water 1 Gallon", "size": 128, "unit": "fl_oz", "base_price": 1.29},
        {"name": "Purified Water 40pk 16.9oz", "size": 40, "unit": "count", "base_price": 5.99},
    ]},
    {"generic": "orange juice", "category": "Beverages", "variants": [
        {"name": "Orange Juice 52oz", "size": 52, "unit": "fl_oz", "base_price": 3.99},
        {"name": "Orange Juice with Pulp 52oz", "size": 52, "unit": "fl_oz", "base_price": 3.99},
        {"name": "Organic Orange Juice 52oz", "size": 52, "unit": "fl_oz", "base_price": 5.49},
    ]},
    {"generic": "coffee", "category": "Beverages", "variants": [
        {"name": "Ground Coffee Medium Roast 12oz", "size": 12, "unit": "oz", "base_price": 7.99},
        {"name": "Ground Coffee Dark Roast 12oz", "size": 12, "unit": "oz", "base_price": 7.99},
        {"name": "Whole Bean Coffee 12oz", "size": 12, "unit": "oz", "base_price": 8.99},
        {"name": "K-Cups 12ct", "size": 12, "unit": "count", "base_price": 7.49},
        {"name": "Instant Coffee 8oz", "size": 8, "unit": "oz", "base_price": 5.99},
    ]},
    {"generic": "tea", "category": "Beverages", "variants": [
        {"name": "Green Tea 20ct", "size": 20, "unit": "count", "base_price": 2.99},
        {"name": "Black Tea 100ct", "size": 100, "unit": "count", "base_price": 4.49},
        {"name": "Herbal Tea Variety 20ct", "size": 20, "unit": "count", "base_price": 3.49},
    ]},
    {"generic": "soda", "category": "Beverages", "variants": [
        {"name": "Cola 12pk 12oz Cans", "size": 12, "unit": "count", "base_price": 5.99},
        {"name": "Cola 2 Liter", "size": 67.6, "unit": "fl_oz", "base_price": 1.99},
        {"name": "Lemon Lime 12pk 12oz Cans", "size": 12, "unit": "count", "base_price": 5.99},
        {"name": "Ginger Ale 12pk 12oz", "size": 12, "unit": "count", "base_price": 5.99},
    ]},
    # FROZEN
    {"generic": "frozen pizza", "category": "Frozen", "variants": [
        {"name": "Pepperoni Pizza 20oz", "size": 20, "unit": "oz", "base_price": 5.99},
        {"name": "Cheese Pizza 20oz", "size": 20, "unit": "oz", "base_price": 5.49},
        {"name": "Supreme Pizza 22oz", "size": 22, "unit": "oz", "base_price": 6.49},
    ]},
    {"generic": "frozen vegetables", "category": "Frozen", "variants": [
        {"name": "Frozen Broccoli 12oz", "size": 12, "unit": "oz", "base_price": 1.49},
        {"name": "Frozen Mixed Vegetables 12oz", "size": 12, "unit": "oz", "base_price": 1.49},
        {"name": "Frozen Corn 12oz", "size": 12, "unit": "oz", "base_price": 1.29},
        {"name": "Frozen Peas 12oz", "size": 12, "unit": "oz", "base_price": 1.49},
        {"name": "Frozen Green Beans 12oz", "size": 12, "unit": "oz", "base_price": 1.49},
        {"name": "Stir Fry Vegetables 12oz", "size": 12, "unit": "oz", "base_price": 2.29},
    ]},
    {"generic": "ice cream", "category": "Frozen", "variants": [
        {"name": "Vanilla Ice Cream 48oz", "size": 48, "unit": "fl_oz", "base_price": 4.99},
        {"name": "Chocolate Ice Cream 48oz", "size": 48, "unit": "fl_oz", "base_price": 4.99},
        {"name": "Cookie Dough Ice Cream 48oz", "size": 48, "unit": "fl_oz", "base_price": 5.49},
        {"name": "Premium Vanilla Ice Cream 14oz", "size": 14, "unit": "fl_oz", "base_price": 5.99},
    ]},
    {"generic": "frozen chicken nuggets", "category": "Frozen", "variants": [
        {"name": "Chicken Nuggets 32oz", "size": 32, "unit": "oz", "base_price": 7.99},
        {"name": "Chicken Tenders 25oz", "size": 25, "unit": "oz", "base_price": 8.49},
    ]},
    {"generic": "frozen waffles", "category": "Frozen", "variants": [
        {"name": "Frozen Waffles 10ct", "size": 10, "unit": "count", "base_price": 2.99},
        {"name": "Frozen Waffles Blueberry 10ct", "size": 10, "unit": "count", "base_price": 3.29},
    ]},
    # SNACKS
    {"generic": "chips", "category": "Snacks", "variants": [
        {"name": "Classic Potato Chips 8oz", "size": 8, "unit": "oz", "base_price": 4.29},
        {"name": "BBQ Potato Chips 8oz", "size": 8, "unit": "oz", "base_price": 4.29},
        {"name": "Sour Cream & Onion Chips 8oz", "size": 8, "unit": "oz", "base_price": 4.29},
        {"name": "Tortilla Chips 13oz", "size": 13, "unit": "oz", "base_price": 3.99},
        {"name": "Kettle Cooked Chips 8oz", "size": 8, "unit": "oz", "base_price": 4.49},
    ]},
    {"generic": "crackers", "category": "Snacks", "variants": [
        {"name": "Saltine Crackers 16oz", "size": 16, "unit": "oz", "base_price": 2.99},
        {"name": "Cheddar Crackers 12.4oz", "size": 12.4, "unit": "oz", "base_price": 3.99},
        {"name": "Whole Wheat Crackers 9oz", "size": 9, "unit": "oz", "base_price": 3.49},
    ]},
    {"generic": "nuts", "category": "Snacks", "variants": [
        {"name": "Mixed Nuts 16oz", "size": 16, "unit": "oz", "base_price": 8.99},
        {"name": "Almonds 16oz", "size": 16, "unit": "oz", "base_price": 7.99},
        {"name": "Cashews 16oz", "size": 16, "unit": "oz", "base_price": 9.99},
        {"name": "Peanuts Roasted 16oz", "size": 16, "unit": "oz", "base_price": 3.99},
    ]},
    {"generic": "granola bars", "category": "Snacks", "variants": [
        {"name": "Granola Bars Variety 12ct", "size": 12, "unit": "count", "base_price": 3.99},
        {"name": "Protein Bars 5ct", "size": 5, "unit": "count", "base_price": 5.99},
        {"name": "Chewy Granola Bars 8ct", "size": 8, "unit": "count", "base_price": 3.29},
    ]},
    # HOUSEHOLD
    {"generic": "laundry detergent", "category": "Household", "variants": [
        {"name": "Liquid Laundry Detergent 92oz", "size": 92, "unit": "fl_oz", "base_price": 11.99},
        {"name": "Liquid Laundry Detergent 64oz", "size": 64, "unit": "fl_oz", "base_price": 8.49},
        {"name": "Laundry Pods 42ct", "size": 42, "unit": "count", "base_price": 13.99},
        {"name": "Free & Clear Detergent 92oz", "size": 92, "unit": "fl_oz", "base_price": 12.49},
        {"name": "Liquid Laundry Detergent 170oz", "size": 170, "unit": "fl_oz", "base_price": 19.99},
    ]},
    {"generic": "dish soap", "category": "Household", "variants": [
        {"name": "Dish Soap 22oz", "size": 22, "unit": "fl_oz", "base_price": 3.49},
        {"name": "Dish Soap 38oz", "size": 38, "unit": "fl_oz", "base_price": 4.99},
        {"name": "Dish Pods 32ct", "size": 32, "unit": "count", "base_price": 5.99},
    ]},
    {"generic": "paper towels", "category": "Household", "variants": [
        {"name": "Paper Towels 6 Roll", "size": 6, "unit": "count", "base_price": 7.99},
        {"name": "Paper Towels 12 Roll", "size": 12, "unit": "count", "base_price": 14.99},
        {"name": "Paper Towels Select-A-Size 8 Roll", "size": 8, "unit": "count", "base_price": 10.49},
    ]},
    {"generic": "toilet paper", "category": "Household", "variants": [
        {"name": "Toilet Paper 12 Roll", "size": 12, "unit": "count", "base_price": 8.99},
        {"name": "Toilet Paper 24 Roll", "size": 24, "unit": "count", "base_price": 16.99},
        {"name": "Toilet Paper Mega 6 Roll", "size": 6, "unit": "count", "base_price": 7.49},
    ]},
    {"generic": "trash bags", "category": "Household", "variants": [
        {"name": "Tall Kitchen Trash Bags 13gal 45ct", "size": 45, "unit": "count", "base_price": 8.99},
        {"name": "Large Trash Bags 30gal 25ct", "size": 25, "unit": "count", "base_price": 7.99},
        {"name": "Drawstring Trash Bags 13gal 80ct", "size": 80, "unit": "count", "base_price": 12.99},
    ]},
    {"generic": "all purpose cleaner", "category": "Household", "variants": [
        {"name": "All Purpose Cleaner 32oz", "size": 32, "unit": "fl_oz", "base_price": 3.49},
        {"name": "Disinfectant Spray 19oz", "size": 19, "unit": "fl_oz", "base_price": 4.99},
        {"name": "Glass Cleaner 23oz", "size": 23, "unit": "fl_oz", "base_price": 3.29},
    ]},
    # PERSONAL CARE
    {"generic": "shampoo", "category": "Personal Care", "variants": [
        {"name": "Shampoo 12.5oz", "size": 12.5, "unit": "fl_oz", "base_price": 4.99},
        {"name": "2-in-1 Shampoo & Conditioner 12.5oz", "size": 12.5, "unit": "fl_oz", "base_price": 4.99},
        {"name": "Dandruff Shampoo 12.5oz", "size": 12.5, "unit": "fl_oz", "base_price": 6.49},
    ]},
    {"generic": "toothpaste", "category": "Personal Care", "variants": [
        {"name": "Toothpaste 6oz", "size": 6, "unit": "oz", "base_price": 3.99},
        {"name": "Whitening Toothpaste 4.8oz", "size": 4.8, "unit": "oz", "base_price": 4.99},
        {"name": "Sensitive Toothpaste 4oz", "size": 4, "unit": "oz", "base_price": 5.49},
    ]},
    {"generic": "body wash", "category": "Personal Care", "variants": [
        {"name": "Body Wash 18oz", "size": 18, "unit": "fl_oz", "base_price": 5.49},
        {"name": "Moisturizing Body Wash 22oz", "size": 22, "unit": "fl_oz", "base_price": 6.49},
    ]},
    {"generic": "deodorant", "category": "Personal Care", "variants": [
        {"name": "Deodorant 2.6oz", "size": 2.6, "unit": "oz", "base_price": 4.99},
        {"name": "Natural Deodorant 2.6oz", "size": 2.6, "unit": "oz", "base_price": 6.99},
    ]},
    # BABY
    {"generic": "diapers", "category": "Baby", "variants": [
        {"name": "Diapers Size 3 72ct", "size": 72, "unit": "count", "base_price": 22.99},
        {"name": "Diapers Size 4 64ct", "size": 64, "unit": "count", "base_price": 22.99},
        {"name": "Diapers Size 5 56ct", "size": 56, "unit": "count", "base_price": 22.99},
        {"name": "Overnight Diapers Size 4 48ct", "size": 48, "unit": "count", "base_price": 24.99},
    ]},
    {"generic": "baby wipes", "category": "Baby", "variants": [
        {"name": "Baby Wipes Sensitive 72ct", "size": 72, "unit": "count", "base_price": 2.99},
        {"name": "Baby Wipes Refill 240ct", "size": 240, "unit": "count", "base_price": 6.99},
    ]},
    {"generic": "baby formula", "category": "Baby", "variants": [
        {"name": "Infant Formula Powder 12.5oz", "size": 12.5, "unit": "oz", "base_price": 18.99},
        {"name": "Gentle Infant Formula 12.5oz", "size": 12.5, "unit": "oz", "base_price": 19.99},
        {"name": "Organic Infant Formula 23.2oz", "size": 23.2, "unit": "oz", "base_price": 32.99},
    ]},
    # PET
    {"generic": "dog food", "category": "Pet", "variants": [
        {"name": "Dry Dog Food 15lb", "size": 15, "unit": "lb", "base_price": 18.99},
        {"name": "Dry Dog Food 30lb", "size": 30, "unit": "lb", "base_price": 29.99},
        {"name": "Wet Dog Food 13oz 6pk", "size": 6, "unit": "count", "base_price": 8.99},
    ]},
    {"generic": "cat food", "category": "Pet", "variants": [
        {"name": "Dry Cat Food 7lb", "size": 7, "unit": "lb", "base_price": 12.99},
        {"name": "Dry Cat Food 16lb", "size": 16, "unit": "lb", "base_price": 22.99},
        {"name": "Wet Cat Food 3oz 12pk", "size": 12, "unit": "count", "base_price": 9.99},
    ]},
]

# Brand names per store chain
STORE_BRANDS = {
    "walmart": "Great Value",
    "kroger": "Kroger",
    "costco": "Kirkland Signature",
    "traderjoes": "Trader Joe's",
    "target": "Good & Gather",
    "aldi": "Simply Nature",
    "publix": "Publix",
    "heb": "H-E-B",
    "safeway": "Signature Select",
    "wholefoods": "365 by Whole Foods",
}

NATIONAL_BRANDS = [
    "Heinz", "Kraft", "General Mills", "Kellogg's", "Del Monte",
    "Barilla", "Tyson", "Oscar Mayer", "Dole", "Smucker's",
    "Nature's Own", "Bounty", "Charmin", "Tide", "Dawn",
    "Colgate", "Dove", "Pampers", "Huggies", "Purina",
]


async def generate():
    await connect_db()
    db = get_db()

    await db.stores.drop()
    await db.products.drop()
    print("Cleared old data")

    # Generate stores
    stores = []
    store_counter = {}
    for chain_id, chain_info in STORE_CHAINS.items():
        store_counter[chain_id] = 0
        locations_for_chain = random.sample(LOCATIONS, min(random.randint(3, 7), len(LOCATIONS)))
        for loc in locations_for_chain:
            store_counter[chain_id] += 1
            store_id = f"{chain_id}-{loc['zip']}-{store_counter[chain_id]:02d}"
            rating = round(random.uniform(*chain_info["rating_range"]), 1)
            lat_offset = random.uniform(-0.008, 0.008)
            lng_offset = random.uniform(-0.008, 0.008)
            stores.append({
                "store_id": store_id,
                "name": chain_info["name"],
                "chain": chain_id,
                "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'El Camino Real', 'Stevens Creek Blvd', 'Fremont Blvd', 'Mission Blvd', 'First St', 'Central Ave', 'Market St', 'Broadway', 'Oak Ave'])}, {loc['city']}, {loc['state']}",
                "zip_code": loc["zip"],
                "latitude": round(loc["lat"] + lat_offset, 6),
                "longitude": round(loc["lng"] + lng_offset, 6),
                "rating": rating,
                "hours": random.choice(["6AM-11PM", "7AM-10PM", "8AM-9PM", "6AM-12AM", "10AM-8:30PM", "24 Hours"]),
                "phone": f"({random.randint(408, 650)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            })

    await db.stores.insert_many(stores)
    print(f"Created {len(stores)} stores")

    # Generate products
    products = []
    batch_size = 5000

    for product_group in PRODUCT_CATALOG:
        generic = product_group["generic"]
        category = product_group["category"]

        for variant in product_group["variants"]:
            for store in stores:
                chain_id = store["chain"]
                chain_info = STORE_CHAINS[chain_id]
                store_brand = STORE_BRANDS[chain_id]

                # Store brand version
                price_factor = chain_info["price_factor"]
                location_variance = random.uniform(0.95, 1.05)
                final_price = round(variant["base_price"] * price_factor * location_variance, 2)

                products.append({
                    "store_id": store["store_id"],
                    "product_name": f"{store_brand} {variant['name']}",
                    "generic_name": generic,
                    "brand": store_brand,
                    "price": final_price,
                    "unit_size": variant["size"],
                    "unit_type": variant["unit"],
                    "category": category,
                    "upc": f"{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}",
                    "image_url": "",
                    "in_stock": random.random() > 0.05,
                    "last_updated": datetime.utcnow() - timedelta(hours=random.randint(0, 48)),
                })

                # National brand version (70% chance of being available)
                if random.random() < 0.7:
                    national_brand = random.choice(NATIONAL_BRANDS)
                    national_price = round(variant["base_price"] * random.uniform(1.0, 1.3) * location_variance, 2)

                    products.append({
                        "store_id": store["store_id"],
                        "product_name": f"{national_brand} {variant['name']}",
                        "generic_name": generic,
                        "brand": national_brand,
                        "price": national_price,
                        "unit_size": variant["size"],
                        "unit_type": variant["unit"],
                        "category": category,
                        "upc": f"{random.randint(10000000, 99999999)}{random.randint(1000, 9999)}",
                        "image_url": "",
                        "in_stock": random.random() > 0.08,
                        "last_updated": datetime.utcnow() - timedelta(hours=random.randint(0, 48)),
                    })

                if len(products) >= batch_size:
                    await db.products.insert_many(products)
                    print(f"  Inserted batch: {len(products)} products (total so far...)")
                    products = []

    if products:
        await db.products.insert_many(products)
        print(f"  Inserted final batch: {len(products)} products")

    # Create indexes
    await db.products.create_index("generic_name")
    await db.products.create_index("store_id")
    await db.products.create_index("brand")
    await db.products.create_index("price")
    await db.products.create_index([("generic_name", 1), ("store_id", 1)])
    await db.stores.create_index("store_id")
    await db.stores.create_index("chain")
    await db.stores.create_index("zip_code")
    print("Indexes created")

    # Final count
    store_count = await db.stores.count_documents({})
    product_count = await db.products.count_documents({})
    generic_count = len(await db.products.distinct("generic_name"))
    print(f"\nDone! {store_count} stores, {product_count} products, {generic_count} categories")


if __name__ == "__main__":
    asyncio.run(generate())
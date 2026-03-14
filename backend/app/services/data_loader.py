from app.models.schemas import Store, PriceEntry

MOCK_STORES = [
    Store(id="walmart-01", name="Walmart Supercenter", latitude=37.4849, longitude=-122.1478, rating=3.8, address="555 Showers Dr, Mountain View, CA"),
    Store(id="target-01", name="Target", latitude=37.4419, longitude=-122.1430, rating=4.1, address="2000 El Camino Real, Palo Alto, CA"),
    Store(id="costco-01", name="Costco Wholesale", latitude=37.4255, longitude=-122.0980, rating=4.4, address="1000 N Rengstorff Ave, Mountain View, CA"),
    Store(id="tj-01", name="Trader Joes", latitude=37.4400, longitude=-122.1600, rating=4.5, address="855 El Camino Real, Palo Alto, CA"),
    Store(id="kroger-01", name="Kroger", latitude=37.4600, longitude=-122.1200, rating=3.9, address="3922 Middlefield Rd, Palo Alto, CA"),
]

MOCK_PRICES = [
    PriceEntry(item_name="Milk", store_id="walmart-01", price=3.48, unit_size=128, unit_type="fl_oz", brand="Great Value"),
    PriceEntry(item_name="Milk", store_id="target-01", price=3.89, unit_size=128, unit_type="fl_oz", brand="Good and Gather"),
    PriceEntry(item_name="Milk", store_id="costco-01", price=6.49, unit_size=256, unit_type="fl_oz", brand="Kirkland"),
    PriceEntry(item_name="Milk", store_id="tj-01", price=3.99, unit_size=128, unit_type="fl_oz", brand="Trader Joes"),
    PriceEntry(item_name="Milk", store_id="kroger-01", price=3.29, unit_size=128, unit_type="fl_oz", brand="Kroger"),
    PriceEntry(item_name="Eggs", store_id="walmart-01", price=3.12, unit_size=12, unit_type="count", brand="Great Value"),
    PriceEntry(item_name="Eggs", store_id="target-01", price=3.49, unit_size=12, unit_type="count", brand="Good and Gather"),
    PriceEntry(item_name="Eggs", store_id="costco-01", price=7.99, unit_size=36, unit_type="count", brand="Kirkland"),
    PriceEntry(item_name="Eggs", store_id="tj-01", price=3.79, unit_size=12, unit_type="count", brand="Trader Joes"),
    PriceEntry(item_name="Eggs", store_id="kroger-01", price=2.99, unit_size=12, unit_type="count", brand="Kroger"),
    PriceEntry(item_name="Bread", store_id="walmart-01", price=2.48, unit_size=20, unit_type="oz", brand="Great Value"),
    PriceEntry(item_name="Bread", store_id="target-01", price=3.29, unit_size=20, unit_type="oz", brand="Good and Gather"),
    PriceEntry(item_name="Bread", store_id="costco-01", price=4.99, unit_size=44, unit_type="oz", brand="Kirkland"),
    PriceEntry(item_name="Bread", store_id="tj-01", price=2.99, unit_size=20, unit_type="oz", brand="Trader Joes"),
    PriceEntry(item_name="Bread", store_id="kroger-01", price=2.79, unit_size=20, unit_type="oz", brand="Kroger"),
    PriceEntry(item_name="Chicken Breast", store_id="walmart-01", price=8.47, unit_size=3, unit_type="lb", brand="Great Value"),
    PriceEntry(item_name="Chicken Breast", store_id="target-01", price=9.99, unit_size=2.5, unit_type="lb", brand="Good and Gather"),
    PriceEntry(item_name="Chicken Breast", store_id="costco-01", price=22.99, unit_size=6.5, unit_type="lb", brand="Kirkland"),
    PriceEntry(item_name="Chicken Breast", store_id="tj-01", price=6.99, unit_size=1.5, unit_type="lb", brand="Trader Joes"),
    PriceEntry(item_name="Chicken Breast", store_id="kroger-01", price=7.99, unit_size=2.5, unit_type="lb", brand="Kroger"),
    PriceEntry(item_name="Rice", store_id="walmart-01", price=3.98, unit_size=5, unit_type="lb", brand="Great Value"),
    PriceEntry(item_name="Rice", store_id="target-01", price=4.49, unit_size=5, unit_type="lb", brand="Market Pantry"),
    PriceEntry(item_name="Rice", store_id="costco-01", price=9.99, unit_size=15, unit_type="lb", brand="Kirkland"),
    PriceEntry(item_name="Rice", store_id="tj-01", price=3.49, unit_size=3, unit_type="lb", brand="Trader Joes"),
    PriceEntry(item_name="Rice", store_id="kroger-01", price=4.29, unit_size=5, unit_type="lb", brand="Kroger"),
    PriceEntry(item_name="Olive Oil", store_id="walmart-01", price=5.97, unit_size=17, unit_type="fl_oz", brand="Great Value"),
    PriceEntry(item_name="Olive Oil", store_id="target-01", price=6.49, unit_size=17, unit_type="fl_oz", brand="Good and Gather"),
    PriceEntry(item_name="Olive Oil", store_id="costco-01", price=12.99, unit_size=51, unit_type="fl_oz", brand="Kirkland"),
    PriceEntry(item_name="Olive Oil", store_id="tj-01", price=5.99, unit_size=16.9, unit_type="fl_oz", brand="Trader Joes"),
    PriceEntry(item_name="Olive Oil", store_id="kroger-01", price=6.99, unit_size=17, unit_type="fl_oz", brand="Kroger"),
    PriceEntry(item_name="Bananas", store_id="walmart-01", price=0.62, unit_size=1, unit_type="lb", brand=""),
    PriceEntry(item_name="Bananas", store_id="target-01", price=0.69, unit_size=1, unit_type="lb", brand=""),
    PriceEntry(item_name="Bananas", store_id="costco-01", price=1.99, unit_size=3, unit_type="lb", brand=""),
    PriceEntry(item_name="Bananas", store_id="tj-01", price=0.23, unit_size=1, unit_type="count", brand=""),
    PriceEntry(item_name="Bananas", store_id="kroger-01", price=0.59, unit_size=1, unit_type="lb", brand=""),
    PriceEntry(item_name="Cereal", store_id="walmart-01", price=3.98, unit_size=18, unit_type="oz", brand="Great Value"),
    PriceEntry(item_name="Cereal", store_id="target-01", price=4.29, unit_size=18, unit_type="oz", brand="Good and Gather"),
    PriceEntry(item_name="Cereal", store_id="costco-01", price=7.49, unit_size=40, unit_type="oz", brand="Kirkland"),
    PriceEntry(item_name="Cereal", store_id="tj-01", price=3.49, unit_size=14, unit_type="oz", brand="Trader Joes"),
    PriceEntry(item_name="Cereal", store_id="kroger-01", price=3.79, unit_size=18, unit_type="oz", brand="Kroger"),
    PriceEntry(item_name="Pasta", store_id="walmart-01", price=1.28, unit_size=16, unit_type="oz", brand="Great Value"),
    PriceEntry(item_name="Pasta", store_id="target-01", price=1.49, unit_size=16, unit_type="oz", brand="Good and Gather"),
    PriceEntry(item_name="Pasta", store_id="costco-01", price=4.49, unit_size=64, unit_type="oz", brand="Barilla"),
    PriceEntry(item_name="Pasta", store_id="tj-01", price=0.99, unit_size=16, unit_type="oz", brand="Trader Joes", on_sale=True),
    PriceEntry(item_name="Pasta", store_id="kroger-01", price=1.39, unit_size=16, unit_type="oz", brand="Kroger"),
    PriceEntry(item_name="Laundry Detergent", store_id="walmart-01", price=11.97, unit_size=92, unit_type="fl_oz", brand="Tide"),
    PriceEntry(item_name="Laundry Detergent", store_id="target-01", price=12.49, unit_size=92, unit_type="fl_oz", brand="Tide"),
    PriceEntry(item_name="Laundry Detergent", store_id="costco-01", price=19.99, unit_size=170, unit_type="fl_oz", brand="Kirkland"),
    PriceEntry(item_name="Laundry Detergent", store_id="tj-01", price=7.99, unit_size=64, unit_type="fl_oz", brand="Trader Joes"),
    PriceEntry(item_name="Laundry Detergent", store_id="kroger-01", price=11.49, unit_size=92, unit_type="fl_oz", brand="Tide", on_sale=True),
]


def load_stores():
    return MOCK_STORES


def load_price_entries():
    return MOCK_PRICES

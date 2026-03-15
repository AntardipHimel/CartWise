"use client";
import { useState } from "react";
import { optimizeShopping } from "@/lib/api";
import dynamic from "next/dynamic";
import Link from "next/link";

const StoreMap = dynamic(() => import("@/components/StoreMap"), { ssr: false });

const SUGGESTED_ITEMS = [
  "Milk", "Eggs", "Bread", "Chicken Breast", "Rice",
  "Olive Oil", "Bananas", "Cereal", "Pasta", "Laundry Detergent",
];

interface ShoppingItem {
  name: string;
  quantity: number;
}

export default function Home() {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [convenience, setConvenience] = useState(0.5);
  const [gasPrice, setGasPrice] = useState(3.5);
  const [mpg, setMpg] = useState(25);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const userLat = 37.45;
  const userLng = -122.15;

  const addItem = (name: string) => {
    if (!name.trim()) return;
    const exists = items.find((i) => i.name.toLowerCase() === name.toLowerCase());
    if (exists) return;
    setItems([...items, { name: name.trim(), quantity: 1 }]);
    setInputValue("");
    setShowSuggestions(false);
  };

  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleOptimize = async () => {
    if (items.length === 0) return;
    setLoading(true);
    try {
      const data = await optimizeShopping({
        items,
        user_lat: userLat,
        user_lng: userLng,
        convenience_weight: convenience,
        gas_price_per_gallon: gasPrice,
        vehicle_mpg: mpg,
      });
      setResult(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const filtered = SUGGESTED_ITEMS.filter(
    (s) =>
      s.toLowerCase().includes(inputValue.toLowerCase()) &&
      !items.find((i) => i.name.toLowerCase() === s.toLowerCase())
  );

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-10 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
  <div className="text-center lg:text-left">
    <h1 className="mb-2 text-5xl font-bold text-emerald-400">CartWise</h1>
    <p className="text-lg text-gray-400">
      Smart shopping optimizer - find the best stores, save money and time
    </p>
  </div>

  <Link
    href="/users/create"
    className="inline-flex items-center justify-center rounded-xl border border-emerald-600 px-5 py-3 font-semibold text-emerald-400 transition hover:bg-emerald-600 hover:text-white"
  >
    Create User Profile
  </Link>
</div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4 text-emerald-300">Shopping List</h2>

            <div className="relative mb-4">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value);
                  setShowSuggestions(true);
                }}
                onKeyDown={(e) => e.key === "Enter" && addItem(inputValue)}
                onFocus={() => setShowSuggestions(true)}
                placeholder="Type an item (e.g. Milk, Eggs)..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
              />
              {showSuggestions && filtered.length > 0 && inputValue && (
                <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
                  {filtered.map((s) => (
                    <button
                      key={s}
                      onClick={() => addItem(s)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-700 text-gray-300 hover:text-white"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
              {SUGGESTED_ITEMS.filter(
                (s) => !items.find((i) => i.name === s)
              ).map((s) => (
                <button
                  key={s}
                  onClick={() => addItem(s)}
                  className="text-xs bg-gray-800 border border-gray-700 rounded-full px-3 py-1 text-gray-400 hover:border-emerald-500 hover:text-emerald-400"
                >
                  + {s}
                </button>
              ))}
            </div>

            <div className="space-y-2 mb-6">
              {items.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-2"
                >
                  <span className="text-gray-200">{item.name}</span>
                  <button
                    onClick={() => removeItem(i)}
                    className="text-gray-500 hover:text-red-400 text-lg"
                  >
                    x
                  </button>
                </div>
              ))}
              {items.length === 0 && (
                <p className="text-gray-600 text-center py-4">
                  Add items to get started
                </p>
              )}
            </div>

            <div className="space-y-4 mb-6 border-t border-gray-800 pt-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Savings vs Convenience</span>
                  <span className="text-emerald-400">
                    {convenience < 0.3
                      ? "Max Savings"
                      : convenience > 0.7
                      ? "Max Convenience"
                      : "Balanced"}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={convenience}
                  onChange={(e) => setConvenience(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500"
                />
                <div className="flex justify-between text-xs text-gray-600">
                  <span>Save more money</span>
                  <span>Save more time</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">
                    Gas price ($/gal)
                  </label>
                  <input
                    type="number"
                    value={gasPrice}
                    onChange={(e) => setGasPrice(parseFloat(e.target.value))}
                    step="0.1"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">
                    Vehicle MPG
                  </label>
                  <input
                    type="number"
                    value={mpg}
                    onChange={(e) => setMpg(parseFloat(e.target.value))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={handleOptimize}
              disabled={items.length === 0 || loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold py-3 rounded-xl transition-colors"
            >
              {loading ? "Optimizing..." : "Optimize My Shopping"}
            </button>
          </div>

          <div className="space-y-6">
            {!result && (
              <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 text-center">
                <p className="text-gray-500 text-lg py-12">
                  Add items and hit optimize to see your best shopping plan
                </p>
              </div>
            )}

            {result && (
              <>
                <div className="bg-emerald-900/40 border border-emerald-700 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-emerald-400 text-lg font-semibold">
                      Recommendation
                    </span>
                    <span className="bg-emerald-600 text-white text-xs px-2 py-0.5 rounded-full uppercase">
                      {result.recommended === "single"
                        ? "One Store"
                        : "Multi Store"}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm">
                    {result.recommendation_reason}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div
                    className={
                      "bg-gray-900 rounded-2xl p-5 border " +
                      (result.recommended === "single"
                        ? "border-emerald-500"
                        : "border-gray-800")
                    }
                  >
                    <h3 className="text-sm font-semibold text-gray-400 mb-1">
                      SINGLE STORE
                    </h3>
                    <p className="text-white font-bold text-lg mb-3">
                      {result.single_store_plan.stores[0]?.name}
                    </p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Items</span>
                        <span className="text-white">
                          ${result.single_store_plan.total_item_cost.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Gas</span>
                        <span className="text-white">
                          ${result.single_store_plan.travel_cost.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Drive</span>
                        <span className="text-white">
                          {result.single_store_plan.travel_distance_miles} mi /{" "}
                          {result.single_store_plan.travel_time_minutes} min
                        </span>
                      </div>
                      <div className="flex justify-between border-t border-gray-800 pt-2">
                        <span className="text-gray-400 font-semibold">Total</span>
                        <span className="text-emerald-400 font-bold">
                          $
                          {(
                            result.single_store_plan.total_item_cost +
                            result.single_store_plan.travel_cost
                          ).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div
                    className={
                      "bg-gray-900 rounded-2xl p-5 border " +
                      (result.recommended === "multi"
                        ? "border-emerald-500"
                        : "border-gray-800")
                    }
                  >
                    <h3 className="text-sm font-semibold text-gray-400 mb-1">
                      MULTI STORE
                    </h3>
                    <p className="text-white font-bold text-lg mb-3">
                      {result.multi_store_plan.stores
                        .map((s: any) => s.name.split(" ")[0])
                        .join(" + ")}
                    </p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Items</span>
                        <span className="text-white">
                          ${result.multi_store_plan.total_item_cost.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Gas</span>
                        <span className="text-white">
                          ${result.multi_store_plan.travel_cost.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Drive</span>
                        <span className="text-white">
                          {result.multi_store_plan.travel_distance_miles} mi /{" "}
                          {result.multi_store_plan.travel_time_minutes} min
                        </span>
                      </div>
                      <div className="flex justify-between border-t border-gray-800 pt-2">
                        <span className="text-gray-400 font-semibold">Total</span>
                        <span className="text-emerald-400 font-bold">
                          $
                          {(
                            result.multi_store_plan.total_item_cost +
                            result.multi_store_plan.travel_cost
                          ).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
                  <h3 className="text-sm font-semibold text-gray-400 mb-3">
                    STORE MAP
                  </h3>
                  <StoreMap
                    stores={
                      result.recommended === "single"
                        ? result.single_store_plan.stores
                        : result.multi_store_plan.stores
                    }
                    userLat={userLat}
                    userLng={userLng}
                  />
                </div>

                <div className="bg-gray-900 rounded-2xl p-5 border border-gray-800">
                  <h3 className="text-sm font-semibold text-gray-400 mb-3">
                    PRICE BREAKDOWN BY ITEM
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(result.item_rankings).map(
                      ([item, rankings]: [string, any]) => (
                        <div key={item} className="bg-gray-800 rounded-xl p-3">
                          <p className="text-white font-medium mb-2">{item}</p>
                          <div className="grid grid-cols-5 gap-1">
                            {rankings.slice(0, 5).map((r: any, i: number) => (
                              <div
                                key={i}
                                className={
                                  "text-center rounded-lg p-2 text-xs " +
                                  (i === 0
                                    ? "bg-emerald-900/50 border border-emerald-700"
                                    : "bg-gray-750")
                                }
                              >
                                <p className="text-gray-400 truncate">
                                  {r.store_name.split(" ")[0]}
                                </p>
                                <p className="text-white font-semibold">
                                  ${r.price.toFixed(2)}
                                </p>
                                <p className="text-gray-500">
                                  {r.unit_size}
                                  {r.unit_type}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
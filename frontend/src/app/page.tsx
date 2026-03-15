"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import AuthGuard from "@/components/AuthGuard";
import LocationIcon from "@/components/LocationIcon";
import ProfilePanel from "@/components/ProfilePanel";
import ShoppingItemBuilder, {
  DraftShoppingItem,
} from "@/components/ShoppingItemBuilder";
import { getUser, optimizeSmart, saveTrip } from "@/lib/api";
import { getStoredSession, pushCachedRoute } from "@/lib/auth";

const StoreMap = dynamic(() => import("@/components/StoreMap"), { ssr: false });

type UserProfile = {
  name: string;
  email: string;
  zip_code: string;
  latitude: number;
  longitude: number;
  destination_latitude: number;
  destination_longitude: number;
  max_drive_miles: number;
  max_store_count: number;
  vehicle_mpg: number;
  gas_price: number;
};

const defaultProfile: UserProfile = {
  name: "",
  email: "",
  zip_code: "",
  latitude: 37.45,
  longitude: -122.15,
  destination_latitude: 37.45,
  destination_longitude: -122.15,
  max_drive_miles: 15,
  max_store_count: 3,
  vehicle_mpg: 25,
  gas_price: 3.5,
};

function LocationFieldRow({
  title,
  lat,
  lon,
  onLatChange,
  onLonChange,
  onUseCurrent,
}: {
  title: string;
  lat: number;
  lon: number;
  onLatChange: (value: number) => void;
  onLonChange: (value: number) => void;
  onUseCurrent: () => void;
}) {
  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
            <LocationIcon className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{title}</div>
            <div className="text-xs text-gray-500">Coordinates for this trip point</div>
          </div>
        </div>

        <button
          type="button"
          onClick={onUseCurrent}
          className="rounded-xl border border-emerald-600 px-3 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-600 hover:text-white"
        >
          Use Current
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div>
          <label className="mb-2 block text-sm text-gray-400">Latitude</label>
          <input
            type="number"
            step="any"
            value={lat}
            onChange={(e) => onLatChange(Number(e.target.value))}
            className="w-full rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm text-gray-400">Longitude</label>
          <input
            type="number"
            step="any"
            value={lon}
            onChange={(e) => onLonChange(Number(e.target.value))}
            className="w-full rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
          />
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [sessionEmail, setSessionEmail] = useState("");
  const [profile, setProfile] = useState<UserProfile>(defaultProfile);
  const [items, setItems] = useState<DraftShoppingItem[]>([]);
  const [tripStartTime, setTripStartTime] = useState("18:00");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  useEffect(() => {
    const session = getStoredSession();
    if (!session) return;

    setSessionEmail(session.email);

    const loadProfile = async () => {
      const data = await getUser(session.email);
      if (!data?.error) {
        setProfile({
          name: data.name ?? "",
          email: data.email ?? session.email,
          zip_code: data.zip_code ?? "",
          latitude: data.latitude ?? 37.45,
          longitude: data.longitude ?? -122.15,
          destination_latitude: data.destination_latitude ?? data.latitude ?? 37.45,
          destination_longitude: data.destination_longitude ?? data.longitude ?? -122.15,
          max_drive_miles: data.max_drive_miles ?? 15,
          max_store_count: data.max_store_count ?? 3,
          vehicle_mpg: data.vehicle_mpg ?? 25,
          gas_price: data.gas_price ?? 3.5,
        });
      }
    };

    loadProfile();
  }, []);

  const optimizeItems = useMemo(() => {
    return items.map((item) => ({
      item_key: item.item_key,
      filters: {
        brand: item.filters.brand,
        package_size: item.filters.package_size,
        package_unit: item.filters.package_unit,
        max_price: item.filters.max_price,
        must_buy: item.filters.must_buy,
        allow_substitutes: item.filters.allow_substitutes,
      },
    }));
  }, [items]);

  const activeCategory = result?.recommended_category
    ? result.categories?.[result.recommended_category]
    : null;

  const getCurrentCoords = (onSuccess: (lat: number, lon: number) => void) => {
    setStatusMessage("");

    if (!navigator.geolocation) {
      setStatusMessage("Geolocation is not supported.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        onSuccess(position.coords.latitude, position.coords.longitude);
        setStatusMessage("Current location applied.");
      },
      () => {
        setStatusMessage("Unable to fetch current location.");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const handleUseCurrentStart = () => {
    getCurrentCoords((lat, lon) => {
      setProfile((prev) => ({
        ...prev,
        latitude: lat,
        longitude: lon,
      }));
    });
  };

  const handleUseCurrentEnd = () => {
    getCurrentCoords((lat, lon) => {
      setProfile((prev) => ({
        ...prev,
        destination_latitude: lat,
        destination_longitude: lon,
      }));
    });
  };

  const handleOptimize = async () => {
    if (optimizeItems.length === 0) return;

    setLoading(true);
    setStatusMessage("");

    try {
      const data = await optimizeSmart({
        email: sessionEmail,
        start_lat: Number(profile.latitude),
        start_lng: Number(profile.longitude),
        end_lat: Number(profile.destination_latitude),
        end_lng: Number(profile.destination_longitude),
        trip_start_time: tripStartTime,
        max_radius_miles: Number(profile.max_drive_miles),
        max_store_count: Number(profile.max_store_count),
        vehicle_mpg: Number(profile.vehicle_mpg),
        gas_price_per_gallon: Number(profile.gas_price),
        candidate_limit_per_item: 30,
        minimum_multi_store_savings: 2.0,
        items: optimizeItems,
      });

      setResult(data);
    } catch {
      setStatusMessage("Optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCategory = async (categoryKey: "cheapest" | "shortest") => {
    if (!result || !sessionEmail) return;

    const category = result.categories?.[categoryKey];
    if (!category) return;

    const payload = {
      category: categoryKey,
      plan_chosen: categoryKey,
      items_purchased: category.included_products ?? [],
      stores_visited: category.stores ?? [],
      route_taken: category.route ?? [],
      total_spent: Number(category.metrics?.total_cost ?? 0),
      total_saved: 0,
      saved_at: new Date().toISOString(),
    };

    pushCachedRoute(payload);
    await saveTrip(sessionEmail, payload);
    setStatusMessage(`${categoryKey} route saved.`);
  };

  return (
    <AuthGuard>
      <main className="min-h-screen bg-gray-950 text-white">
        <div className="mx-auto max-w-7xl px-4 py-8">
          <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h1 className="text-5xl font-bold text-emerald-400">CartWise</h1>
              <p className="mt-2 text-lg text-gray-400">
                Smart shopping optimizer for savings, convenience, and route planning
              </p>
            </div>

            <button
              onClick={() => setShowProfile(true)}
              className="rounded-2xl border border-gray-800 bg-gray-900 px-5 py-4 text-left transition hover:border-emerald-500"
            >
              <div className="text-sm text-gray-400">Profile</div>
              <div className="mt-1 font-semibold text-white">
                {profile.name || sessionEmail}
              </div>
              <div className="mt-1 text-xs text-gray-500">
                Radius {Number(profile.max_drive_miles).toFixed(1)} mi • Max stores{" "}
                {Number(profile.max_store_count)}
              </div>
            </button>
          </div>

          <div className="grid grid-cols-1 gap-8 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-6">
              <ShoppingItemBuilder items={items} setItems={setItems} />

              <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6">
                <h2 className="mb-4 text-xl font-semibold text-emerald-300">Trip Settings</h2>

                <div className="space-y-4">
                  <LocationFieldRow
                    title="Start Location"
                    lat={profile.latitude}
                    lon={profile.longitude}
                    onLatChange={(value) =>
                      setProfile((prev) => ({ ...prev, latitude: value }))
                    }
                    onLonChange={(value) =>
                      setProfile((prev) => ({ ...prev, longitude: value }))
                    }
                    onUseCurrent={handleUseCurrentStart}
                  />

                  <LocationFieldRow
                    title="End Location"
                    lat={profile.destination_latitude}
                    lon={profile.destination_longitude}
                    onLatChange={(value) =>
                      setProfile((prev) => ({
                        ...prev,
                        destination_latitude: value,
                      }))
                    }
                    onLonChange={(value) =>
                      setProfile((prev) => ({
                        ...prev,
                        destination_longitude: value,
                      }))
                    }
                    onUseCurrent={handleUseCurrentEnd}
                  />
                </div>

                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Driving Radius (miles)</label>
                    <input
                      type="number"
                      min="1"
                      step="0.5"
                      value={profile.max_drive_miles}
                      onChange={(e) =>
                        setProfile((prev) => ({
                          ...prev,
                          max_drive_miles: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Max Store Count</label>
                    <input
                      type="number"
                      min="1"
                      value={profile.max_store_count}
                      onChange={(e) =>
                        setProfile((prev) => ({
                          ...prev,
                          max_store_count: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Vehicle MPG</label>
                    <input
                      type="number"
                      min="1"
                      step="0.1"
                      value={profile.vehicle_mpg}
                      onChange={(e) =>
                        setProfile((prev) => ({
                          ...prev,
                          vehicle_mpg: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Current Gas Price ($/gal)</label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={profile.gas_price}
                      onChange={(e) =>
                        setProfile((prev) => ({
                          ...prev,
                          gas_price: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-gray-400">Trip Start Time</label>
                    <input
                      type="time"
                      value={tripStartTime}
                      onChange={(e) => setTripStartTime(e.target.value)}
                      className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <button
                    type="button"
                    onClick={handleOptimize}
                    disabled={items.length === 0 || loading}
                    className="rounded-xl bg-emerald-600 px-5 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500"
                  >
                    {loading ? "Optimizing..." : "Generate Candidates + Optimize"}
                  </button>
                </div>

                {statusMessage && (
                  <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
                    {statusMessage}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              {!result && (
                <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 text-center">
                  <p className="py-16 text-lg text-gray-500">
                    Add items and optimize to see route categories and selected products.
                  </p>
                </div>
              )}

              {result && (
                <>
                  <div className="rounded-2xl border border-emerald-700 bg-emerald-900/30 p-5">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-semibold text-emerald-300">Recommendation</span>
                      <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-xs uppercase text-white">
                        {result.recommended_category}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-300">{result.recommendation_reason}</p>
                  </div>

                  {(["cheapest", "shortest"] as const).map((key) => {
                    const category = result.categories?.[key];
                    if (!category) return null;

                    return (
                      <div
                        key={key}
                        className={
                          "rounded-2xl border p-5 " +
                          (result.recommended_category === key
                            ? "border-emerald-500 bg-gray-900"
                            : "border-gray-800 bg-gray-900")
                        }
                      >
                        <div className="mb-3 flex items-center justify-between">
                          <h3 className="text-lg font-semibold capitalize text-white">{key}</h3>
                          <button
                            onClick={() => handleSelectCategory(key)}
                            className="rounded-xl border border-emerald-600 px-3 py-2 text-sm font-semibold text-emerald-400 transition hover:bg-emerald-600 hover:text-white"
                          >
                            Select Route
                          </button>
                        </div>

                        <p className="mb-4 text-sm text-gray-400">{category.summary}</p>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div className="rounded-xl bg-gray-800 p-4">
                            <div className="text-gray-500">Total Cost</div>
                            <div className="mt-1 font-semibold text-white">
                              ${Number(category.metrics?.total_cost ?? 0).toFixed(2)}
                            </div>
                          </div>
                          <div className="rounded-xl bg-gray-800 p-4">
                            <div className="text-gray-500">Travel Distance</div>
                            <div className="mt-1 font-semibold text-white">
                              {Number(category.metrics?.travel_distance_miles ?? 0).toFixed(2)} mi
                            </div>
                          </div>
                          <div className="rounded-xl bg-gray-800 p-4">
                            <div className="text-gray-500">Items Included</div>
                            <div className="mt-1 font-semibold text-white">
                              {category.metrics?.items_included ?? 0} / {category.metrics?.items_requested ?? 0}
                            </div>
                          </div>
                          <div className="rounded-xl bg-gray-800 p-4">
                            <div className="text-gray-500">Store Count</div>
                            <div className="mt-1 font-semibold text-white">
                              {category.metrics?.store_count ?? 0}
                            </div>
                          </div>
                        </div>

                        <div className="mt-5">
                          <div className="mb-2 text-sm font-semibold text-gray-300">Selected Products</div>
                          <div className="space-y-2">
                            {(category.included_products ?? []).map((product: any, index: number) => (
                              <div key={index} className="rounded-xl bg-gray-800 px-4 py-3 text-sm">
                                <div className="font-medium text-white">{product.item_key}</div>
                                <div className="mt-1 text-gray-400">
                                  {product.item_name || product.product_id}
                                  {product.brand ? ` • ${product.brand}` : ""}
                                  {product.package_size && product.package_unit
                                    ? ` • ${product.package_size} ${product.package_unit}`
                                    : ""}
                                </div>
                                <div className="mt-1 text-emerald-400">
                                  ${Number(product.price ?? 0).toFixed(2)}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {category.missing_items?.length > 0 && (
                          <div className="mt-5">
                            <div className="mb-2 text-sm font-semibold text-red-300">Missing Items</div>
                            <div className="flex flex-wrap gap-2">
                              {category.missing_items.map((item: string) => (
                                <span
                                  key={item}
                                  className="rounded-full border border-red-500/30 px-3 py-1 text-xs text-red-300"
                                >
                                  {item}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
                    <h3 className="mb-3 text-sm font-semibold text-gray-400">STORE MAP</h3>
                    <StoreMap
                      stores={activeCategory?.stores ?? []}
                      userLat={Number(profile.latitude)}
                      userLng={Number(profile.longitude)}
                    />
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {showProfile && sessionEmail && (
          <ProfilePanel email={sessionEmail} onClose={() => setShowProfile(false)} />
        )}
      </main>
    </AuthGuard>
  );
}
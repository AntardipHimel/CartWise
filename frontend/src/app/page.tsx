"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import AuthGuard from "@/components/AuthGuard";
import LocationIcon from "@/components/LocationIcon";
import ProfilePanel from "@/components/ProfilePanel";
import ShoppingItemBuilder, {
  DraftShoppingItem,
} from "@/components/ShoppingItemBuilder";
import { getUser, optimizeSmartRanked, saveTrip } from "@/lib/api";
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
  const [selectedRouteRank, setSelectedRouteRank] = useState<number | null>(null);
  const [expandedRoute, setExpandedRoute] = useState<number | null>(null);
  const [expandedStores, setExpandedStores] = useState<Record<string, boolean>>({});
  const [routeFilter, setRouteFilter] = useState<"all" | "balanced" | "single" | "multi">("all");

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

  const activeRoute = result?.routes?.find(
    (r: any) => r.rank === selectedRouteRank
  ) ?? null;

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
      const data = await optimizeSmartRanked({
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
      setSelectedRouteRank(data.balanced_route_rank || 1);
      setExpandedRoute(null);
      setExpandedStores({});
      setRouteFilter("all");
    } catch {
      setStatusMessage("Optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRoute = async (rank: number) => {
    if (!result || !sessionEmail) return;

    const route = result.routes?.find((r: any) => r.rank === rank);
    if (!route) return;

    setSelectedRouteRank(rank);

    const payload = {
      category: route.is_balanced_pick ? "balanced" : `route_${rank}`,
      plan_chosen: route.label,
      items_purchased: route.included_products ?? [],
      stores_visited: route.stores ?? [],
      route_taken: route.route ?? [],
      total_spent: Number(route.metrics?.total_cost ?? 0),
      total_saved: 0,
      saved_at: new Date().toISOString(),
    };

    pushCachedRoute(payload);
    await saveTrip(sessionEmail, payload);
    setStatusMessage(`${route.label} saved.`);
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

              {result && result.routes?.length > 0 && (
                <>
                  {/* Recommendation banner */}
                  <div className="rounded-2xl border border-emerald-700 bg-emerald-900/30 p-5">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-semibold text-emerald-300">Recommendation</span>
                      <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-xs uppercase text-white">
                        Route {result.balanced_route_rank}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-300">{result.recommendation_reason}</p>
                  </div>

                  {/* Filters */}
                  <div className="flex flex-wrap gap-2">
                    {(
                      [
                        { key: "all", label: "All Routes" },
                        { key: "balanced", label: "Best Balanced" },
                        { key: "single", label: "Single Store" },
                        { key: "multi", label: "Multi Store" },
                      ] as const
                    ).map((f) => (
                      <button
                        key={f.key}
                        onClick={() => setRouteFilter(f.key)}
                        className={
                          "rounded-full px-4 py-2 text-xs font-semibold transition " +
                          (routeFilter === f.key
                            ? "border border-emerald-500 bg-emerald-500/20 text-emerald-300"
                            : "border border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600")
                        }
                      >
                        {f.label}
                      </button>
                    ))}
                    <span className="flex items-center text-xs text-gray-500">
                      {result.routes.filter((r: any) => {
                        if (routeFilter === "balanced") return r.is_balanced_pick;
                        if (routeFilter === "single") return (r.metrics?.store_count ?? 0) <= 1;
                        if (routeFilter === "multi") return (r.metrics?.store_count ?? 0) > 1;
                        return true;
                      }).length}{" "}
                      of {result.routes.length} routes
                    </span>
                  </div>

                  {/* Route cards */}
                  {result.routes
                    .filter((route: any) => {
                      if (routeFilter === "balanced") return route.is_balanced_pick;
                      if (routeFilter === "single") return (route.metrics?.store_count ?? 0) <= 1;
                      if (routeFilter === "multi") return (route.metrics?.store_count ?? 0) > 1;
                      return true;
                    })
                    .map((route: any) => {
                      const isSelected = selectedRouteRank === route.rank;
                      const isExpanded = expandedRoute === route.rank;
                      const storeStops = (route.route ?? []).filter(
                        (s: any) => s.type === "store"
                      );

                      // Group products by store_id
                      const productsByStore: Record<string, any[]> = {};
                      for (const p of route.included_products ?? []) {
                        if (!productsByStore[p.store_id]) productsByStore[p.store_id] = [];
                        productsByStore[p.store_id].push(p);
                      }

                      return (
                        <div
                          key={route.rank}
                          className={
                            "overflow-hidden rounded-2xl border transition " +
                            (isSelected
                              ? "border-emerald-500 bg-gray-900 ring-1 ring-emerald-500/30"
                              : "border-gray-800 bg-gray-900")
                          }
                        >
                          {/* Card header */}
                          <div
                            className={
                              "flex items-center justify-between px-5 py-4 " +
                              (route.is_balanced_pick ? "bg-amber-500/5" : "")
                            }
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-lg font-bold text-white">
                                {route.label}
                              </span>
                              {route.is_balanced_pick && (
                                <span className="rounded-full bg-amber-500/20 px-2.5 py-0.5 text-xs font-bold uppercase text-amber-400">
                                  ★ Best Balanced
                                </span>
                              )}
                              {route.rank === 1 && !route.is_balanced_pick && (
                                <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-bold uppercase text-emerald-400">
                                  Cheapest
                                </span>
                              )}
                            </div>
                            <button
                              onClick={() => handleSelectRoute(route.rank)}
                              className={
                                "rounded-xl px-4 py-2 text-sm font-semibold transition " +
                                (isSelected
                                  ? "bg-emerald-600 text-white"
                                  : "border border-emerald-600 text-emerald-400 hover:bg-emerald-600 hover:text-white")
                              }
                            >
                              {isSelected ? "✓ Selected" : "Select Route"}
                            </button>
                          </div>

                          {/* Metrics row */}
                          <div className="grid grid-cols-4 gap-3 px-5 pb-4">
                            <div className="rounded-xl bg-emerald-500/10 p-3 text-center">
                              <div className="text-xs font-semibold uppercase text-emerald-500">
                                Total Cost
                              </div>
                              <div className="mt-1 text-base font-bold text-white">
                                ${Number(route.metrics?.total_cost ?? 0).toFixed(2)}
                              </div>
                            </div>
                            <div className="rounded-xl bg-gray-800 p-3 text-center">
                              <div className="text-xs font-semibold uppercase text-gray-500">
                                Travel
                              </div>
                              <div className="mt-1 text-base font-bold text-white">
                                {Number(route.metrics?.travel_distance_miles ?? 0).toFixed(1)} mi
                              </div>
                            </div>
                            <div className="rounded-xl bg-gray-800 p-3 text-center">
                              <div className="text-xs font-semibold uppercase text-gray-500">
                                Items
                              </div>
                              <div className="mt-1 text-base font-bold text-white">
                                {route.metrics?.items_included ?? 0}/{route.metrics?.items_requested ?? 0}
                              </div>
                            </div>
                            <div className="rounded-xl bg-gray-800 p-3 text-center">
                              <div className="text-xs font-semibold uppercase text-gray-500">
                                Stores
                              </div>
                              <div className="mt-1 text-base font-bold text-white">
                                {route.metrics?.store_count ?? 0}
                              </div>
                            </div>
                          </div>

                          {/* Trip Plan accordion */}
                          <div className="border-t border-gray-800">
                            <button
                              onClick={() =>
                                setExpandedRoute(isExpanded ? null : route.rank)
                              }
                              className="flex w-full items-center justify-between px-5 py-3 text-left"
                            >
                              <span className="text-sm font-semibold text-white">
                                Trip Plan
                              </span>
                              <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2.5"
                                className={
                                  "text-gray-500 transition-transform " +
                                  (isExpanded ? "rotate-180" : "")
                                }
                              >
                                <polyline points="6 9 12 15 18 9" />
                              </svg>
                            </button>

                            {isExpanded && (
                              <div className="space-y-2 px-5 pb-5">
                                {/* Start */}
                                <div className="flex items-center justify-between rounded-xl border border-gray-700 bg-gray-800/60 px-4 py-3">
                                  <div className="flex items-center gap-3">
                                    <div className="h-3 w-3 rounded-full bg-emerald-500" />
                                    <span className="text-sm font-semibold text-white">
                                      Start
                                    </span>
                                  </div>
                                  <div className="flex gap-4 text-xs text-gray-500">
                                    <span>Distance: 0</span>
                                    <span>Time: {tripStartTime}</span>
                                  </div>
                                </div>

                                {/* Store stops */}
                                {storeStops.map((stop: any, si: number) => {
                                  const storeKey = `${route.rank}-${stop.store_id}`;
                                  const storeProducts =
                                    productsByStore[stop.store_id] ?? [];
                                  const storeOpen = expandedStores[storeKey] ?? false;
                                  const storeTotal = storeProducts.reduce(
                                    (s: number, p: any) => s + (p.price ?? 0),
                                    0
                                  );
                                  const COLORS = [
                                    "bg-blue-500",
                                    "bg-fuchsia-500",
                                    "bg-orange-500",
                                    "bg-teal-500",
                                    "bg-violet-500",
                                  ];

                                  return (
                                    <div key={si}>
                                      {/* Connector line */}
                                      <div className="ml-[21px] h-4 w-0.5 bg-gray-700" />

                                      <div className="overflow-hidden rounded-xl border border-gray-700 bg-gray-800/60">
                                        <button
                                          onClick={() =>
                                            setExpandedStores((prev) => ({
                                              ...prev,
                                              [storeKey]: !storeOpen,
                                            }))
                                          }
                                          className="flex w-full items-center justify-between px-4 py-3 text-left"
                                        >
                                          <div className="flex items-center gap-3">
                                            <div
                                              className={
                                                "h-3 w-3 rounded-full " +
                                                COLORS[si % COLORS.length]
                                              }
                                            />
                                            <span className="text-sm font-semibold text-white">
                                              {stop.name || stop.vendor || stop.store_id}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                              {storeProducts.length} items
                                            </span>
                                          </div>
                                          <div className="flex items-center gap-4 text-xs">
                                            <span className="text-gray-500">
                                              +
                                              {Number(
                                                (route.metrics
                                                  ?.travel_distance_miles ?? 0) /
                                                  Math.max(storeStops.length, 1)
                                              ).toFixed(1)}{" "}
                                              mi
                                            </span>
                                            <span className="font-semibold text-white">
                                              ${storeTotal.toFixed(2)}
                                            </span>
                                            <svg
                                              width="14"
                                              height="14"
                                              viewBox="0 0 24 24"
                                              fill="none"
                                              stroke="currentColor"
                                              strokeWidth="2.5"
                                              className={
                                                "text-gray-500 transition-transform " +
                                                (storeOpen ? "rotate-180" : "")
                                              }
                                            >
                                              <polyline points="6 9 12 15 18 9" />
                                            </svg>
                                          </div>
                                        </button>

                                        {storeOpen && (
                                          <div className="border-t border-gray-700 px-4 pb-3 pt-2">
                                            {/* Product table header */}
                                            <div className="mb-1 grid grid-cols-[1fr_1fr_0.6fr_0.6fr] gap-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
                                              <span>Name</span>
                                              <span>Brand</span>
                                              <span>Size</span>
                                              <span className="text-right">
                                                Price
                                              </span>
                                            </div>
                                            {storeProducts.map(
                                              (p: any, pi: number) => (
                                                <div
                                                  key={pi}
                                                  className="grid grid-cols-[1fr_1fr_0.6fr_0.6fr] gap-2 border-t border-gray-700/50 py-2 text-xs"
                                                >
                                                  <span className="font-medium text-white">
                                                    {p.item_name || p.item_key}
                                                  </span>
                                                  <span className="text-gray-400">
                                                    {p.brand || "—"}
                                                  </span>
                                                  <span className="text-gray-400">
                                                    {p.package_size && p.package_unit
                                                      ? `${p.package_size} ${p.package_unit}`
                                                      : "—"}
                                                  </span>
                                                  <span className="text-right font-semibold text-emerald-400">
                                                    $
                                                    {Number(
                                                      p.price ?? 0
                                                    ).toFixed(2)}
                                                  </span>
                                                </div>
                                              )
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}

                                {/* End connector + stop */}
                                <div className="ml-[21px] h-4 w-0.5 bg-gray-700" />
                                <div className="flex items-center justify-between rounded-xl border border-gray-700 bg-gray-800/60 px-4 py-3">
                                  <div className="flex items-center gap-3">
                                    <div className="h-3 w-3 rounded-full bg-red-500" />
                                    <span className="text-sm font-semibold text-white">
                                      End
                                    </span>
                                  </div>
                                  <div className="flex gap-4 text-xs text-gray-500">
                                    <span>
                                      {Number(
                                        route.metrics?.travel_distance_miles ?? 0
                                      ).toFixed(1)}{" "}
                                      mi total
                                    </span>
                                    <span>
                                      ~
                                      {Math.round(
                                        route.metrics?.travel_time_minutes ?? 0
                                      )}{" "}
                                      min
                                    </span>
                                  </div>
                                </div>

                                {/* Missing items */}
                                {route.missing_items?.length > 0 && (
                                  <div className="mt-3">
                                    <div className="mb-2 text-xs font-semibold text-red-300">
                                      Missing Items
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                      {route.missing_items.map((item: string) => (
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

                                {/* Route map */}
                                <div className="mt-3">
                                  <StoreMap
                                    route={route.route ?? []}
                                    userLat={Number(profile.latitude)}
                                    userLng={Number(profile.longitude)}
                                    mapId={`route-${route.rank}`}
                                  />
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
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
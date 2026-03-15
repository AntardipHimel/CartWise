"use client";

import { useEffect, useState } from "react";
import {
  getRecommendations,
  getUser,
  getUserTrips,
  updateUser,
} from "@/lib/api";
import { clearStoredSession, getCachedRoutes } from "@/lib/auth";

type Props = {
  email: string;
  onClose: () => void;
};

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

const emptyProfile: UserProfile = {
  name: "",
  email: "",
  zip_code: "",
  latitude: 0,
  longitude: 0,
  destination_latitude: 0,
  destination_longitude: 0,
  max_drive_miles: 15,
  max_store_count: 3,
  vehicle_mpg: 25,
  gas_price: 3.5,
};

function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
  step,
  placeholder,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
  step?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-gray-400">{label}</label>
      <input
        type={type}
        step={step}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
      />
    </div>
  );
}

export default function ProfilePanel({ email, onClose }: Props) {
  const [profile, setProfile] = useState<UserProfile>(emptyProfile);
  const [trips, setTrips] = useState<any[]>([]);
  const [cachedRoutes, setCachedRoutes] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      const [userData, tripData, recommendationData] = await Promise.all([
        getUser(email),
        getUserTrips(email),
        getRecommendations(email),
      ]);

      if (!userData?.error) {
        setProfile({
          name: userData.name ?? "",
          email: userData.email ?? email,
          zip_code: userData.zip_code ?? "",
          latitude: userData.latitude ?? 0,
          longitude: userData.longitude ?? 0,
          destination_latitude: userData.destination_latitude ?? userData.latitude ?? 0,
          destination_longitude: userData.destination_longitude ?? userData.longitude ?? 0,
          max_drive_miles: userData.max_drive_miles ?? 15,
          max_store_count: userData.max_store_count ?? 3,
          vehicle_mpg: userData.vehicle_mpg ?? 25,
          gas_price: userData.gas_price ?? 3.5,
        });
      }

      setTrips(tripData?.trips ?? []);
      setRecommendations(recommendationData ?? null);
      setCachedRoutes(getCachedRoutes());
    };

    load();
  }, [email]);

  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    const result = await updateUser(email, {
      name: profile.name,
      zip_code: profile.zip_code,
      latitude: Number(profile.latitude),
      longitude: Number(profile.longitude),
      destination_latitude: Number(profile.destination_latitude),
      destination_longitude: Number(profile.destination_longitude),
      max_drive_miles: Number(profile.max_drive_miles),
      max_store_count: Number(profile.max_store_count),
      vehicle_mpg: Number(profile.vehicle_mpg),
      gas_price: Number(profile.gas_price),
    });

    if (result?.error) {
      setMessage(result.error);
    } else {
      setMessage("Profile updated.");
    }

    setSaving(false);
  };

  const handleLogout = () => {
    clearStoredSession();
    window.location.href = "/login";
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50">
      <div className="h-full w-full max-w-2xl overflow-y-auto border-l border-gray-800 bg-gray-950 p-6 text-white">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-emerald-400">Profile</h2>
            <p className="mt-1 text-sm text-gray-400">{email}</p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleLogout}
              className="rounded-xl border border-red-500/40 px-4 py-2 text-sm font-medium text-red-300 transition hover:bg-red-500/10"
            >
              Logout
            </button>
            <button
              onClick={onClose}
              className="rounded-xl border border-gray-700 px-4 py-2 text-sm font-medium text-gray-300 transition hover:border-emerald-500 hover:text-emerald-400"
            >
              Close
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
            <h3 className="mb-4 text-lg font-semibold text-emerald-300">Account Settings</h3>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <LabeledInput
                label="Name"
                value={profile.name}
                onChange={(value) => setProfile((prev) => ({ ...prev, name: value }))}
                placeholder="Your name"
              />
              <LabeledInput
                label="Email"
                value={profile.email}
                onChange={() => {}}
                placeholder="Email"
              />
              <LabeledInput
                label="ZIP Code"
                value={profile.zip_code}
                onChange={(value) => setProfile((prev) => ({ ...prev, zip_code: value }))}
                placeholder="ZIP code"
              />
              <LabeledInput
                label="Driving Radius (miles)"
                value={profile.max_drive_miles}
                onChange={(value) =>
                  setProfile((prev) => ({ ...prev, max_drive_miles: Number(value) }))
                }
                type="number"
                step="0.5"
              />
              <LabeledInput
                label="Max Store Count"
                value={profile.max_store_count}
                onChange={(value) =>
                  setProfile((prev) => ({ ...prev, max_store_count: Number(value) }))
                }
                type="number"
              />
              <LabeledInput
                label="Vehicle MPG"
                value={profile.vehicle_mpg}
                onChange={(value) =>
                  setProfile((prev) => ({ ...prev, vehicle_mpg: Number(value) }))
                }
                type="number"
                step="0.1"
              />
              <LabeledInput
                label="Gas Price ($/gal)"
                value={profile.gas_price}
                onChange={(value) =>
                  setProfile((prev) => ({ ...prev, gas_price: Number(value) }))
                }
                type="number"
                step="0.01"
              />
              <div className="hidden md:block" />

              <LabeledInput
                label="Start Latitude"
                value={profile.latitude}
                onChange={(value) =>
                  setProfile((prev) => ({ ...prev, latitude: Number(value) }))
                }
                type="number"
                step="any"
              />
              <LabeledInput
                label="Start Longitude"
                value={profile.longitude}
                onChange={(value) =>
                  setProfile((prev) => ({ ...prev, longitude: Number(value) }))
                }
                type="number"
                step="any"
              />
              <LabeledInput
                label="End Latitude"
                value={profile.destination_latitude}
                onChange={(value) =>
                  setProfile((prev) => ({
                    ...prev,
                    destination_latitude: Number(value),
                  }))
                }
                type="number"
                step="any"
              />
              <LabeledInput
                label="End Longitude"
                value={profile.destination_longitude}
                onChange={(value) =>
                  setProfile((prev) => ({
                    ...prev,
                    destination_longitude: Number(value),
                  }))
                }
                type="number"
                step="any"
              />
            </div>

            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="rounded-xl bg-emerald-600 px-4 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:bg-gray-700 disabled:text-gray-500"
              >
                {saving ? "Saving..." : "Save Profile"}
              </button>

              {message && <span className="text-sm text-emerald-300">{message}</span>}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
            <h3 className="mb-4 text-lg font-semibold text-emerald-300">Recommendations</h3>

            <div className="space-y-3">
              {(recommendations?.regular_list ?? []).slice(0, 6).map((item: any, index: number) => (
                <div key={index} className="rounded-xl bg-gray-800 px-4 py-3 text-sm">
                  <div className="font-medium text-white">{item.item}</div>
                  <div className="mt-1 text-gray-400">Seen {item.count} time(s)</div>
                </div>
              ))}

              {(!recommendations?.regular_list || recommendations.regular_list.length === 0) && (
                <div className="rounded-xl bg-gray-800 px-4 py-3 text-sm text-gray-400">
                  No recommendation history yet.
                </div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
            <h3 className="mb-4 text-lg font-semibold text-emerald-300">Cached Selected Routes</h3>

            <div className="space-y-3">
              {cachedRoutes.length === 0 && (
                <div className="rounded-xl bg-gray-800 px-4 py-3 text-sm text-gray-400">
                  No locally cached routes yet.
                </div>
              )}

              {cachedRoutes.map((route, index) => (
                <div key={index} className="rounded-xl bg-gray-800 px-4 py-3 text-sm">
                  <div className="font-medium text-white">
                    {route.category || route.plan_chosen || "Saved plan"}
                  </div>
                  <div className="mt-1 text-gray-400">
                    Total spent: ${Number(route.total_spent ?? 0).toFixed(2)}
                  </div>
                  <div className="mt-1 text-gray-500">
                    {new Date(route.saved_at || Date.now()).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-900 p-5">
            <h3 className="mb-4 text-lg font-semibold text-emerald-300">Trip History</h3>

            <div className="space-y-3">
              {trips.length === 0 && (
                <div className="rounded-xl bg-gray-800 px-4 py-3 text-sm text-gray-400">
                  No saved trips yet.
                </div>
              )}

              {trips.map((trip, index) => (
                <div key={index} className="rounded-xl bg-gray-800 px-4 py-3 text-sm">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-white">
                      {trip.plan_chosen || "Saved plan"}
                    </div>
                    <div className="text-gray-400">
                      ${Number(trip.total_spent ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <div className="mt-1 text-gray-500">
                    {trip.trip_date ? new Date(trip.trip_date).toLocaleString() : "Unknown date"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
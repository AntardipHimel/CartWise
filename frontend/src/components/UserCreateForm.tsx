"use client";

import { FormEvent, useMemo, useState } from "react";
import { createUser } from "@/lib/api";

type FormState = {
  name: string;
  email: string;
  password: string;
  zip_code: string;
  latitude: string;
  longitude: string;
  destination_latitude: string;
  destination_longitude: string;
  max_drive_miles: string;
  max_store_count: string;
  vehicle_mpg: string;
  gas_price: string;
};

const initialState: FormState = {
  name: "",
  email: "",
  password: "",
  zip_code: "",
  latitude: "",
  longitude: "",
  destination_latitude: "",
  destination_longitude: "",
  max_drive_miles: "15",
  max_store_count: "3",
  vehicle_mpg: "25",
  gas_price: "3.5",
};

export default function UserCreateForm() {
  const [form, setForm] = useState<FormState>(initialState);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  const canSubmit = useMemo(() => {
    return (
      form.name.trim().length > 0 &&
      form.email.trim().length > 0 &&
      form.password.trim().length > 0
    );
  }, [form]);

  const updateField = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleUseCurrentLocation = async () => {
    setMessage(null);
    setIsError(false);

    if (!navigator.geolocation) {
      setMessage("Geolocation is not supported in this browser.");
      setIsError(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = String(position.coords.latitude);
        const lng = String(position.coords.longitude);
        updateField("latitude", lat);
        updateField("longitude", lng);
        if (!form.destination_latitude.trim()) updateField("destination_latitude", lat);
        if (!form.destination_longitude.trim()) updateField("destination_longitude", lng);
      },
      () => {
        setMessage("Unable to fetch current location.");
        setIsError(true);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!canSubmit) {
      setMessage("Name, email, and password are required.");
      setIsError(true);
      return;
    }

    setSubmitting(true);
    setMessage(null);
    setIsError(false);

    try {
      const latitude = form.latitude.trim() ? Number(form.latitude) : 0;
      const longitude = form.longitude.trim() ? Number(form.longitude) : 0;

      const payload = {
        name: form.name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        zip_code: form.zip_code.trim(),
        latitude,
        longitude,
        destination_latitude: form.destination_latitude.trim()
          ? Number(form.destination_latitude)
          : latitude,
        destination_longitude: form.destination_longitude.trim()
          ? Number(form.destination_longitude)
          : longitude,
        max_drive_miles: form.max_drive_miles.trim()
          ? Number(form.max_drive_miles)
          : 15,
        max_store_count: form.max_store_count.trim()
          ? Number(form.max_store_count)
          : 3,
        vehicle_mpg: form.vehicle_mpg.trim() ? Number(form.vehicle_mpg) : 25,
        gas_price: form.gas_price.trim() ? Number(form.gas_price) : 3.5,
        brand_preferences: {},
      };

      const result = await createUser(payload);

      if (result?.error) {
        setMessage(result.error);
        setIsError(true);
      } else {
        setMessage("User profile created successfully.");
        setIsError(false);
        setForm(initialState);
      }
    } catch {
      setMessage("Failed to create user profile.");
      setIsError(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900 p-6 shadow-2xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-emerald-400">Create User Profile</h1>
        <p className="mt-2 text-sm text-gray-400">
          Save shopper profile, location, and route settings for optimization.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
              placeholder="Abrar Hossain"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
              placeholder="name@example.com"
            />
          </div>

          <div className="md:col-span-2">
            <label className="mb-2 block text-sm font-medium text-gray-300">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
              placeholder="Enter password"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Driving Radius (miles)</label>
            <input
              type="number"
              min="0"
              step="0.1"
              value={form.max_drive_miles}
              onChange={(e) => updateField("max_drive_miles", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Max Store Count</label>
            <input
              type="number"
              min="1"
              value={form.max_store_count}
              onChange={(e) => updateField("max_store_count", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Vehicle MPG</label>
            <input
              type="number"
              min="1"
              step="0.1"
              value={form.vehicle_mpg}
              onChange={(e) => updateField("vehicle_mpg", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Gas Price ($/gal)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={form.gas_price}
              onChange={(e) => updateField("gas_price", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">ZIP Code</label>
            <input
              type="text"
              value={form.zip_code}
              onChange={(e) => updateField("zip_code", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div className="md:col-span-2">
            <button
              type="button"
              onClick={handleUseCurrentLocation}
              className="rounded-xl border border-emerald-600 px-4 py-3 text-sm font-semibold text-emerald-400 transition hover:bg-emerald-600 hover:text-white"
            >
              Use Current Location
            </button>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Start Latitude</label>
            <input
              type="number"
              step="any"
              value={form.latitude}
              onChange={(e) => updateField("latitude", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">Start Longitude</label>
            <input
              type="number"
              step="any"
              value={form.longitude}
              onChange={(e) => updateField("longitude", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">End Latitude</label>
            <input
              type="number"
              step="any"
              value={form.destination_latitude}
              onChange={(e) => updateField("destination_latitude", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-300">End Longitude</label>
            <input
              type="number"
              step="any"
              value={form.destination_longitude}
              onChange={(e) => updateField("destination_longitude", e.target.value)}
              className="w-full rounded-xl border border-gray-700 bg-gray-800 px-4 py-3 text-white outline-none transition focus:border-emerald-500"
            />
          </div>
        </div>

        {message && (
          <div
            className={`rounded-xl border px-4 py-3 text-sm ${
              isError
                ? "border-red-500/40 bg-red-500/10 text-red-300"
                : "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
            }`}
          >
            {message}
          </div>
        )}

        <button
          type="submit"
          disabled={!canSubmit || submitting}
          className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-gray-700 disabled:text-gray-500"
        >
          {submitting ? "Creating Profile..." : "Create User"}
        </button>
      </form>
    </div>
  );
}
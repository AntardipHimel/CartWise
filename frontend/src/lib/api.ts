const API_BASE = "http://127.0.0.1:8000/api";

export async function createUser(data: {
  name: string;
  email: string;
  password: string;
  zip_code: string;
  latitude: number;
  longitude: number;
  destination_latitude: number;
  destination_longitude: number;
  max_drive_miles: number;
  max_store_count: number;
  vehicle_mpg: number;
  gas_price: number;
  brand_preferences: Record<string, string>;
}) {
  const res = await fetch(API_BASE + "/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function loginUser(data: { email: string; password: string }) {
  const res = await fetch(API_BASE + "/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getUser(email: string) {
  const res = await fetch(API_BASE + `/users/${encodeURIComponent(email)}`);
  return res.json();
}

export async function updateUser(
  email: string,
  data: {
    name?: string;
    zip_code?: string;
    latitude?: number;
    longitude?: number;
    destination_latitude?: number;
    destination_longitude?: number;
    max_drive_miles?: number;
    max_store_count?: number;
    vehicle_mpg?: number;
    gas_price?: number;
    brand_preferences?: Record<string, string>;
  }
) {
  const res = await fetch(API_BASE + `/users/${encodeURIComponent(email)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getUserTrips(email: string) {
  const res = await fetch(API_BASE + `/users/${encodeURIComponent(email)}/trips`);
  return res.json();
}

export async function saveTrip(email: string, data: any) {
  const res = await fetch(API_BASE + `/users/${encodeURIComponent(email)}/trips`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getRecommendations(email: string) {
  const res = await fetch(API_BASE + `/users/${encodeURIComponent(email)}/recommendations`);
  return res.json();
}

export async function getItemSuggestions(query: string, limit = 12) {
  const res = await fetch(
    API_BASE + `/items/suggest?q=${encodeURIComponent(query)}&limit=${limit}`
  );
  return res.json();
}

export async function getItemFilters(itemKey: string) {
  const res = await fetch(API_BASE + `/items/${encodeURIComponent(itemKey)}/filters`);
  return res.json();
}

export async function optimizeSmart(data: {
  email?: string;
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
  trip_start_time: string;
  max_radius_miles: number;
  max_store_count: number;
  vehicle_mpg: number;
  gas_price_per_gallon: number;
  candidate_limit_per_item: number;
  minimum_multi_store_savings: number;
  items: {
    item_key: string;
    filters: {
      brand?: string | null;
      package_size?: number | null;
      package_unit?: string | null;
      max_price?: number | null;
      must_buy: boolean;
      allow_substitutes: boolean;
    };
  }[];
}) {
  const res = await fetch(API_BASE + "/optimize-smart", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function optimizeSmartRanked(data: {
  email?: string;
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
  trip_start_time: string;
  max_radius_miles: number;
  max_store_count: number;
  vehicle_mpg: number;
  gas_price_per_gallon: number;
  candidate_limit_per_item: number;
  minimum_multi_store_savings: number;
  items: {
    item_key: string;
    filters: {
      brand?: string | null;
      package_size?: number | null;
      package_unit?: string | null;
      max_price?: number | null;
      must_buy: boolean;
      allow_substitutes: boolean;
    };
  }[];
}) {
  const res = await fetch(API_BASE + "/optimize-smart-ranked", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}
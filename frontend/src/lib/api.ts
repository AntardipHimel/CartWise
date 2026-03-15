const API_BASE = "http://127.0.0.1:8000/api";

export async function optimizeShopping(data: {
  items: { name: string; quantity: number }[];
  user_lat: number;
  user_lng: number;
  convenience_weight: number;
  gas_price_per_gallon: number;
  vehicle_mpg: number;
}) {
  const res = await fetch(API_BASE + "/optimize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getStores() {
  const res = await fetch(API_BASE + "/stores");
  return res.json();
}

export async function getProducts() {
  const res = await fetch(API_BASE + "/products");
  return res.json();
}

export async function createUser(data: {
  name: string;
  email: string;
  password: string;
  zip_code: string;
  latitude: number;
  longitude: number;
  max_drive_miles: number;
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
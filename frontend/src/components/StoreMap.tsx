"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type RouteStop = {
  type: string;
  lat?: number;
  lon?: number;
  name?: string;
  vendor?: string;
  store_id?: string;
};

type Store = {
  name?: string;
  address?: string;
  lat?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
};

type MapProps = {
  route?: RouteStop[];
  stores?: Store[];
  userLat: number;
  userLng: number;
  mapId?: string;
};

const STORE_COLORS = ["#4285F4", "#EA4335", "#FBBC04", "#34A853", "#9334E6"];

function makePinIcon(label: string, bg: string, size = 32): L.DivIcon {
  return L.divIcon({
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 4)],
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${bg};border:3px solid white;
      box-shadow:0 2px 8px rgba(0,0,0,0.35);
      display:flex;align-items:center;justify-content:center;
      font-size:${size < 30 ? 10 : 13}px;font-weight:700;color:white;
      font-family:-apple-system,system-ui,sans-serif;
    ">${label}</div>`,
  });
}

async function fetchOSRMRoute(
  coords: [number, number][]
): Promise<[number, number][]> {
  if (coords.length < 2) return [];

  // OSRM expects lon,lat
  const coordStr = coords.map(([lat, lon]) => `${lon},${lat}`).join(";");
  const url = `https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.code === "Ok" && data.routes?.[0]?.geometry?.coordinates) {
      // GeoJSON is [lon, lat] — flip to [lat, lon] for Leaflet
      return data.routes[0].geometry.coordinates.map(
        ([lon, lat]: [number, number]) => [lat, lon] as [number, number]
      );
    }
  } catch (e) {
    console.warn("OSRM routing failed, falling back to straight lines", e);
  }
  return [];
}

export default function StoreMap({
  route,
  stores,
  userLat,
  userLng,
  mapId = "default",
}: MapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const map = L.map(containerRef.current, {
      zoomControl: true,
      scrollWheelZoom: true,
    }).setView([userLat, userLng], 13);
    mapRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    const bounds = L.latLngBounds([]);

    if (route && route.length > 0) {
      // ── Route mode ──
      const waypoints: [number, number][] = [];
      let storeNum = 0;

      route.forEach((stop) => {
        const lat = stop.lat;
        const lon = stop.lon;
        if (lat == null || lon == null) return;

        waypoints.push([lat, lon]);
        bounds.extend(L.latLng(lat, lon));

        if (stop.type === "start") {
          L.marker([lat, lon], { icon: makePinIcon("S", "#34A853", 34), zIndexOffset: 1000 })
            .addTo(map)
            .bindPopup("<b style='font-size:13px'>📍 Start</b>");
        } else if (stop.type === "end") {
          L.marker([lat, lon], { icon: makePinIcon("E", "#EA4335", 34), zIndexOffset: 1000 })
            .addTo(map)
            .bindPopup("<b style='font-size:13px'>🏁 End</b>");
        } else if (stop.type === "store") {
          storeNum++;
          const color = STORE_COLORS[(storeNum - 1) % STORE_COLORS.length];
          L.marker([lat, lon], { icon: makePinIcon(String(storeNum), color, 30), zIndexOffset: 900 })
            .addTo(map)
            .bindPopup(
              `<div style="font-size:13px">
                <b>Stop ${storeNum}</b><br/>
                ${stop.name || stop.vendor || stop.store_id || "Store"}
              </div>`
            );
        }
      });

      // Fetch real road route from OSRM
      if (waypoints.length >= 2) {
        fetchOSRMRoute(waypoints).then((roadCoords) => {
          if (!mapRef.current) return;

          if (roadCoords.length > 0) {
            // Real road route — Google Maps style blue
            L.polyline(roadCoords as L.LatLngExpression[], {
              color: "#4285F4",
              weight: 5,
              opacity: 0.85,
              lineJoin: "round",
              lineCap: "round",
            }).addTo(mapRef.current);

            // Subtle border/shadow line behind
            L.polyline(roadCoords as L.LatLngExpression[], {
              color: "#1a56db",
              weight: 8,
              opacity: 0.3,
              lineJoin: "round",
              lineCap: "round",
            }).addTo(mapRef.current).bringToBack();
          } else {
            // Fallback: straight lines if OSRM fails
            L.polyline(waypoints as L.LatLngExpression[], {
              color: "#4285F4",
              weight: 4,
              opacity: 0.7,
              dashArray: "10, 8",
            }).addTo(mapRef.current);
          }
        });
      }
    } else if (stores && stores.length > 0) {
      // ── Legacy pin mode ──
      bounds.extend(L.latLng(userLat, userLng));

      L.marker([userLat, userLng], { icon: makePinIcon("S", "#34A853", 34) })
        .addTo(map)
        .bindPopup("<b>You</b>");

      stores.forEach((store, i) => {
        const lat = store.lat ?? store.latitude;
        const lon = store.lon ?? store.longitude;
        if (lat == null || lon == null) return;
        bounds.extend(L.latLng(lat, lon));

        L.marker([lat, lon], {
          icon: makePinIcon(String(i + 1), STORE_COLORS[i % STORE_COLORS.length], 28),
        })
          .addTo(map)
          .bindPopup(store.name || "Store");
      });
    } else {
      bounds.extend(L.latLng(userLat, userLng));
    }

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [45, 45], maxZoom: 14 });
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [route, stores, userLat, userLng]);

  return (
    <div
      ref={containerRef}
      className="h-[300px] w-full rounded-xl border border-gray-700"
    />
  );
}
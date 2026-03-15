"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type Store = {
  name?: string;
  address?: string;
  lat?: number;
  lon?: number;
  latitude?: number;
  longitude?: number;
};

type MapProps = {
  stores: Store[];
  userLat: number;
  userLng: number;
};

export default function StoreMap({ stores, userLat, userLng }: MapProps) {
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const map = L.map("map").setView([userLat, userLng], 12);
    mapRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "OpenStreetMap",
    }).addTo(map);

    L.circleMarker([userLat, userLng], {
      radius: 10,
      fillColor: "#3b82f6",
      color: "#1e40af",
      weight: 2,
      fillOpacity: 0.9,
    })
      .addTo(map)
      .bindPopup("Start");

    stores.forEach((store) => {
      const lat = store.lat ?? store.latitude;
      const lon = store.lon ?? store.longitude;
      if (lat === undefined || lon === undefined) return;

      L.circleMarker([lat, lon], {
        radius: 8,
        fillColor: "#10b981",
        color: "#065f46",
        weight: 2,
        fillOpacity: 0.9,
      })
        .addTo(map)
        .bindPopup((store.name || "Store") + "<br/>" + (store.address || ""));
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [stores, userLat, userLng]);

  return <div id="map" className="h-[350px] w-full rounded-xl border border-gray-700" />;
}
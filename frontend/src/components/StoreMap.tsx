"use client";
import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface Store {
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
}

interface MapProps {
  stores: Store[];
  userLat: number;
  userLng: number;
}

export default function StoreMap({ stores, userLat, userLng }: MapProps) {
  useEffect(() => {
    const map = L.map("map").setView([userLat, userLng], 13);
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
      .bindPopup("You are here");

    stores.forEach((store) => {
      L.circleMarker([store.latitude, store.longitude], {
        radius: 8,
        fillColor: "#10b981",
        color: "#065f46",
        weight: 2,
        fillOpacity: 0.9,
      })
        .addTo(map)
        .bindPopup(store.name + "<br/>" + (store.address || ""));
    });

    return () => { map.remove(); };
  }, [stores, userLat, userLng]);

  return <div id="map" className="w-full h-[350px] rounded-xl border border-gray-700" />;
}

'use client';

import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default Leaflet icon missing in Next.js build
const customIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

interface MapProps {
  onLocationSelect: (lat: number, lon: number) => void;
  selectedPos: [number, number] | null;
}

// Map Click Handler Component
function LocationMarker({ onLocationSelect, selectedPos }: MapProps) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });

  return selectedPos === null ? null : (
    <Marker position={selectedPos} icon={customIcon}>
      <Popup>Selected Site Target</Popup>
    </Marker>
  );
}

export default function MapScanner({ onLocationSelect, selectedPos }: MapProps) {
  // Default centered on Maharashtra, India (our flagship demo area)
  const defaultCenter: [number, number] = [19.7515, 75.7139];

  return (
    <div className="h-[500px] w-full rounded-xl overflow-hidden shadow-lg border border-slate-700">
      <MapContainer
        center={selectedPos || defaultCenter}
        zoom={7}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LocationMarker onLocationSelect={onLocationSelect} selectedPos={selectedPos} />
      </MapContainer>
    </div>
  );
}
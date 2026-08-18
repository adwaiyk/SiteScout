"use client";

import { useState, useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMapEvents,
  useMap,
  LayersControl,
  Circle,
  GeoJSON,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function createColorIcon(color: string) {
  return new L.DivIcon({
    className: "custom-marker",
    html: `<div style="
      width: 14px; height: 14px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

function createInfraIcon(type: "substation" | "power_line" | "road") {
  const colors = { substation: "#8b5cf6", power_line: "#f59e0b", road: "#6b7280" };
  const symbols = { substation: "⚡", power_line: "⚡", road: "🛣" };
  return new L.DivIcon({
    className: "infra-marker",
    html: `<div style="
      width: 18px; height: 18px;
      background: ${colors[type]};
      border: 2px solid white;
      border-radius: 4px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      display: flex; align-items: center; justify-content: center;
      font-size: 8px; color: white;
    ">${symbols[type]}</div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

const RESULT_ICONS = {
  excellent: createColorIcon("#10b981"),
  viable: createColorIcon("#f59e0b"),
  unsuitable: createColorIcon("#ef4444"),
};

export interface SiteMarker {
  id: string;
  position: [number, number];
  label: string;
  rating: "excellent" | "viable" | "unsuitable";
  score?: number;
}

export interface InfraMarker {
  id: string;
  position: [number, number];
  label: string;
  type: "substation" | "power_line" | "road";
  distance_km?: number;
}

export interface ConflictZone {
  id: string;
  center: [number, number];
  radius_m: number;
  type: string;
  severity: "hard" | "warning" | "info";
}

interface MapScannerProps {
  onLocationSelect: (lat: number, lon: number) => void;
  selectedPos: [number, number] | null;
  center?: [number, number];
  zoom?: number;
  siteMarkers?: SiteMarker[];
  infraMarkers?: InfraMarker[];
  conflictZones?: ConflictZone[];
}

function LocationMarker({
  onLocationSelect,
  selectedPos,
}: {
  onLocationSelect: (lat: number, lon: number) => void;
  selectedPos: [number, number] | null;
}) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });

  return selectedPos === null ? null : (
    <Marker position={selectedPos} icon={defaultIcon}>
      <Popup>
        <div className="text-xs space-y-1">
          <p className="font-semibold">Selected Site Target</p>
          <p className="font-mono text-muted-foreground">
            {selectedPos[0].toFixed(6)}, {selectedPos[1].toFixed(6)}
          </p>
        </div>
      </Popup>
    </Marker>
  );
}

function LayerControlPanel({
  showSolar,
  setShowSolar,
  showWind,
  setShowWind,
  showInfra,
  setShowInfra,
  showConflicts,
  setShowConflicts,
}: {
  showSolar: boolean;
  setShowSolar: (v: boolean) => void;
  showWind: boolean;
  setShowWind: (v: boolean) => void;
  showInfra: boolean;
  setShowInfra: (v: boolean) => void;
  showConflicts: boolean;
  setShowConflicts: (v: boolean) => void;
}) {
  return (
    <div className="absolute top-3 right-3 z-[1000] bg-background/90 backdrop-blur-md border border-border rounded-lg p-3 shadow-lg min-w-[180px]">
      <p className="text-xs font-semibold text-foreground mb-2 uppercase tracking-wider">
        Overlays
      </p>
      <div className="space-y-1.5">
        {[
          { label: "Solar GHI Heatmap", checked: showSolar, toggle: setShowSolar, color: "bg-amber-500" },
          { label: "Wind Speed Layer", checked: showWind, toggle: setShowWind, color: "bg-cyan-500" },
          { label: "Infrastructure", checked: showInfra, toggle: setShowInfra, color: "bg-violet-500" },
          { label: "Conflict Zones", checked: showConflicts, toggle: setShowConflicts, color: "bg-red-500" },
        ].map((layer) => (
          <label
            key={layer.label}
            className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-muted/50 cursor-pointer transition-colors"
          >
            <input
              type="checkbox"
              checked={layer.checked}
              onChange={() => layer.toggle(!layer.checked)}
              className="sr-only"
            />
            <div
              className={`h-3 w-3 rounded-sm border transition-colors ${
                layer.checked
                  ? `${layer.color} border-transparent`
                  : "bg-transparent border-muted-foreground/40"
              }`}
            />
            <span className="text-xs text-foreground">{layer.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function CoordinateDisplay({ pos }: { pos: [number, number] | null }) {
  if (!pos) return null;
  return (
    <div className="absolute bottom-3 left-3 z-[1000] bg-background/90 backdrop-blur-md border border-border rounded-lg px-3 py-2 shadow-lg">
      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
        Target Coordinates
      </p>
      <p className="text-xs font-mono text-foreground">
        {pos[0].toFixed(6)}°N, {pos[1].toFixed(6)}°E
      </p>
    </div>
  );
}

export default function MapScanner({
  onLocationSelect,
  selectedPos,
  center,
  zoom = 7,
  siteMarkers = [],
  infraMarkers = [],
  conflictZones = [],
}: MapScannerProps) {
  const [showSolar, setShowSolar] = useState(false);
  const [showWind, setShowWind] = useState(false);
  const [showInfra, setShowInfra] = useState(true);
  const [showConflicts, setShowConflicts] = useState(true);

  const mapCenter: [number, number] = center || [19.7515, 75.7139];

  return (
    <div className="relative h-[560px] w-full rounded-lg overflow-hidden border border-border">
      {/* Custom Overlay Control Panel */}
      <LayerControlPanel
        showSolar={showSolar}
        setShowSolar={setShowSolar}
        showWind={showWind}
        setShowWind={setShowWind}
        showInfra={showInfra}
        setShowInfra={setShowInfra}
        showConflicts={showConflicts}
        setShowConflicts={setShowConflicts}
      />

      {/* Coordinate Display */}
      <CoordinateDisplay pos={selectedPos} />

      <MapContainer
        center={mapCenter}
        zoom={zoom}
        scrollWheelZoom={true}
        className="h-full w-full"
        zoomControl={true}
      >
        {/* Base Layer Switcher */}
        <LayersControl position="bottomright">
          <LayersControl.BaseLayer checked name="Streets">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="Satellite">
            <TileLayer
              attribution="Tiles &copy; Esri"
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="Terrain">
            <TileLayer
              attribution='&copy; <a href="https://www.opentopomap.org">OpenTopoMap</a>'
              url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {/* Infrastructure overlay: OpenInfraMap power layer */}
        {showInfra && (
          <TileLayer
            url="https://tiles-{s}.openinframap.org/power/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://openinframap.org">OpenInfraMap</a>'
            subdomains={["a", "b", "c"]}
            opacity={0.7}
            maxZoom={18}
          />
        )}

        {/* Click handler + selected marker */}
        <LocationMarker
          onLocationSelect={onLocationSelect}
          selectedPos={selectedPos}
        />

        {/* Scan radius circle */}
        {selectedPos && (
          <Circle
            center={selectedPos}
            radius={5000}
            pathOptions={{
              color: "hsl(175, 60%, 50%)",
              fillColor: "hsl(175, 60%, 50%)",
              fillOpacity: 0.08,
              weight: 1,
              dashArray: "4 4",
            }}
          />
        )}

        {/* Infrastructure markers */}
        {showInfra &&
          infraMarkers.map((m) => (
            <Marker key={m.id} position={m.position} icon={createInfraIcon(m.type)}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-semibold">{m.label}</p>
                  <p className="text-muted-foreground capitalize">{m.type.replace("_", " ")}</p>
                  {m.distance_km !== undefined && (
                    <p className="text-muted-foreground">{m.distance_km.toFixed(1)} km from site</p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Conflict zones */}
        {showConflicts &&
          conflictZones.map((cz) => (
            <Circle
              key={cz.id}
              center={cz.center}
              radius={cz.radius_m}
              pathOptions={{
                color: cz.severity === "hard" ? "#ef4444" : cz.severity === "warning" ? "#f59e0b" : "#6b7280",
                fillColor: cz.severity === "hard" ? "#ef4444" : cz.severity === "warning" ? "#f59e0b" : "#6b7280",
                fillOpacity: 0.12,
                weight: 2,
                dashArray: cz.severity === "hard" ? undefined : "4 4",
              }}
            >
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-semibold">{cz.type}</p>
                  <span
                    className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      cz.severity === "hard"
                        ? "bg-red-500/20 text-red-600"
                        : cz.severity === "warning"
                          ? "bg-amber-500/20 text-amber-600"
                          : "bg-gray-500/20 text-gray-600"
                    }`}
                  >
                    {cz.severity === "hard" ? "Restricted" : cz.severity === "warning" ? "Warning" : "Info"}
                  </span>
                </div>
              </Popup>
            </Circle>
          ))}

        {/* Site result markers */}
        {siteMarkers.map((marker) => (
          <Marker
            key={marker.id}
            position={marker.position}
            icon={RESULT_ICONS[marker.rating]}
          >
            <Popup>
              <div className="text-xs space-y-1">
                <p className="font-semibold">{marker.label}</p>
                {marker.score !== undefined && (
                  <p className="text-muted-foreground">Score: {marker.score.toFixed(0)}/100</p>
                )}
                <span
                  className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    marker.rating === "excellent"
                      ? "bg-emerald-500/20 text-emerald-600"
                      : marker.rating === "viable"
                        ? "bg-amber-500/20 text-amber-600"
                        : "bg-red-500/20 text-red-600"
                  }`}
                >
                  {marker.rating.charAt(0).toUpperCase() + marker.rating.slice(1)}
                </span>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
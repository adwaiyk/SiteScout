"""
SiteScout — OpenStreetMap Infrastructure Proximity Service.

Queries the Overpass API to find power lines, substations, and major roads
within a configurable radius, then calculates precise distances in meters
using UTM projections.
"""

from __future__ import annotations

from typing import Any, Dict

import geopandas as gpd
import httpx
from pyproj import CRS
from shapely.geometry import LineString, Point

from app.config import get_settings

_settings = get_settings()


async def fetch_osm_infrastructure(
    lat: float, lon: float, radius_m: int = 10000
) -> Dict[str, Any]:
    """
    Query OpenStreetMap (Overpass API) within a radius around a coordinate
    to find power lines, substations, and major roads.

    Parameters
    ----------
    lat, lon : float
        Site coordinates.
    radius_m : int
        Search radius in meters (default 10 km).

    Returns
    -------
    dict
        Nearest distances in km and counts of each infrastructure type found.
    """
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["power"="substation"](around:{radius_m},{lat},{lon});
      way["power"="line"](around:{radius_m},{lat},{lon});
      way["highway"~"motorway|trunk|primary|secondary"](around:{radius_m},{lat},{lon});
    );
    out geom;
    """

    headers = {
        "User-Agent": "SiteScout_Renewable_App/1.0 (contact@sitescout.io)",
        "Referer": "https://sitescout.io",
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            response = await client.post(
                _settings.OVERPASS_URL, data={"data": overpass_query}
            )

            if response.status_code != 200:
                print(
                    f"Primary API returned {response.status_code}. "
                    f"Details: {response.text}"
                )
                print("Trying fallback mirror...")
                response = await client.post(
                    _settings.OVERPASS_MIRROR_URL, data={"data": overpass_query}
                )

            if response.status_code != 200:
                print(
                    f"Mirror also failed with status {response.status_code}. "
                    f"Details: {response.text}"
                )
                return _fallback_infrastructure_response()

            data = response.json()
            elements = data.get("elements", [])
            return _process_osm_elements(lat, lon, elements)

        except Exception as e:
            print(f"Error fetching OSM data: {e}")
            return _fallback_infrastructure_response()


def _process_osm_elements(
    lat: float, lon: float, elements: list
) -> Dict[str, Any]:
    """Categorize OSM elements and compute nearest distances in km."""
    site_point = Point(lon, lat)

    utm_zone = int((lon + 180) / 6) + 1
    crs_utm = CRS.from_dict({"proj": "utm", "zone": utm_zone, "south": lat < 0})

    site_gdf = gpd.GeoDataFrame(
        {"geometry": [site_point]}, crs="EPSG:4326"
    ).to_crs(crs_utm)
    site_geom_utm = site_gdf.geometry.iloc[0]

    substations: list[float] = []
    power_lines: list[float] = []
    roads: list[float] = []

    for elem in elements:
        elem_type = elem.get("type")
        tags = elem.get("tags", {})

        if elem_type == "node":
            geom = Point(elem["lon"], elem["lat"])
        elif elem_type == "way" and "geometry" in elem:
            coords = [(pt["lon"], pt["lat"]) for pt in elem["geometry"]]
            if len(coords) >= 2:
                geom = LineString(coords)
            else:
                continue
        else:
            continue

        feat_gdf = gpd.GeoDataFrame(
            {"geometry": [geom]}, crs="EPSG:4326"
        ).to_crs(crs_utm)
        feat_geom_utm = feat_gdf.geometry.iloc[0]
        dist_m = site_geom_utm.distance(feat_geom_utm)

        if tags.get("power") == "substation":
            substations.append(dist_m)
        elif tags.get("power") == "line":
            power_lines.append(dist_m)
        elif "highway" in tags:
            roads.append(dist_m)

    min_substation_dist = round(min(substations) / 1000.0, 2) if substations else None
    min_power_line_dist = round(min(power_lines) / 1000.0, 2) if power_lines else None
    min_road_dist = round(min(roads) / 1000.0, 2) if roads else None

    return {
        "nearest_substation_km": min_substation_dist,
        "nearest_power_line_km": min_power_line_dist,
        "nearest_major_road_km": min_road_dist,
        "substations_found_in_radius": len(substations),
        "power_lines_found_in_radius": len(power_lines),
        "roads_found_in_radius": len(roads),
    }


def _fallback_infrastructure_response() -> Dict[str, Any]:
    """Return a safe default when OSM queries fail."""
    return {
        "nearest_substation_km": None,
        "nearest_power_line_km": None,
        "nearest_major_road_km": None,
        "substations_found_in_radius": 0,
        "power_lines_found_in_radius": 0,
        "roads_found_in_radius": 0,
    }

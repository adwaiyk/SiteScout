import httpx
import asyncio
import geopandas as gpd
from shapely.geometry import Point, LineString
from pyproj import CRS
from typing import Dict, Any

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_MIRROR_URL = "https://overpass.kumi.systems/api/interpreter"

async def fetch_osm_infrastructure(lat: float, lon: float, radius_m: int = 10000) -> Dict[str, Any]:
    """
    Queries OpenStreetMap (Overpass API) within a radius (default 10km) around a 
    given coordinate to find power lines, substations, and major roads.
    Calculates proximity in meters.
    """
    # CRITICAL FIX: Changed 'out geometry;' to 'out geom;' to satisfy Overpass QL syntax
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
        "Referer": "https://sitescout.io"
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            response = await client.post(OVERPASS_URL, data={"data": overpass_query})
            
            if response.status_code != 200:
                print(f"Primary API returned {response.status_code}. Details: {response.text}")
                print("Trying fallback mirror...")
                response = await client.post(OVERPASS_MIRROR_URL, data={"data": overpass_query})

            if response.status_code != 200:
                print(f"Mirror also failed with status {response.status_code}. Details: {response.text}")
                return _fallback_infrastructure_response()

            data = response.json()
            elements = data.get("elements", [])
            return process_osm_elements(lat, lon, elements)

        except Exception as e:
            print(f"Error fetching OSM data: {e}")
            return _fallback_infrastructure_response()

def process_osm_elements(lat: float, lon: float, elements: list) -> Dict[str, Any]:
    site_point = Point(lon, lat)
    
    utm_zone = int((lon + 180) / 6) + 1
    crs_utm = CRS.from_dict({'proj': 'utm', 'zone': utm_zone, 'south': lat < 0})
    
    site_gdf = gpd.GeoDataFrame({'geometry': [site_point]}, crs="EPSG:4326").to_crs(crs_utm)
    site_geom_utm = site_gdf.geometry.iloc[0]

    substations = []
    power_lines = []
    roads = []

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

        feat_gdf = gpd.GeoDataFrame({'geometry': [geom]}, crs="EPSG:4326").to_crs(crs_utm)
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
        "roads_found_in_radius": len(roads)
    }

def _fallback_infrastructure_response() -> Dict[str, Any]:
    return {
        "nearest_substation_km": None,
        "nearest_power_line_km": None,
        "nearest_major_road_km": None,
        "substations_found_in_radius": 0,
        "power_lines_found_in_radius": 0,
        "roads_found_in_radius": 0
    }

if __name__ == "__main__":
    test_lat, test_lon = 19.7515, 75.7139
    print(f"Searching OpenStreetMap infrastructure around Lat: {test_lat}, Lon: {test_lon}...")
    
    result = asyncio.run(fetch_osm_infrastructure(test_lat, test_lon))
    
    print("\n--- OpenStreetMap Infrastructure Results ---")
    print(f"⚡ Nearest Substation: {result['nearest_substation_km']} km")
    print(f"🔌 Nearest Power Line: {result['nearest_power_line_km']} km")
    print(f"🛣️ Nearest Major Road: {result['nearest_major_road_km']} km")
    print(f"📊 Features Found (Substations: {result['substations_found_in_radius']}, Lines: {result['power_lines_found_in_radius']}, Roads: {result['roads_found_in_radius']})")
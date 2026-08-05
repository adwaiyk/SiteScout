import httpx
import asyncio
from typing import Dict, Any, List

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_MIRROR_URL = "https://overpass.kumi.systems/api/interpreter"

async def detect_land_use_conflicts(lat: float, lon: float, radius_m: int = 1500) -> Dict[str, Any]:
    """
    Scans a 1.5km radius around the site for protected areas, water bodies, 
    and agricultural/forest zones that could prevent or complicate deployment.
    """
    # Overpass QL query: searches for WDPA-aligned protected areas, nature reserves, water, and farmland
    overpass_query = f"""
    [out:json][timeout:25];
    (
      way["boundary"="protected_area"](around:{radius_m},{lat},{lon});
      relation["boundary"="protected_area"](around:{radius_m},{lat},{lon});
      way["leisure"="nature_reserve"](around:{radius_m},{lat},{lon});
      relation["leisure"="nature_reserve"](around:{radius_m},{lat},{lon});
      way["natural"="water"](around:{radius_m},{lat},{lon});
      way["landuse"~"forest|farmland"](around:{radius_m},{lat},{lon});
    );
    out tags;
    """

    headers = {
        "User-Agent": "SiteScout_Renewable_App/1.0 (contact@sitescout.io)",
        "Referer": "https://sitescout.io"
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            response = await client.post(OVERPASS_URL, data={"data": overpass_query})
            
            if response.status_code != 200:
                response = await client.post(OVERPASS_MIRROR_URL, data={"data": overpass_query})

            if response.status_code != 200:
                return _fallback_conflict_response()

            data = response.json()
            elements = data.get("elements", [])
            return _process_conflict_elements(elements)

        except Exception as e:
            print(f"Error fetching conflict data: {e}")
            return _fallback_conflict_response()

def _process_conflict_elements(elements: list) -> Dict[str, Any]:
    """
    Categorizes the overlapping polygons into specific risk flags.
    """
    hard_flags = []
    warnings = []
    
    for elem in elements:
        tags = elem.get("tags", {})
        name = tags.get("name", "Unnamed Zone")
        
        # Hard Flags: Cannot build here (Protected Areas, Reserves, Water)
        if tags.get("boundary") == "protected_area" or tags.get("leisure") == "nature_reserve":
            if f"Protected Area: {name}" not in hard_flags:
                hard_flags.append(f"Protected Area: {name}")
                
        elif tags.get("natural") == "water":
            if f"Water Body: {name}" not in hard_flags:
                hard_flags.append(f"Water Body: {name}")
                
        # Warnings: Can build, but requires extra permits or compensation (Forests, Farmland)
        elif tags.get("landuse") == "forest":
            if f"Forest Zone: {name}" not in warnings:
                warnings.append(f"Forest Zone: {name}")
                
        elif tags.get("landuse") == "farmland":
            if f"Agricultural Land: {name}" not in warnings:
                warnings.append(f"Agricultural Land: {name}")

    return {
        "is_unsuitable": len(hard_flags) > 0,
        "hard_flags": hard_flags,
        "warnings": warnings,
        "total_conflicts_found": len(hard_flags) + len(warnings)
    }

def _fallback_conflict_response() -> Dict[str, Any]:
    return {
        "is_unsuitable": False,
        "hard_flags": [],
        "warnings": ["Data unavailable - Manual survey required"],
        "total_conflicts_found": 0
    }

# Local execution test
if __name__ == "__main__":
    # Test coordinates (Let's check a known forest/water area just to see it trigger)
    # 19.9880, 73.5381 is near a dam/reservoir in Maharashtra
    test_lat, test_lon = 19.9880, 73.5381
    print(f"Scanning for Land-Use Conflicts around Lat: {test_lat}, Lon: {test_lon}...")
    
    result = asyncio.run(detect_land_use_conflicts(test_lat, test_lon))
    
    print("\n--- Land-Use Conflict Report ---")
    print(f"Site Unsuitable: {result['is_unsuitable']}")
    print(f"Hard Flags (No Build): {result['hard_flags']}")
    print(f"Warnings (Permit Risks): {result['warnings']}")
"""
SiteScout — Land-Use Conflict Detection Service.

Scans for protected areas, water bodies, and agricultural/forest zones
that could prevent or complicate renewable energy deployment.
"""

from __future__ import annotations

from typing import Any, Dict

import httpx

from app.config import get_settings

_settings = get_settings()


async def detect_land_use_conflicts(
    lat: float, lon: float, radius_m: int = 1500
) -> Dict[str, Any]:
    """
    Scan a configurable radius around the site for protected areas,
    water bodies, and agricultural/forest zones.

    Parameters
    ----------
    lat, lon : float
        Site coordinates.
    radius_m : int
        Search radius in meters (default 1.5 km).

    Returns
    -------
    dict
        Contains `is_unsuitable`, `hard_flags`, `warnings`, and counts.
    """
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
        "Referer": "https://sitescout.io",
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            response = await client.post(
                _settings.OVERPASS_URL, data={"data": overpass_query}
            )

            if response.status_code != 200:
                response = await client.post(
                    _settings.OVERPASS_MIRROR_URL, data={"data": overpass_query}
                )

            if response.status_code != 200:
                return _fallback_conflict_response()

            data = response.json()
            elements = data.get("elements", [])
            return _process_conflict_elements(elements)

        except Exception as e:
            print(f"Error fetching conflict data: {e}")
            return _fallback_conflict_response()


def _process_conflict_elements(elements: list) -> Dict[str, Any]:
    """Categorize overlapping polygons into hard flags and warnings."""
    hard_flags: list[str] = []
    warnings: list[str] = []

    for elem in elements:
        tags = elem.get("tags", {})
        name = tags.get("name", "Unnamed Zone")

        # Hard Flags: Cannot build here (Protected Areas, Reserves, Water)
        if tags.get("boundary") == "protected_area" or tags.get("leisure") == "nature_reserve":
            label = f"Protected Area: {name}"
            if label not in hard_flags:
                hard_flags.append(label)

        elif tags.get("natural") == "water":
            label = f"Water Body: {name}"
            if label not in hard_flags:
                hard_flags.append(label)

        # Warnings: Can build, but requires extra permits (Forests, Farmland)
        elif tags.get("landuse") == "forest":
            label = f"Forest Zone: {name}"
            if label not in warnings:
                warnings.append(label)

        elif tags.get("landuse") == "farmland":
            label = f"Agricultural Land: {name}"
            if label not in warnings:
                warnings.append(label)

    return {
        "is_unsuitable": len(hard_flags) > 0,
        "hard_flags": hard_flags,
        "warnings": warnings,
        "total_conflicts_found": len(hard_flags) + len(warnings),
    }


def _fallback_conflict_response() -> Dict[str, Any]:
    """Return a safe default when conflict queries fail."""
    return {
        "is_unsuitable": False,
        "hard_flags": [],
        "warnings": ["Data unavailable - Manual survey required"],
        "total_conflicts_found": 0,
    }

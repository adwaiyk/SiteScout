from __future__ import annotations
from typing import Any, Dict
import httpx
from app.config import get_settings
_settings = get_settings()

async def detect_land_use_conflicts(lat: float, lon: float, radius_m: int=1500) -> Dict[str, Any]:
    overpass_query = f'\n    [out:json][timeout:25];\n    (\n      way["boundary"="protected_area"](around:{radius_m},{lat},{lon});\n      relation["boundary"="protected_area"](around:{radius_m},{lat},{lon});\n      way["leisure"="nature_reserve"](around:{radius_m},{lat},{lon});\n      relation["leisure"="nature_reserve"](around:{radius_m},{lat},{lon});\n      way["natural"="water"](around:{radius_m},{lat},{lon});\n      way["landuse"~"forest|farmland"](around:{radius_m},{lat},{lon});\n    );\n    out tags;\n    '
    headers = {'User-Agent': 'SiteScout_Renewable_App/1.0 (contact@sitescout.io)', 'Referer': 'https://sitescout.io'}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            response = await client.post(_settings.OVERPASS_URL, data={'data': overpass_query})
            if response.status_code != 200:
                response = await client.post(_settings.OVERPASS_MIRROR_URL, data={'data': overpass_query})
            if response.status_code != 200:
                return _fallback_conflict_response()
            data = response.json()
            elements = data.get('elements', [])
            return _process_conflict_elements(elements)
        except Exception as e:
            print(f'Error fetching conflict data: {e}')
            return _fallback_conflict_response()

def _process_conflict_elements(elements: list) -> Dict[str, Any]:
    hard_flags: list[str] = []
    warnings: list[str] = []
    for elem in elements:
        tags = elem.get('tags', {})
        name = tags.get('name', 'Unnamed Zone')
        if tags.get('boundary') == 'protected_area' or tags.get('leisure') == 'nature_reserve':
            label = f'Protected Area: {name}'
            if label not in hard_flags:
                hard_flags.append(label)
        elif tags.get('natural') == 'water':
            label = f'Water Body: {name}'
            if label not in hard_flags:
                hard_flags.append(label)
        elif tags.get('landuse') == 'forest':
            label = f'Forest Zone: {name}'
            if label not in warnings:
                warnings.append(label)
        elif tags.get('landuse') == 'farmland':
            label = f'Agricultural Land: {name}'
            if label not in warnings:
                warnings.append(label)
    return {'is_unsuitable': len(hard_flags) > 0, 'hard_flags': hard_flags, 'warnings': warnings, 'total_conflicts_found': len(hard_flags) + len(warnings)}

def _fallback_conflict_response() -> Dict[str, Any]:
    return {'is_unsuitable': False, 'hard_flags': [], 'warnings': ['Data unavailable - Manual survey required'], 'total_conflicts_found': 0}

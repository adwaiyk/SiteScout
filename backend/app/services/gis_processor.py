from __future__ import annotations
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point

def create_site_buffer(lat: float, lon: float, radius_km: float=5.0) -> gpd.GeoDataFrame:
    site_point = Point(lon, lat)
    gdf = gpd.GeoDataFrame({'geometry': [site_point]}, crs='EPSG:4326')
    utm_zone = int((lon + 180) / 6) + 1
    crs_utm = CRS.from_dict({'proj': 'utm', 'zone': utm_zone, 'south': lat < 0})
    gdf_utm = gdf.to_crs(crs_utm)
    buffer_geom = gdf_utm.geometry.buffer(radius_km * 1000)
    gdf_buffer = gpd.GeoDataFrame({'geometry': buffer_geom}, crs=crs_utm).to_crs('EPSG:4326')
    return gdf_buffer

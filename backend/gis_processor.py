import geopandas as gpd
from shapely.geometry import Point
import pyproj
from pyproj import CRS

def create_site_buffer(lat: float, lon: float, radius_km: float = 5.0) -> gpd.GeoDataFrame:
    """
    Takes a latitude and longitude and creates a geographic boundary (buffer) 
    around it. Useful for checking infrastructure proximity and land-use conflicts.
    """
    # 1. Create a raw geographic point (Longitude goes first in GIS!)
    site_point = Point(lon, lat)
    
    # 2. Convert to a GeoDataFrame using standard GPS coordinates (EPSG:4326)
    gdf = gpd.GeoDataFrame({'geometry': [site_point]}, crs="EPSG:4326")
    
    # 3. GPS coordinates use degrees, but we need to measure in meters/kilometers.
    # We dynamically calculate the local UTM projection zone based on the longitude.
    utm_zone = int((lon + 180) / 6) + 1
    crs_utm = CRS.from_dict({'proj': 'utm', 'zone': utm_zone, 'south': lat < 0})
    
    # 4. Project to the metric system, create the buffer, and project back to GPS coords
    gdf_utm = gdf.to_crs(crs_utm)
    
    # Create the buffer (radius_km converted to meters)
    buffer_geom = gdf_utm.geometry.buffer(radius_km * 1000)
    
    # Project back to standard Lat/Lon (EPSG:4326) so it's easy to plot on a web map
    gdf_buffer = gpd.GeoDataFrame({'geometry': buffer_geom}, crs=crs_utm).to_crs("EPSG:4326")
    
    return gdf_buffer

# Quick local test block
if __name__ == "__main__":
    # Test with coordinates for a potential site in Maharashtra, India
    test_lat, test_lon = 19.7515, 75.7139 
    
    print(f"Generating 5km analysis zone for Lat: {test_lat}, Lon: {test_lon}...")
    site_boundary = create_site_buffer(test_lat, test_lon, radius_km=5.0)
    
    print("\nResulting Polygon Coordinates (GeoJSON format):")
    print(site_boundary.geometry.iloc[0])
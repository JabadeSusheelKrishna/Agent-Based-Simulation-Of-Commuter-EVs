import math
import random
from configurations import AREA_BOUNDS

# --- Helper Functions ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth in kilometers."""
    R = 6371  # Radius of Earth in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def get_random_location():
    """Generate random coordinates within the defined area."""
    lat = random.uniform(AREA_BOUNDS["min_lat"], AREA_BOUNDS["max_lat"])
    lon = random.uniform(AREA_BOUNDS["min_lon"], AREA_BOUNDS["max_lon"])
    return {"lat": lat, "lon": lon}
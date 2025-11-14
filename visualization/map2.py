import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np # Need numpy for random number generation

# --- Load GeoJSON files (Your original code) ---
# ... (roads, charging_points, agents loading)

# Load GeoJSON files
roads = gpd.read_file("../data/roads.geojson")
charging_points = gpd.read_file("../data/charging_points.geojson")
agents = gpd.read_file("../agent_locations.geojson")


# --- New Jitter Function ---
def jitter_points(gdf, amount=0.0001):
    """
    Adds a small, random offset (jitter) to the coordinates of a GeoDataFrame.
    The 'amount' controls the magnitude of the jitter.
    """
    # Create new geometry by adding random noise to the x and y coordinates
    # We use .copy() to ensure we are modifying a copy of the geometry column
    # The random noise is scaled by 'amount' (adjust this based on your map scale)
    jittered_geometry = gdf.geometry.copy()
    
    # Calculate the centroid coordinates
    x = jittered_geometry.x.values
    y = jittered_geometry.y.values
    
    # Add random jitter
    x_jittered = x + np.random.uniform(-amount, amount, size=len(gdf))
    y_jittered = y + np.random.uniform(-amount, amount, size=len(gdf))
    
    # Create new Point geometries from the jittered coordinates
    gdf['geometry'] = gpd.points_from_xy(x_jittered, y_jittered)
    return gdf

# --- Apply Jitter ONLY to the Agents Data (where overlap is an issue) ---
# Choose an appropriate jitter amount. A smaller number (like 0.0001) is often
# good for coordinate systems like WGS84 (lat/lon).
JITTER_AMOUNT = 0.00015
agents_jittered = jitter_points(agents.copy(), amount=JITTER_AMOUNT)

# --- Create the plot (Your original code structure, but using agents_jittered) ---
fig, ax = plt.subplots(figsize=(12, 10))

# Plot the road network
roads.plot(ax=ax, color='lightgray', linewidth=0.8, label='Roads')

# Plot charging stations
charging_points.plot(ax=ax, color='red', marker='^', markersize=90, label='Charging Stations', zorder=5)

# Define marker styles for each type of agent location
agent_styles = {
    'home': {'color': 'blue', 'marker': 'o', 'label': 'Homes'},
    'office': {'color': 'green', 'marker': 's', 'label': 'Offices'},
    'shop': {'color': 'orange', 'marker': 'D', 'label': 'Shops'},
    'restaurant': {'color': 'purple', 'marker': 'P', 'label': 'Restaurants'},
}

# Plot each type separately using the JITTERED data
for loc_type, style in agent_styles.items():
    # Filter the jittered data
    subset = agents_jittered[agents_jittered['type'].str.lower() == loc_type]
    if not subset.empty:
        # We also increase zorder to ensure points are drawn on top of roads
        subset.plot(ax=ax, color=style['color'], marker=style['marker'],
                    markersize=60, label=style['label'], alpha=0.7, zorder=10)


# Title and labels
plt.title(f"EV Simulation Map Layout (Agents Jittered by $\\pm${JITTER_AMOUNT})", fontsize=16, weight='bold')
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Add legend
plt.legend(title="Map Legend", loc='upper right', fontsize=10, title_fontsize=11)

# Optional: grid and styling
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()

# Display the map
plt.show()
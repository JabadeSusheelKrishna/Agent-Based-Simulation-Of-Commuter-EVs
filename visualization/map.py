import geopandas as gpd
import matplotlib.pyplot as plt

# Load GeoJSON files
roads = gpd.read_file("../data/roads.geojson")
charging_points = gpd.read_file("../data/charging_points.geojson")
agents = gpd.read_file("../agent_locations.geojson")

# Create the plot
fig, ax = plt.subplots(figsize=(12, 10))

# Plot the road network
roads.plot(ax=ax, color='lightgray', linewidth=0.8, label='Roads')

# Plot charging stations
charging_points.plot(ax=ax, color='red', marker='^', markersize=90, label='Charging Stations')

# Define marker styles for each type of agent location
agent_styles = {
    'home': {'color': 'blue', 'marker': 'o', 'label': 'Homes'},
    'office': {'color': 'green', 'marker': 's', 'label': 'Offices'},
    'shop': {'color': 'orange', 'marker': 'D', 'label': 'Shops'},
    'restaurant': {'color': 'purple', 'marker': 'P', 'label': 'Restaurants'},
}

# Plot each type separately
for loc_type, style in agent_styles.items():
    subset = agents[agents['type'].str.lower() == loc_type]
    if not subset.empty:
        subset.plot(ax=ax, color=style['color'], marker=style['marker'],
                    markersize=60, label=style['label'])

# Title and labels
plt.title("EV Simulation Map Layout", fontsize=16, weight='bold')
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Add legend
plt.legend(title="Map Legend", loc='upper right', fontsize=10, title_fontsize=11)

# Optional: grid and styling
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()

# Display the map
plt.show()

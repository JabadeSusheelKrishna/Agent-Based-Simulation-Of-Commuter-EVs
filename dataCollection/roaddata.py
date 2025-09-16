import osmnx as ox

# Center point of Gachibowli (approx)
lat, lon = 17.45430744606664, 78.36028648601219

# Get all roads within 2 km of this point
G = ox.graph_from_point((lat, lon), dist=1500, network_type="drive")

# Convert graph to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)

# Save road edges as GeoJSON
edges.to_file("roads.geojson", driver="GeoJSON")

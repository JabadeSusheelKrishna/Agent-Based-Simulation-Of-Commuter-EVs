
import json
import random
from typing import Dict, List, Tuple

# Assuming the RoadNetwork and Agent classes are available or can be imported.
# For this snippet, we'll re-implement the necessary parts to avoid circular imports or complex setup.

class MinimalRoadNetwork:
    def __init__(self, roads_file: str):
        self.nodes = {}  # {node_id: {'lat': float, 'lon': float}}
        self.load_road_network(roads_file)

    def load_road_network(self, filename: str):
        with open(filename, 'r') as f:
            data = json.load(f)

        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']

            u = props.get('u')
            v = props.get('v')

            if u is None or v is None:
                continue

            # Add nodes - taking the first coordinate of the LineString for 'u' and last for 'v'
            # This might not be perfectly accurate if nodes are shared across multiple LineStrings
            # but it's consistent with how app2.py seems to handle it.
            if len(coords) > 0 and u not in self.nodes:
                self.nodes[u] = {'lat': coords[0][1], 'lon': coords[0][0]}
            if len(coords) > 1 and v not in self.nodes:
                self.nodes[v] = {'lat': coords[-1][1], 'lon': coords[-1][0]}

class MinimalAgent:
    def __init__(self, agent_id: int, home_location: int, office_location: int,
                 shop: int, restaurant: int):
        self.id = agent_id
        self.home_location = home_location
        self.office_location = office_location
        self.shop = shop
        self.restaurant = restaurant

def generate_agent_locations_geojson(roads_file: str, num_agents: int, output_file: str = 'agent_locations.geojson'):
    road_network = MinimalRoadNetwork(roads_file)
    node_ids = list(road_network.nodes.keys())
    
    agents: List[MinimalAgent] = []
    for i in range(num_agents):
        home = random.choice(node_ids)
        office = random.choice([n for n in node_ids if n != home])
        
        possible_nodes = [n for n in node_ids if n not in (home, office)]
        if possible_nodes:
            shop = random.choice(possible_nodes)
            remaining = [n for n in possible_nodes if n != shop]
            restaurant = random.choice(remaining or possible_nodes)
        else:
            shop = home
            restaurant = office
        
        agents.append(MinimalAgent(i, home, office, shop, restaurant))

    features = []
    for agent in agents:
        # Home location
        home_coords = road_network.nodes.get(agent.home_location)
        if home_coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "agent_id": agent.id,
                    "type": "home",
                    "node_id": agent.home_location
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [home_coords['lon'], home_coords['lat']]
                }
            })
        
        # Office location
        office_coords = road_network.nodes.get(agent.office_location)
        if office_coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "agent_id": agent.id,
                    "type": "office",
                    "node_id": agent.office_location
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [office_coords['lon'], office_coords['lat']]
                }
            })

        # Shop location
        shop_coords = road_network.nodes.get(agent.shop)
        if shop_coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "agent_id": agent.id,
                    "type": "shop",
                    "node_id": agent.shop
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [shop_coords['lon'], shop_coords['lat']]
                }
            })

        # Restaurant location
        restaurant_coords = road_network.nodes.get(agent.restaurant)
        if restaurant_coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "agent_id": agent.id,
                    "type": "restaurant",
                    "node_id": agent.restaurant
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [restaurant_coords['lon'], restaurant_coords['lat']]
                }
            })

    geojson_output = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_file, 'w') as f:
        json.dump(geojson_output, f, indent=2)
    print(f"Generated agent locations saved to {output_file}")

if __name__ == "__main__":
    # Example usage:
    generate_agent_locations_geojson(
        roads_file='data/roads.geojson',
        num_agents=5,  # You can adjust the number of agents
        output_file='agent_locations.geojson'
    )

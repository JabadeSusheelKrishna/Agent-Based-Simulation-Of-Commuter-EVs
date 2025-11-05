import json
import os
from typing import List, Dict, Any
from ev_simulation import EVSimulation, Location, CONFIG

class AgentInitializer:
    """
    A class to initialize and manage agent and office locations.
    It can save locations to a JSON file and load them for consistent simulation runs.
    """
    
    def __init__(self, roads_file: str = None, num_agents: int = None):
        """
        Initialize the AgentInitializer with road network and number of agents.
        
        Args:
            roads_file (str, optional): Path to the roads GeoJSON file. Defaults to None (uses config).
            num_agents (int, optional): Number of agents to generate. Defaults to None (uses config).
        """
        # Initialize simulation to access road network and generation methods
        self.sim = EVSimulation(roads_file=roads_file or CONFIG['paths']['roads'])
        self.num_agents = num_agents or CONFIG['agent']['count']
    
    def generate_locations(self) -> Dict[str, Any]:
        """
        Generate random locations for agents and offices.
        
        Returns:
            Dict: A dictionary containing home and office locations for all agents.
        """
        # Generate locations for all agents (2 locations per agent: home and office)
        locations = self.sim.generate_random_locations(self.num_agents * 2)
        
        # Convert locations to a serializable format
        locations_data = {
            'homes': [],
            'offices': [],
            'num_agents': self.num_agents
        }
        
        for i in range(self.num_agents):
            home = locations[i * 2]
            office = locations[i * 2 + 1]
            
            locations_data['homes'].append({
                'lat': home.lat,
                'lon': home.lon,
                'node_id': home.node_id
            })
            
            locations_data['offices'].append({
                'lat': office.lat,
                'lon': office.lon,
                'node_id': office.node_id
            })
        
        return locations_data
    
    def save_locations_to_file(self, filepath: str = 'Locations.json'):
        """
        Generate and save locations to a JSON file.
        
        Args:
            filepath (str, optional): Path to save the locations file. Defaults to 'Locations.json'.
        """
        locations_data = self.generate_locations()
        
        with open(filepath, 'w') as f:
            json.dump(locations_data, f, indent=2)
        
        print(f"Locations saved to {os.path.abspath(filepath)}")
    
    @staticmethod
    def load_locations(filepath: str = 'Locations.json') -> Dict[str, Any]:
        """
        Load locations from a JSON file.
        
        Args:
            filepath (str, optional): Path to the locations file. Defaults to 'Locations.json'.
            
        Returns:
            Dict: The loaded locations data.
        """
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def create_agents_from_locations(sim: 'EVSimulation', locations_data: Dict[str, Any]) -> None:
        """
        Create agents in the simulation using pre-defined locations.
        
        Args:
            sim: The simulation instance.
            locations_data: The locations data loaded from JSON.
        """
        from ev_simulation import EVAgent  # Import here to avoid circular imports
        
        num_agents = locations_data.get('num_agents', 0)
        homes = locations_data.get('homes', [])
        offices = locations_data.get('offices', [])
        
        if len(homes) < num_agents or len(offices) < num_agents:
            raise ValueError("Insufficient location data for the requested number of agents")
        
        for i in range(num_agents):
            home_data = homes[i]
            office_data = offices[i]
            
            home = Location(
                lat=home_data['lat'],
                lon=home_data['lon'],
                node_id=home_data.get('node_id')
            )
            
            office = Location(
                lat=office_data['lat'],
                lon=office_data['lon'],
                node_id=office_data.get('node_id')
            )
            
            # Create agent using EVAgent class directly
            agent = EVAgent(i, home, office, sim.road_network)
            sim.agents.append(agent)


def generate_locations_file(num_agents: int = None, output_file: str = 'Locations.json'):
    """
    Helper function to generate and save locations to a file.
    
    Args:
        num_agents (int, optional): Number of agents to generate. Defaults to None (uses config).
        output_file (str, optional): Path to save the locations file. Defaults to 'Locations.json'.
    """
    initializer = AgentInitializer(num_agents=num_agents)
    initializer.save_locations_to_file(output_file)


if __name__ == "__main__":
    # Generate and save locations when run directly
    generate_locations_file()

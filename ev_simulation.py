import json
import networkx as nx
import numpy as np
import random
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import time

@dataclass
class Location:
    """Represents a geographic location with coordinates"""
    lat: float
    lon: float
    node_id: Optional[int] = None
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance in meters using geodesic distance"""
        return geodesic((self.lat, self.lon), (other.lat, other.lon)).meters

class ChargingStation:
    """Represents a charging station with limited capacity and queue management"""
    
    def __init__(self, location: Location, name: str, max_ports: int = 4):
        self.location = location
        self.name = name
        self.max_ports = max_ports
        self.occupied_ports = 0
        self.queue = deque()  # Queue of agents waiting to charge
        self.charging_agents = []  # Currently charging agents
        
    def is_available(self) -> bool:
        """Check if charging station has available ports"""
        return self.occupied_ports < self.max_ports
    
    def add_to_queue(self, agent: 'EVAgent'):
        """Add agent to waiting queue"""
        if agent not in self.queue:
            self.queue.append(agent)
    
    def start_charging(self, agent: 'EVAgent') -> bool:
        """Start charging an agent if port is available"""
        if self.is_available():
            self.occupied_ports += 1
            self.charging_agents.append(agent)
            agent.start_charging()
            return True
        return False
    
    def finish_charging(self, agent: 'EVAgent'):
        """Agent finishes charging and leaves"""
        if agent in self.charging_agents:
            self.charging_agents.remove(agent)
            self.occupied_ports -= 1
            agent.finish_charging()
            
            # Start charging next agent in queue if available
            if self.queue and self.is_available():
                next_agent = self.queue.popleft()
                self.start_charging(next_agent)
    
    def update(self):
        """Update charging station state - process charging agents"""
        finished_agents = []
        for agent in self.charging_agents:
            if agent.is_fully_charged():
                finished_agents.append(agent)
        
        for agent in finished_agents:
            self.finish_charging(agent)

class EVAgent:
    """Represents an EV commuter agent"""
    
    def __init__(self, agent_id: int, home: Location, office: Location, road_network: nx.Graph):
        self.agent_id = agent_id
        self.home = home
        self.office = office
        self.current_location = home
        self.road_network = road_network
        
        # Battery management
        self.battery_capacity = 100.0  # kWh
        self.current_battery = random.uniform(20, 80)  # Start with lower random charge
        self.low_battery_threshold = 30.0
        self.consumption_rate = 2.0  # kWh per km (higher consumption for demo)
        self.charging_rate = 50.0  # kWh per hour (fast charging)
        
        # State management
        self.state = "at_home"  # at_home, commuting_to_office, at_office, commuting_to_home, charging, waiting_to_charge
        self.destination = None
        self.path = []
        self.path_index = 0
        self.charging_start_time = None
        self.schedule_offset = random.uniform(0, 60)  # Random start time offset in minutes
        
    def needs_charging(self) -> bool:
        """Check if agent needs to charge"""
        return self.current_battery < self.low_battery_threshold
    
    def start_charging(self):
        """Start charging process"""
        self.state = "charging"
        self.charging_start_time = time.time()
    
    def finish_charging(self):
        """Finish charging and resume journey"""
        self.state = "commuting_to_office" if self.destination == self.office else "commuting_to_home"
        self.charging_start_time = None
    
    def is_fully_charged(self) -> bool:
        """Check if battery is fully charged or charging time is sufficient"""
        if self.charging_start_time is None:
            return False
        
        charging_time_hours = (time.time() - self.charging_start_time) / 3600
        charge_added = charging_time_hours * self.charging_rate
        
        # Charge to 80% or for at least 15 minutes (whichever comes first)
        return (self.current_battery + charge_added >= 80.0) or (charging_time_hours >= 0.25)
    
    def update_battery_after_charging(self):
        """Update battery level after charging"""
        if self.charging_start_time:
            charging_time_hours = (time.time() - self.charging_start_time) / 3600
            charge_added = charging_time_hours * self.charging_rate
            self.current_battery = min(100.0, self.current_battery + charge_added)
    
    def find_path_to_destination(self, destination: Location) -> List[int]:
        """Find shortest path to destination using road network"""
        try:
            # Find nearest nodes to current location and destination
            current_node = self.find_nearest_node(self.current_location)
            dest_node = self.find_nearest_node(destination)
            
            if current_node is None or dest_node is None:
                return []
            
            # Use NetworkX to find shortest path
            path = nx.shortest_path(self.road_network, current_node, dest_node, weight='length')
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def find_nearest_node(self, location: Location) -> Optional[int]:
        """Find nearest road network node to a location"""
        min_distance = float('inf')
        nearest_node = None
        
        for node in self.road_network.nodes():
            node_data = self.road_network.nodes[node]
            if 'x' in node_data and 'y' in node_data:
                node_location = Location(node_data['y'], node_data['x'])
                distance = location.distance_to(node_location)
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node
        
        return nearest_node
    
    def move_along_path(self):
        """Move agent along the current path"""
        if not self.path or self.path_index >= len(self.path) - 1:
            return False
        
        current_node = self.path[self.path_index]
        next_node = self.path[self.path_index + 1]
        
        # Calculate distance and battery consumption
        if self.road_network.has_edge(current_node, next_node):
            edge_data = self.road_network[current_node][next_node]
            distance_km = edge_data.get('length', 100) / 1000  # Convert to km
            battery_consumed = distance_km * self.consumption_rate
            
            # Update battery and position
            self.current_battery -= battery_consumed
            self.path_index += 1
            
            # Update current location
            node_data = self.road_network.nodes[next_node]
            self.current_location = Location(node_data['y'], node_data['x'], next_node)
            
            return True
        
        return False
    
    def update(self, current_time_minutes: int, charging_stations: List[ChargingStation]):
        """Update agent state based on time and conditions"""
        
        # Handle charging state
        if self.state == "charging":
            if self.is_fully_charged():
                self.update_battery_after_charging()
                # Find the charging station and finish charging
                for station in charging_stations:
                    if self in station.charging_agents:
                        station.finish_charging(self)
                        break
            return
        
        # Handle waiting to charge state
        if self.state == "waiting_to_charge":
            return
        
        # Schedule-based state transitions
        morning_commute_start = 8 * 60 + self.schedule_offset  # 8 AM + offset
        evening_commute_start = 17 * 60 + self.schedule_offset  # 5 PM + offset
        
        # Morning commute: home to office
        if (self.state == "at_home" and 
            current_time_minutes >= morning_commute_start and 
            current_time_minutes < morning_commute_start + 120):  # 2-hour window
            
            self.destination = self.office
            self.path = self.find_path_to_destination(self.destination)
            self.path_index = 0
            self.state = "commuting_to_office"
        
        # Evening commute: office to home
        elif (self.state == "at_office" and 
              current_time_minutes >= evening_commute_start and 
              current_time_minutes < evening_commute_start + 120):  # 2-hour window
            
            self.destination = self.home
            self.path = self.find_path_to_destination(self.destination)
            self.path_index = 0
            self.state = "commuting_to_home"
        
        # Handle commuting states
        if self.state in ["commuting_to_office", "commuting_to_home"]:
            # Check if needs charging
            if self.needs_charging():
                nearest_station = self.find_nearest_charging_station(charging_stations)
                if nearest_station:
                    if nearest_station.is_available():
                        nearest_station.start_charging(self)
                    else:
                        nearest_station.add_to_queue(self)
                        self.state = "waiting_to_charge"
                return
            
            # Continue moving along path
            if self.path:
                moved = self.move_along_path()
                if not moved or self.path_index >= len(self.path) - 1:
                    # Reached destination
                    if self.destination == self.office:
                        self.state = "at_office"
                    else:
                        self.state = "at_home"
                    self.path = []
                    self.path_index = 0
    
    def find_nearest_charging_station(self, charging_stations: List[ChargingStation]) -> Optional[ChargingStation]:
        """Find the nearest charging station"""
        if not charging_stations:
            return None
        
        min_distance = float('inf')
        nearest_station = None
        
        for station in charging_stations:
            distance = self.current_location.distance_to(station.location)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station

class EVSimulation:
    """Main simulation class"""
    
    def __init__(self, roads_file: str, charging_points_file: str):
        self.road_network = self.load_road_network(roads_file)
        self.charging_stations = self.load_charging_stations(charging_points_file)
        self.agents = []
        self.current_time = 0  # Time in minutes from start of day
        self.simulation_speed = 10  # Minutes per simulation step
        
    def load_road_network(self, roads_file: str) -> nx.Graph:
        """Load road network from GeoJSON and create NetworkX graph"""
        with open(roads_file, 'r') as f:
            roads_data = json.load(f)
        
        G = nx.Graph()
        
        # Add nodes and edges from road features
        for feature in roads_data['features']:
            if feature['geometry']['type'] == 'LineString':
                properties = feature['properties']
                u_node = properties['u']
                v_node = properties['v']
                length = properties.get('length', 100)  # Default length if missing
                
                # Add nodes with coordinates
                coords = feature['geometry']['coordinates']
                start_coord = coords[0]
                end_coord = coords[-1]
                
                G.add_node(u_node, x=start_coord[0], y=start_coord[1])
                G.add_node(v_node, x=end_coord[0], y=end_coord[1])
                
                # Add edge with length as weight
                G.add_edge(u_node, v_node, length=length)
        
        return G
    
    def load_charging_stations(self, charging_points_file: str) -> List[ChargingStation]:
        """Load charging stations from GeoJSON"""
        with open(charging_points_file, 'r') as f:
            charging_data = json.load(f)
        
        stations = []
        for feature in charging_data['features']:
            if feature['geometry']['type'] == 'Point':
                coords = feature['geometry']['coordinates']
                name = feature['properties'].get('name', 'Unknown')
                location = Location(coords[1], coords[0])  # lat, lon
                
                # Random number of ports between 2-6
                max_ports = random.randint(2, 6)
                station = ChargingStation(location, name, max_ports)
                stations.append(station)
        
        return stations
    
    def generate_random_locations(self, num_locations: int) -> List[Location]:
        """Generate random locations on the road network"""
        locations = []
        nodes = list(self.road_network.nodes())
        
        for temp in range(num_locations):
            node = random.choice(nodes)
            node_data = self.road_network.nodes[node]
            location = Location(node_data['y'], node_data['x'], node)
            locations.append(location)
            if temp % 2 == 1 and temp > 1:                  # making sure that there is only one office
                locations[temp] = locations[temp-2]
        
        return locations
    
    def create_agents(self, num_agents: int):
        """Create EV agents with random home and office locations"""
        locations = self.generate_random_locations(num_agents * 2)
        
        for i in range(num_agents):
            home = locations[i * 2]             # even places
            office = locations[i * 2 + 1]       # Odd places
            agent = EVAgent(i, home, office, self.road_network)
            self.agents.append(agent)
    
    def step(self):
        """Execute one simulation step"""
        # Update all agents
        for agent in self.agents:
            agent.update(self.current_time, self.charging_stations)
        
        # Update all charging stations
        for station in self.charging_stations:
            station.update()
        
        # Advance time
        self.current_time += self.simulation_speed
    
    def get_simulation_stats(self) -> Dict:
        """Get current simulation statistics"""
        stats = {
            'time': self.current_time,
            'agents_at_home': sum(1 for a in self.agents if a.state == 'at_home'),
            'agents_at_office': sum(1 for a in self.agents if a.state == 'at_office'),
            'agents_commuting': sum(1 for a in self.agents if 'commuting' in a.state),
            'agents_charging': sum(1 for a in self.agents if a.state == 'charging'),
            'agents_waiting': sum(1 for a in self.agents if a.state == 'waiting_to_charge'),
            'avg_battery': np.mean([a.current_battery for a in self.agents]),
            'low_battery_agents': sum(1 for a in self.agents if a.needs_charging()),
            'total_charging_ports': sum(s.max_ports for s in self.charging_stations),
            'occupied_ports': sum(s.occupied_ports for s in self.charging_stations),
            'queue_lengths': [len(s.queue) for s in self.charging_stations]
        }
        return stats
    
    def print_stats(self):
        """Print current simulation statistics"""
        stats = self.get_simulation_stats()
        hours = stats['time'] // 60
        minutes = stats['time'] % 60
        
        print(f"\n=== Simulation Time: {hours:02d}:{minutes:02d} ===")
        print(f"Agents at home: {stats['agents_at_home']}")
        print(f"Agents at office: {stats['agents_at_office']}")
        print(f"Agents commuting: {stats['agents_commuting']}")
        print(f"Agents charging: {stats['agents_charging']}")
        print(f"Agents waiting to charge: {stats['agents_waiting']}")
        print(f"Average battery level: {stats['avg_battery']:.1f}%")
        print(f"Low battery agents: {stats['low_battery_agents']}")
        print(f"Charging ports occupied: {stats['occupied_ports']}/{stats['total_charging_ports']}")
        print(f"Queue lengths: {stats['queue_lengths']}")
    
    def run_simulation(self, duration_hours: int = 24, print_interval: int = 60):
        """Run the simulation for specified duration"""
        duration_minutes = duration_hours * 60
        
        print("Starting EV Commuter Simulation...")
        print(f"Number of agents: {len(self.agents)}")
        print(f"Number of charging stations: {len(self.charging_stations)}")
        print(f"Simulation duration: {duration_hours} hours")
        
        step_count = 0
        while self.current_time < duration_minutes:
            self.step()
            step_count += 1
            
            # Print stats at specified intervals
            if step_count % (print_interval // self.simulation_speed) == 0:
                self.print_stats()
        
        print("\nSimulation completed!")
        self.print_stats()

def main():
    """Main function to run the simulation"""
    # Initialize simulation
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    
    # Create agents
    num_agents = 20  # Start with 20 agents for testing
    sim.create_agents(num_agents)
    
    # Run simulation for one day
    sim.run_simulation(duration_hours=24, print_interval=120)  # Print stats every 2 hours

if __name__ == "__main__":
    main()

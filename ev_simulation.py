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
    
    def start_charging(self, agent: 'EVAgent', current_sim_time: int = None) -> bool:
        """Start charging an agent if port is available"""
        if self.is_available():
            self.occupied_ports += 1
            self.charging_agents.append(agent)
            agent.start_charging(current_sim_time)
            return True
        return False
    
    def finish_charging(self, agent: 'EVAgent'):
        """Agent finishes charging and leaves"""
        if agent in self.charging_agents:
            self.charging_agents.remove(agent)
            self.occupied_ports -= 1
            agent.finish_charging()
    
    def process_queue(self, current_sim_time: int = None):
        """Process waiting queue - separate method to handle timing properly"""
        while self.queue and self.is_available():
            next_agent = self.queue.popleft()
            self.start_charging(next_agent, current_sim_time)
    
    def update(self, current_sim_time: int = None):
        """Update charging station state - process charging agents"""
        finished_agents = []
        for agent in self.charging_agents:
            if agent.is_fully_charged(current_sim_time):
                finished_agents.append(agent)
        
        for agent in finished_agents:
            self.finish_charging(agent)
        
        # Process queue after finishing agents to maintain proper synchronization
        self.process_queue(current_sim_time)

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
        self.consumption_rate = 5.0  # kWh per km (realistic consumption rate)
        self.charging_rate = 50.0  # kWh per hour (fast charging)
        
        # Movement parameters (in km/h and km)
        self.speed = 25.0  # Average speed in km/h
        self.distance_this_step = 0.0  # Distance to cover in current step
        self.partial_edge_progress = 0.0  # For partial movement along an edge
        
        # State management
        self.state = "at_home"  # at_home, commuting_to_office, at_office, commuting_to_home, charging, waiting_to_charge
        self.destination = None
        self.path = []
        self.path_index = 0
        self.charging_start_time = None
        self.charging_start_sim_time = None  # Track simulation time when charging started
        self.schedule_offset = random.uniform(0, 60)  # Random start time offset in minutes
        
    def needs_charging(self) -> bool:
        """Check if agent needs to charge"""
        return self.current_battery < self.low_battery_threshold
    
    def start_charging(self, current_sim_time: int = None):
        """Start charging process"""
        self.state = "charging"
        self.charging_start_time = time.time()
        self.charging_start_sim_time = current_sim_time
    
    def finish_charging(self):
        """Finish charging and resume journey"""
        # Resume the appropriate commuting state based on destination
        if self.destination == self.office:
            self.state = "commuting_to_office"
        elif self.destination == self.home:
            self.state = "commuting_to_home"
        else:
            # If no destination set, determine state based on current time and location
            # Check if closer to home or office to determine appropriate state
            distance_to_home = self.current_location.distance_to(self.home)
            distance_to_office = self.current_location.distance_to(self.office)
            
            if distance_to_home < distance_to_office:
                self.state = "at_home"
            else:
                self.state = "at_office"
        
        self.charging_start_time = None
        self.charging_start_sim_time = None
    
    def is_fully_charged(self, current_sim_time: int = None) -> bool:
        """Check if battery is fully charged or charging time is sufficient"""
        if self.charging_start_sim_time is None:
            return False
        
        if current_sim_time is None:
            return False
            
        charging_time_minutes = current_sim_time - self.charging_start_sim_time
        charging_time_hours = charging_time_minutes / 60.0
        charge_added = charging_time_hours * self.charging_rate
        
        # Charge to 80% or for at least 30 minutes of simulation time (whichever comes first)
        return (self.current_battery + charge_added >= 80.0) or (charging_time_minutes >= 30)
    
    def update_battery_after_charging(self, current_sim_time: int = None):
        """Update battery level after charging"""
        if self.charging_start_sim_time and current_sim_time:
            charging_time_minutes = current_sim_time - self.charging_start_sim_time
            charging_time_hours = charging_time_minutes / 60.0
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
        """Move agent along the current path based on speed and time step"""
        if not self.path or self.path_index >= len(self.path) - 1:
            return False
        
        # Calculate distance to move this step (in km)
        # speed is in km/h, simulation_step is in minutes, so convert to km/step
        simulation_step_minutes = 10  # Should match the simulation step in EVSimulation.step()
        distance_this_step = (self.speed / 60.0) * simulation_step_minutes  # km
        distance_remaining = distance_this_step
        
        while distance_remaining > 0 and self.path_index < len(self.path) - 1:
            current_node = self.path[self.path_index]
            next_node = self.path[self.path_index + 1]
            
            if not self.road_network.has_edge(current_node, next_node):
                self.path_index += 1
                continue
                
            edge_data = self.road_network[current_node][next_node]
            edge_length = edge_data.get('length', 100)  # in meters
            edge_length_km = edge_length / 1000.0  # convert to km
            
            # Calculate how much of this edge we can cover
            edge_remaining = edge_length_km - self.partial_edge_progress
            distance_to_move = min(distance_remaining, edge_remaining)
            
            # Update position along edge
            self.partial_edge_progress += distance_to_move
            distance_remaining -= distance_to_move
            
            # Calculate battery consumption
            battery_consumed = distance_to_move * self.consumption_rate
            self.current_battery = max(0, self.current_battery - battery_consumed)
            
            # If we've reached the end of this edge
            if self.partial_edge_progress >= edge_length_km - 1e-6:  # Small epsilon for floating point comparison
                self.path_index += 1
                self.partial_edge_progress = 0.0
                
                # Update current location to the next node
                node_data = self.road_network.nodes[next_node]
                self.current_location = Location(node_data['y'], node_data['x'], next_node)
            else:
                # Calculate intermediate position along the edge
                ratio = self.partial_edge_progress / edge_length_km
                start_node_data = self.road_network.nodes[current_node]
                end_node_data = self.road_network.nodes[next_node]
                
                # Linear interpolation of coordinates
                lat = start_node_data['y'] + ratio * (end_node_data['y'] - start_node_data['y'])
                lon = start_node_data['x'] + ratio * (end_node_data['x'] - start_node_data['x'])
                self.current_location = Location(lat, lon, node_id=None)  # Not at a node
        
        return distance_remaining < distance_this_step  # Return True if any movement occurred
    
    def update(self, current_time_minutes: int, charging_stations: List[ChargingStation]):
        """Update agent state based on time and conditions"""
        
        # Handle charging state
        if self.state == "charging":
            if self.is_fully_charged(current_time_minutes):
                self.update_battery_after_charging(current_time_minutes)
                # Find the charging station and finish charging
                for station in charging_stations:
                    if self in station.charging_agents:
                        station.finish_charging(self)
                        break
            return
        
        # Handle waiting to charge state
        if self.state == "waiting_to_charge":
            return
        
        # Schedule-based state transitions (handle multi-day simulation)
        # Get time within current day (0-1439 minutes)
        time_in_day = current_time_minutes % (24 * 60)
        
        morning_commute_start = 8 * 60 + self.schedule_offset  # 8 AM + offset
        evening_commute_start = 17 * 60 + self.schedule_offset  # 5 PM + offset
        
        # Handle schedule offset wrapping around midnight
        morning_commute_start = morning_commute_start % (24 * 60)
        evening_commute_start = evening_commute_start % (24 * 60)
        
        # Morning commute: home to office
        if (self.state == "at_home" and 
            time_in_day >= morning_commute_start and 
            time_in_day < morning_commute_start + 120):  # 2-hour window
            
            self.destination = self.office
            self.path = self.find_path_to_destination(self.destination)
            self.path_index = 0
            self.state = "commuting_to_office"
        
        # Evening commute: office to home
        elif (self.state == "at_office" and 
              time_in_day >= evening_commute_start and 
              time_in_day < evening_commute_start + 120):  # 2-hour window
            
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
                        nearest_station.start_charging(self, current_time_minutes)
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
            station.update(self.current_time)
        
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

import json
import math
import heapq
import random
from enum import Enum
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# ===== ENUMS =====
class AgentState(Enum):
    AT_HOME = "AT_HOME"
    AT_OFFICE = "AT_OFFICE"
    MOVING_TO_OFFICE = "MOVING_TO_OFFICE"
    MOVING_TO_HOME = "MOVING_TO_HOME"
    MOVING_TO_CHARGING = "MOVING_TO_CHARGING"
    CHARGING = "CHARGING"
    WAITING_TO_CHARGE = "WAITING_TO_CHARGE"
    STRANDED = "STRANDED"
    AT_CHARGING_STATION = "AT_CHARGING_STATION"
    MOVING_TO_SHOP = "MOVING_TO_SHOP"
    AT_SHOP = "AT_SHOP"
    MOVING_TO_RESTAURANT = "MOVING_TO_RESTAURANT"
    AT_RESTAURANT = "AT_RESTAURANT"

# ===== HELPER FUNCTIONS =====
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def find_nearest_node(lat: float, lon: float, nodes: Dict) -> int:
    """Find the nearest node to a given lat/lon coordinate"""
    min_dist = float('inf')
    nearest_node = None
    
    for node_id, coords in nodes.items():
        dist = haversine_distance(lat, lon, coords['lat'], coords['lon'])
        if dist < min_dist:
            min_dist = dist
            nearest_node = node_id
    
    return nearest_node

# ===== ROAD NETWORK CLASS =====
class RoadNetwork:
    def __init__(self):
        self.nodes = {}  # {node_id: {'lat': float, 'lon': float}}
        self.edges = defaultdict(list)  # {node_id: [(neighbor_id, distance, speed_limit)]}
        self.edge_properties = {}  # {(u, v): {'distance': float, 'speed_limit': float}}
    
    def add_node(self, node_id: int, lat: float, lon: float):
        """Add a node to the network"""
        if node_id not in self.nodes:
            self.nodes[node_id] = {'lat': lat, 'lon': lon}
    
    def add_edge(self, u: int, v: int, distance: float, speed_limit: float):
        """Add an edge between two nodes"""
        self.edges[u].append((v, distance, speed_limit))
        self.edges[v].append((u, distance, speed_limit))  # Bidirectional
        self.edge_properties[(u, v)] = {'distance': distance, 'speed_limit': speed_limit}
        self.edge_properties[(v, u)] = {'distance': distance, 'speed_limit': speed_limit}
    
    def get_edge_properties(self, u: int, v: int) -> Dict:
        """Get properties of an edge"""
        return self.edge_properties.get((u, v), {'distance': 0, 'speed_limit': 30})
    
    def dijkstra(self, start: int, end: int) -> Tuple[List[int], float]:
        """Find shortest path using Dijkstra's algorithm"""
        if start == end:
            return [start], 0
        
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        previous = {node: None for node in self.nodes}
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end:
                break
            
            for neighbor, distance, _ in self.edges[current]:
                if neighbor in visited:
                    continue
                
                new_dist = current_dist + distance
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        if distances[end] == float('inf'):
            return [], float('inf')
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        return path, distances[end]

# ===== AGENT CLASS =====
class Agent:
    def __init__(self, agent_id: int, home_location: int, office_location: int, 
                 battery_capacity: float, energy_consumption_rate: float):
        self.id = agent_id
        self.home_location = home_location
        self.office_location = office_location
        self.current_position = home_location
        self.current_battery_percentage = random.uniform(30, 40)
        self.battery_capacity = battery_capacity
        self.energy_consumption_rate = energy_consumption_rate
        self.battery_threshold = random.uniform(25, 30)
        self.morning_offset = random.randint(-30, 30)
        self.evening_offset = random.randint(-30, 30)
        self.current_state = AgentState.AT_HOME
        self.current_target = None
        self.previous_target = None
        self.current_path = []
        self.path_index = 0
        self.speed = 0
        self.total_distance_traveled = 0
        self.charging_start_time = None
        # New fields for shop & restaurant scheduling
        self.shop = None  # node id for shop
        self.restaurant = None  # node id for restaurant
        # times are minute-of-day (0-1439)
        self.shop_start_time = None
        self.shop_end_time = None
        self.restaurant_start_time = None
        self.restaurant_end_time = None
        # weekday (0=Monday .. 6=Sunday) that the agent visits shop/restaurant
        self.Day = None
    
    def update_battery(self, distance_traveled: float):
        """Decrease battery based on distance traveled"""
        energy_used = distance_traveled * self.energy_consumption_rate
        battery_percentage_used = (energy_used / self.battery_capacity) * 100
        self.current_battery_percentage -= battery_percentage_used
        self.current_battery_percentage = max(0, self.current_battery_percentage)
    
    def needs_charging(self) -> bool:
        """Check if battery is below threshold"""
        return self.current_battery_percentage < self.battery_threshold
    
    def to_dict(self) -> Dict:
        """Convert agent to dictionary for JSON output"""
        return {
            'id': self.id,
            'position': self.current_position,
            'battery_percentage': round(self.current_battery_percentage, 2),
            'state': self.current_state.value,
            'target': self.current_target,
            'shop': self.shop,
            'restaurant': self.restaurant,
            'shop_start_time': self.shop_start_time,
            'shop_end_time': self.shop_end_time,
            'restaurant_start_time': self.restaurant_start_time,
            'restaurant_end_time': self.restaurant_end_time,
            'Day': self.Day,
            'distance_traveled': round(self.total_distance_traveled, 2),
            'speed': self.speed
        }

# ===== CHARGING STATION CLASS =====
class ChargingStation:
    def __init__(self, station_id: int, location: int, coordinates: Tuple[float, float],
                 total_ports: int, charging_rate: float):
        self.id = station_id
        self.location = location  # node_id on road network
        self.coordinates = coordinates  # (lat, lon)
        self.total_ports = total_ports
        self.available_ports = total_ports
        self.charging_agents = []
        self.waiting_queue = []
        self.max_queue_size = 10
        self.charging_rate = charging_rate  # kWh per minute
    
    def can_accept_agent(self) -> bool:
        """Check if station can accept more agents"""
        return len(self.waiting_queue) < self.max_queue_size
    
    def add_to_queue(self, agent_id: int):
        """Add agent to waiting queue"""
        if self.can_accept_agent() and agent_id not in self.waiting_queue:
            self.waiting_queue.append(agent_id)
    
    def update_charging(self, agents: List[Agent], time_step: int):
        """Update charging for all connected agents"""
        for agent_id in self.charging_agents:
            agent = next((a for a in agents if a.id == agent_id), None)
            if agent:
                energy_added = self.charging_rate * time_step
                battery_added = (energy_added / agent.battery_capacity) * 100
                agent.current_battery_percentage = min(100, 
                                                       agent.current_battery_percentage + battery_added)
    
    def to_dict(self) -> Dict:
        """Convert station to dictionary for JSON output"""
        return {
            'id': self.id,
            'location': self.location,
            'coordinates': self.coordinates,
            'available_ports': self.available_ports,
            'charging_count': len(self.charging_agents),
            'waiting_count': len(self.waiting_queue),
            'charging_agents': self.charging_agents[:],
            'waiting_agents': self.waiting_queue[:]
        }

# ===== MAIN SIMULATION CLASS =====
class EVSimulation:
    def __init__(self, roads_file: str, charging_stations_file: str, num_agents: int = 3, num_days: int = 2, allocation_method: str = "nearest"):
        self.road_network = RoadNetwork()
        self.agents = []
        self.charging_stations = []
        self.num_agents = num_agents
        self.num_days = num_days
        # Time parameters (in minutes from midnight)
        self.BASE_OFFICE_START_TIME = 540  # 9:00 AM
        self.BASE_OFFICE_END_TIME = 1020  # 5:00 PM
        self.SIMULATION_START = 0
        # Run for num_days; SIMULATION_END is inclusive minute index
        self.SIMULATION_END = self.num_days * 24 * 60 - 1
        self.TIME_STEP = 1  # 1 minute
        # Allocation method: 'nearest', 'random', 'least_queue'
        self.allocation_method = allocation_method
        # Load data
        self.load_road_network(roads_file)
        self.load_charging_stations(charging_stations_file)
        self.initialize_agents()
    
    def load_road_network(self, filename: str):
        """Load road network from GeoJSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Extract nodes and edges from features
        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            
            # Get node IDs from properties
            u = props.get('u')
            v = props.get('v')
            
            if u is None or v is None:
                continue
            
            # Add nodes
            if len(coords) > 0:
                self.road_network.add_node(u, coords[0][1], coords[0][0])
            if len(coords) > 1:
                self.road_network.add_node(v, coords[-1][1], coords[-1][0])
            
            # Calculate distance if not provided
            distance = props.get('length', 0)
            if distance == 0 and len(coords) >= 2:
                distance = haversine_distance(coords[0][1], coords[0][0], 
                                             coords[-1][1], coords[-1][0]) * 1000  # m to km
            else:
                distance = distance / 1000  # Convert m to km
            
            speed_limit = props.get('speed_kph', 30)
            
            # Add edge
            self.road_network.add_edge(u, v, distance, speed_limit)
        
        print(f"Loaded {len(self.road_network.nodes)} nodes and {len(self.road_network.edge_properties)//2} edges")
    
    def load_charging_stations(self, filename: str):
        """Load charging stations from GeoJSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        for idx, feature in enumerate(data['features']):
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            
            # Find nearest node on road network
            nearest_node = find_nearest_node(coords[1], coords[0], self.road_network.nodes)
            
            # Get number of ports
            total_ports = props.get('ports', 4)
            
            # Calculate charging rate from max power (kW to kWh per minute)
            max_power_kw = props.get('max_power_kw', 50)
            charging_rate = max_power_kw / 60  # kWh per minute
            
            station = ChargingStation(
                station_id=idx,
                location=nearest_node,
                coordinates=(coords[1], coords[0]),
                total_ports=total_ports,
                charging_rate=charging_rate
            )
            
            self.charging_stations.append(station)
        
        print(f"Loaded {len(self.charging_stations)} charging stations")
    
    def initialize_agents(self):
        """Initialize agent array"""
        node_ids = list(self.road_network.nodes.keys())
        
        for i in range(self.num_agents):
            # Select random home and office locations
            home = random.choice(node_ids)
            office = random.choice([n for n in node_ids if n != home])
            
            # Random battery and consumption parameters
            battery_capacity = random.uniform(40, 75)  # kWh
            energy_consumption_rate = random.uniform(0.50, 0.65)  # kWh/km
            
            print("Office Location for agent", i, "is:", office)
            # Create agent and randomly assign shop, restaurant and schedule
            agent = Agent(i, home, office, battery_capacity, energy_consumption_rate)
            possible_nodes = [n for n in node_ids if n not in (home, office)]
            if possible_nodes:
                agent.shop = random.choice(possible_nodes)
                # ensure restaurant is different from shop if possible
                remaining = [n for n in possible_nodes if n != agent.shop]
                agent.restaurant = random.choice(remaining or possible_nodes)
            else:
                agent.shop = home
                agent.restaurant = office

            # shop and restaurant times (minute-of-day)
            # shop start between 10:00 and 15:00, duration 30-120 min
            shop_start = random.randint(600, 900)
            shop_duration = random.randint(30, 120)
            agent.shop_start_time = shop_start
            agent.shop_end_time = shop_start + shop_duration

            # restaurant start between 12:00 and 21:00, duration 30-120 min
            rest_start = random.randint(720, 1260)
            rest_duration = random.randint(30, 120)
            agent.restaurant_start_time = rest_start
            agent.restaurant_end_time = rest_start + rest_duration

            # Day of week the agent visits shop/restaurant (0=Monday .. 6=Sunday)
            agent.Day = random.randint(0, 6)

            print(f"Agent {i}: shop={agent.shop}, restaurant={agent.restaurant}, Day={agent.Day}, shop_time={agent.shop_start_time}-{agent.shop_end_time}, rest_time={agent.restaurant_start_time}-{agent.restaurant_end_time}")

            self.agents.append(agent)
        
        print(f"Initialized {len(self.agents)} agents")
    
    def find_nearest_charging_station(self, current_position: int) -> Optional[ChargingStation]:
        """Find nearest charging station that can accept the agent (nearest method)"""
        min_distance = float('inf')
        nearest_station = None
        for station in self.charging_stations:
            if station.can_accept_agent():
                path, distance = self.road_network.dijkstra(current_position, station.location)
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = station
        return nearest_station

    def find_random_charging_station(self, current_position: int) -> Optional[ChargingStation]:
        """Assign a random charging station that can accept the agent"""
        available_stations = [s for s in self.charging_stations if s.can_accept_agent()]
        if available_stations:
            return random.choice(available_stations)
        return None

    def find_least_queue_charging_station(self, current_position: int) -> Optional[ChargingStation]:
        """Find charging station with the least queue length that can accept the agent"""
        min_queue = float('inf')
        best_station = None
        for station in self.charging_stations:
            if station.can_accept_agent():
                queue_length = len(station.waiting_queue)
                if queue_length < min_queue:
                    min_queue = queue_length
                    best_station = station
        return best_station
    
    def should_start_journey_to_next_location(self, agent: Agent, minute_of_day: int, day_of_week: int) -> Tuple[bool, Optional[int], Optional[AgentState]]:
        """
        Determine if agent should start a journey based on schedule.
        Returns: (should_move, target_location, new_state)
        """
        # Check if it's the agent's special day
        is_special_day = (agent.Day is not None and day_of_week == agent.Day)
        
        office_start_min = (self.BASE_OFFICE_START_TIME + agent.morning_offset) % 1440
        office_end_min = (self.BASE_OFFICE_END_TIME + agent.evening_offset) % 1440
        
        # Priority 1: Shop start time on special day (from home)
        if is_special_day and minute_of_day >= agent.shop_start_time and agent.current_state == AgentState.AT_HOME and minute_of_day <= agent.shop_end_time:
            return True, agent.shop, AgentState.MOVING_TO_SHOP
        
        # Priority 2: Shop end time on special day (from shop to restaurant)
        if is_special_day and minute_of_day == agent.shop_end_time and agent.current_state == AgentState.AT_SHOP:
            return True, agent.restaurant, AgentState.MOVING_TO_RESTAURANT
        
        # Priority 3: Restaurant end time on special day (from restaurant to home)
        if is_special_day and minute_of_day == agent.restaurant_end_time and agent.current_state == AgentState.AT_RESTAURANT:
            return True, agent.home_location, AgentState.MOVING_TO_HOME
        
        # FALLBACK: Handle agents stuck at locations past their scheduled departure time
        # Check if agent at shop but past shop end time
        if is_special_day and agent.current_state == AgentState.AT_SHOP and minute_of_day > agent.shop_end_time:
            return True, agent.restaurant, AgentState.MOVING_TO_RESTAURANT
        
        # Check if agent at restaurant but past restaurant end time
        if is_special_day and agent.current_state == AgentState.AT_RESTAURANT and minute_of_day > agent.restaurant_end_time:
            return True, agent.home_location, AgentState.MOVING_TO_HOME
        
        # Priority 4: Morning office start (but not on special day)
        if minute_of_day >= office_start_min and agent.current_state == AgentState.AT_HOME and not is_special_day:
            return True, agent.office_location, AgentState.MOVING_TO_OFFICE
        
        # Priority 5: Evening office end
        if minute_of_day >= office_end_min and agent.current_state == AgentState.AT_OFFICE:
            return True, agent.home_location, AgentState.MOVING_TO_HOME
        
        return False, None, None
    
    def run(self) -> List[Dict]:
        """Run the simulation"""
        current_time = self.SIMULATION_START
        simulation_data = []
        print(f"Starting simulation from {self.SIMULATION_START} to {self.SIMULATION_END} with allocation method '{self.allocation_method}'...")
        
        while current_time <= self.SIMULATION_END:
            if current_time % 60 == 0:
                print(f"Time: {current_time//60:02d}:00")
            
            timestep_data = {
                'time': current_time,
                'time_formatted': f"{current_time//60:02d}:{current_time%60:02d}",
                'agents': [],
                'charging_stations': []
            }
            
            day_of_week = (current_time // 1440) % 7
            minute_of_day = current_time % 1440
            
            for agent in self.agents:
                # ===== PHASE 1: CHECK FOR SCHEDULED DEPARTURES =====
                should_move, target, new_state = self.should_start_journey_to_next_location(agent, minute_of_day, day_of_week)
                
                if should_move:
                    agent.current_state = new_state
                    agent.current_target = target
                    agent.current_path, _ = self.road_network.dijkstra(agent.current_position, agent.current_target)
                    agent.path_index = 0
                
                # ===== PHASE 2: CHECK FOR LOW BATTERY (only when moving) =====
                if agent.current_state in [AgentState.MOVING_TO_OFFICE, AgentState.MOVING_TO_HOME,
                                          AgentState.MOVING_TO_CHARGING, AgentState.MOVING_TO_SHOP,
                                          AgentState.MOVING_TO_RESTAURANT]:
                    
                    if agent.needs_charging() and agent.current_state != AgentState.MOVING_TO_CHARGING:
                        # Save current destination
                        agent.previous_target = agent.current_target
                        
                        # Select charging station based on allocation method
                        if self.allocation_method == "nearest":
                            station = self.find_nearest_charging_station(agent.current_position)
                        elif self.allocation_method == "random":
                            station = self.find_random_charging_station(agent.current_position)
                        elif self.allocation_method == "least_queue":
                            station = self.find_least_queue_charging_station(agent.current_position)
                        else:
                            station = self.find_nearest_charging_station(agent.current_position)
                        
                        if station:
                            path, distance_to_station = self.road_network.dijkstra(agent.current_position, station.location)
                            energy_needed = distance_to_station * agent.energy_consumption_rate
                            energy_available = (agent.current_battery_percentage / 100) * agent.battery_capacity
                            
                            if energy_available >= energy_needed:
                                agent.current_state = AgentState.MOVING_TO_CHARGING
                                agent.current_target = station.location
                                agent.current_path = path
                                agent.path_index = 0
                            else:
                                agent.current_state = AgentState.STRANDED
                                agent.speed = 0
                                print(f"Agent {agent.id} stranded at node {agent.current_position}")
                
                # ===== PHASE 3: MOVEMENT =====
                if agent.current_state in [AgentState.MOVING_TO_OFFICE, AgentState.MOVING_TO_HOME,
                                          AgentState.MOVING_TO_CHARGING, AgentState.MOVING_TO_SHOP,
                                          AgentState.MOVING_TO_RESTAURANT]:
                    
                    if len(agent.current_path) > 0 and agent.path_index < len(agent.current_path) - 1:
                        # Move along path
                        current_node = agent.current_path[agent.path_index]
                        next_node = agent.current_path[agent.path_index + 1]
                        
                        edge_props = self.road_network.get_edge_properties(current_node, next_node)
                        agent.speed = edge_props['speed_limit']
                        
                        distance_per_timestep = (agent.speed / 60) * self.TIME_STEP
                        agent.update_battery(distance_per_timestep)
                        agent.total_distance_traveled += distance_per_timestep
                        
                        agent.current_position = next_node
                        agent.path_index += 1
                    
                    else:
                        # Reached destination - update state based on target
                        agent.speed = 0
                        
                        if agent.current_target == agent.office_location:
                            agent.current_state = AgentState.AT_OFFICE
                        elif agent.current_target == agent.home_location:
                            agent.current_state = AgentState.AT_HOME
                        elif agent.current_target == agent.shop:
                            agent.current_state = AgentState.AT_SHOP
                        elif agent.current_target == agent.restaurant:
                            agent.current_state = AgentState.AT_RESTAURANT
                        else:
                            # Arrived at charging station
                            station = next((s for s in self.charging_stations if s.location == agent.current_target), None)
                            if station and station.can_accept_agent():
                                station.add_to_queue(agent.id)
                                agent.current_state = AgentState.WAITING_TO_CHARGE
                
                # Add agent data to timestep
                timestep_data['agents'].append(agent.to_dict())
            
            # ===== PHASE 4: CHARGING STATION UPDATES =====
            for station in self.charging_stations:
                # Remove fully charged agents
                for agent_id in station.charging_agents[:]:
                    agent = next((a for a in self.agents if a.id == agent_id), None)
                    if agent and agent.current_battery_percentage >= 80:
                        station.charging_agents.remove(agent_id)
                        station.available_ports += 1
                        
                        # Resume journey to previous target
                        if agent.previous_target:
                            agent.current_target = agent.previous_target
                            agent.previous_target = None
                            agent.current_path, _ = self.road_network.dijkstra(agent.current_position, agent.current_target)
                            agent.path_index = 0
                            
                            # Determine new state based on target
                            if agent.current_target == agent.office_location:
                                agent.current_state = AgentState.MOVING_TO_OFFICE
                            elif agent.current_target == agent.home_location:
                                agent.current_state = AgentState.MOVING_TO_HOME
                            elif agent.current_target == agent.shop:
                                agent.current_state = AgentState.MOVING_TO_SHOP
                            elif agent.current_target == agent.restaurant:
                                agent.current_state = AgentState.MOVING_TO_RESTAURANT
                        else:
                            agent.current_state = AgentState.AT_CHARGING_STATION
                
                # Update charging for connected agents
                station.update_charging(self.agents, self.TIME_STEP)
                
                # Admit waiting agents to available ports
                while station.available_ports > 0 and len(station.waiting_queue) > 0:
                    agent_id = station.waiting_queue.pop(0)
                    agent = next((a for a in self.agents if a.id == agent_id), None)
                    if agent:
                        station.charging_agents.append(agent_id)
                        station.available_ports -= 1
                        agent.current_state = AgentState.CHARGING
                        agent.charging_start_time = current_time
                
                timestep_data['charging_stations'].append(station.to_dict())
            
            simulation_data.append(timestep_data)
            current_time += self.TIME_STEP
        
        print("Simulation complete!")
        return simulation_data
    
    def save_results(self, simulation_data: List[Dict], filename: str = 'simulation_output.json'):
        """Save simulation results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(simulation_data, f, indent=2)
        print(f"Results saved to {filename}")

# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    # Run the simulation three times with different allocation methods
    methods = ["nearest", "random", "least_queue"]
    for method in methods:
        print(f"\n=== Running simulation with '{method}' allocation method ===")
        sim = EVSimulation(
            roads_file='data/roads.geojson',
            charging_stations_file='data/charging_points.geojson',
            num_agents=5,
            num_days=7,
            allocation_method=method
        )
        results = sim.run()
        sim.save_results(results, filename=f'simulation_output_{method}.json')
        
        # Print summary statistics
        print("\n=== SIMULATION SUMMARY ===")
        final_timestep = results[-1]
        print(f"\nAgent Status at End:")
        for agent_data in final_timestep['agents']:
            print(f"Agent {agent_data['id']}: {agent_data['state']} "
                  f"(Battery: {agent_data['battery_percentage']}%, "
                  f"Distance: {agent_data['distance_traveled']} km)")
        
        print(f"\nCharging Station Status:")
        for station_data in final_timestep['charging_stations']:
            print(f"Station {station_data['id']}: "
                  f"{station_data['charging_count']} charging, "
                  f"{station_data['waiting_count']} waiting")
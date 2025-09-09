# main.py - Main entry point for the EV charging simulation.

# --- Imports ---
import networkx as nx
import random
import json
import time

# --- Configuration & Global Variables ---
CONFIG = {
    "simulation_duration_minutes": 1440,  # 24 hours
    "time_step_minutes": 5,
    "num_agents": 1000,
    "charging_threshold_soc": 0.20,  # Agents seek charge below 20%
    "simulation_mode": "greedy"  # Can be "greedy" or "optimized"
}

# Global objects to hold our data and simulation state
network_graph = None
agents = []
charging_stations = []
simulation_time = 0

# --- Helper Classes ---

class Agent:
    """Represents a single EV commuter."""
    def __init__(self, agent_id, home_location, work_location, battery_capacity):
        self.id = agent_id
        self.home = home_location
        self.work = work_location
        self.current_location = home_location
        self.battery_capacity = battery_capacity
        self.current_soc = 1.0  # State of Charge, starts full
        self.is_enroute = False
        self.destination = None
        self.path = []
        self.charging_time_remaining = 0
        self.failed_attempts = 0
        self.charging_overhead_distance = 0
        self.charging_overhead_time = 0

    def decide_action(self):
        """
        Determines the agent's next action based on its state (e.g., commute, charge).
        This is where the core behavioral logic resides.
        """
        pass

    def travel(self):
        """
        Simulates the agent moving along its path for one time step.
        Updates location and battery SOC based on distance traveled.
        """
        pass

    def find_charging_station(self, mode):
        """
        Finds a suitable charging station based on the simulation mode.
        Mode "greedy" finds the nearest available.
        Mode "optimized" calls the central allocation function.
        """
        pass

class ChargingStation:
    """Represents a single charging station with multiple ports."""
    def __init__(self, station_id, location, num_ports, charging_speed_kw):
        self.id = station_id
        self.location = location
        self.num_ports = num_ports
        self.charging_speed = charging_speed_kw
        self.occupied_ports = 0
        self.queue = []
        self.utilization_log = []

    def handle_arrival(self, agent):
        """
        Manages an agent's arrival, either assigning a port or adding to the queue.
        """
        pass

    def update(self):
        """
        Updates the charging process for all agents at the station.
        Moves agents from queue to a free port if available.
        """
        pass

# --- Data Loading & Setup ---

def load_data():
    """
    Loads all necessary data from external files (e.g., CSV, JSON).
    This function will be expanded to read:
    - Road network data for graph creation
    - Charging station locations
    - Building locations for agent generation
    """
    print("Loading data...")
    # TODO: Implement data loading
    # e.g., buildings_data = load_buildings_from_geojson()
    # e.g., stations_data = load_stations_from_csv()
    # e.g., network_graph_data = load_road_network_from_osm()
    print("Data loaded successfully.")

def initialize_simulation():
    """
    Initializes the simulation environment before the main loop begins.
    - Creates the road network graph.
    - Generates and places agents.
    - Initializes charging stations.
    """
    global network_graph, agents, charging_stations

    print("Initializing simulation...")
    # TODO: Implement graph creation from road data
    network_graph = nx.Graph()
    # TODO: Implement agent and station creation
    for i in range(CONFIG["num_agents"]):
        # Example agent generation
        home = (random.randint(0, 100), random.randint(0, 100))
        work = (random.randint(0, 100), random.randint(0, 100))
        agents.append(Agent(i, home, work, 60))
    print("Simulation initialized.")

def central_allocation_function(agent):
    """
    (Part 2) A more sophisticated function for charging station allocation.
    This function will be called by agents in "optimized" mode.
    It considers multiple factors (queue, distance, etc.) to recommend a station.
    """
    print(f"Agent {agent.id} requesting optimized allocation...")
    # TODO: Implement the allocation logic
    # Find best_station based on a defined algorithm
    best_station = None
    return best_station

# --- Simulation Loop ---

def run_simulation():
    """
    Main simulation loop. Advances the simulation by one time step.
    - Updates agents' states (travel, charge).
    - Updates charging stations' states (queue, charging).
    - Collects performance metrics.
    """
    global simulation_time

    print("Starting simulation...")
    while simulation_time < CONFIG["simulation_duration_minutes"]:
        # Update Agents
        for agent in agents:
            agent.decide_action()
            if agent.is_enroute:
                agent.travel()

        # Update Charging Stations
        for station in charging_stations:
            station.update()

        # Log metrics for this time step
        log_metrics()

        # Advance time
        simulation_time += CONFIG["time_step_minutes"]

        # Print progress
        if simulation_time % 60 == 0:
            print(f"Simulation time: {simulation_time} minutes")

    print("Simulation finished.")

# --- Analysis & Visualization ---

def log_metrics():
    """
    Captures key metrics at the end of each time step.
    - Queue lengths at each station
    - Number of charging attempts
    - Agent overheads
    """
    # TODO: Implement metric logging
    pass

def generate_report():
    """
    Generates the final report and visualizations based on the collected metrics.
    - Bottlenecks (congested stations)
    - Charging overhead (distance and time)
    - Utilization (over- and under-utilized stations)
    - Failed charging attempts
    - (Part 2) Comparison of "greedy" vs. "optimized" modes
    """
    print("Generating final report...")
    # TODO: Implement analysis and visualization logic (e.g., using matplotlib, seaborn)
    pass

# --- Main Execution ---

if __name__ == "__main__":
    # Load all data required for the simulation
    load_data()

    # Initialize the simulation environment
    initialize_simulation()

    # Run the simulation
    run_simulation()

    # Generate the final report and visualizations
    generate_report()

import random
import math
import time

# --- Configuration ---
# Coordinates for the Kondapur-Hitech City-Gachibowli corridor
AREA_BOUNDS = {
    "min_lat": 17.43, "max_lat": 17.46,
    "min_lon": 78.33, "max_lon": 78.38
}

# Simulation parameters
NUM_EV_AGENTS = 50
NUM_CHARGING_STATIONS = 5
SIMULATION_HOURS = 24
TIME_STEP_MINUTES = 15 # Each step in the simulation represents 15 minutes

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

# --- Model Classes ---

class ChargingStation:
    """Represents a public EV charging station."""
    def __init__(self, station_id, location):
        self.id = station_id
        self.location = location
        self.capacity = random.randint(2, 6) # Number of charging ports
        self.available_ports = self.capacity
        self.queue = []
        self.utilization_log = []

    def is_available(self):
        """Check if a charging port is free."""
        return self.available_ports > 0

    def occupy_port(self, agent_id):
        """Occupy a port for charging."""
        if self.is_available():
            self.available_ports -= 1
            print(f"Station {self.id}: Port occupied by Agent {agent_id}. Available ports: {self.available_ports}/{self.capacity}")
            return True
        return False

    def release_port(self):
        """Release a port after charging."""
        if self.available_ports < self.capacity:
            self.available_ports += 1
        # Serve the next agent in the queue if any
        if self.queue and self.is_available():
            next_agent_id = self.queue.pop(0)
            # This logic would be handled by the simulation loop,
            # informing the agent it can now charge.
            print(f"Station {self.id}: Port released. Notifying Agent {next_agent_id} from queue.")

    def add_to_queue(self, agent_id):
        """Add an agent to the waiting queue."""
        self.queue.append(agent_id)
        print(f"Station {self.id}: All ports busy. Agent {agent_id} added to queue (Queue size: {len(self.queue)}).")
        
    def log_utilization(self):
        """Log the current utilization for reporting."""
        used_ports = self.capacity - self.available_ports
        self.utilization_log.append(used_ports)

class EV_Agent:
    """Represents an EV commuter."""
    def __init__(self, agent_id):
        self.id = agent_id
        self.home_location = get_random_location()
        self.work_location = get_random_location()
        
        # Vehicle properties
        self.battery_capacity_kwh = random.uniform(30, 60) # e.g., Tata Nexon vs MG ZS EV
        self.soc = random.uniform(0.5, 1.0) # Start with 50-100% charge
        self.consumption_kwh_per_km = random.uniform(0.12, 0.18)
        
        # Behavior
        self.charging_threshold = random.uniform(0.2, 0.4) # Charge when SOC drops below 20-40%
        self.target_soc = 0.9 # Charge up to 90%
        
        # State machine
        self.status = "at_home" # at_home, commuting_to_work, at_work, commuting_to_home, seeking_charge, charging
        self.location = self.home_location
        self.charge_duration_steps = 0

    def get_soc_percentage(self):
        return round(self.soc * 100)

    def drive(self, distance_km):
        """Simulate driving and consuming battery."""
        if distance_km <= 0: return
        
        energy_needed = distance_km * self.consumption_kwh_per_km
        soc_consumed = energy_needed / self.battery_capacity_kwh
        self.soc = max(0, self.soc - soc_consumed)
        print(f"Agent {self.id}: Drove {distance_km:.1f} km. SOC is now {self.get_soc_percentage()}%.")

    def charge(self, charge_rate_kw, time_step_minutes):
        """Simulate charging the battery."""
        if self.soc < self.target_soc:
            energy_added = charge_rate_kw * (time_step_minutes / 60.0)
            soc_added = energy_added / self.battery_capacity_kwh
            self.soc = min(1.0, self.soc + soc_added)
            return False # Still charging
        else:
            print(f"Agent {self.id}: Charging complete. SOC is {self.get_soc_percentage()}%.")
            return True # Charging finished

    def decide_action(self, hour, charging_stations):
        """The core logic for agent behavior based on the time of day."""
        # Morning commute
        if 8 <= hour < 9 and self.status == "at_home":
            self.status = "commuting_to_work"
            distance = haversine_distance(self.home_location['lat'], self.home_location['lon'],
                                          self.work_location['lat'], self.work_location['lon'])
            self.drive(distance)
            self.location = self.work_location
            self.status = "at_work"

        # Evening commute
        elif 17 <= hour < 18 and self.status == "at_work":
            self.status = "commuting_to_home"
            distance = haversine_distance(self.work_location['lat'], self.work_location['lon'],
                                          self.home_location['lat'], self.home_location['lon'])
            self.drive(distance)
            self.location = self.home_location
            self.status = "at_home"

        # Decide to charge (typically after arriving home or work)
        if self.soc < self.charging_threshold and self.status in ["at_home", "at_work"]:
            self.status = "seeking_charge"
            print(f"Agent {self.id}: SOC at {self.get_soc_percentage()}% is below threshold ({self.charging_threshold*100:.0f}%). Seeking a charging station.")

class Simulation:
    """Manages the simulation environment, agents, and time."""
    def __init__(self, num_agents, num_stations):
        self.charging_stations = [ChargingStation(i, get_random_location()) for i in range(num_stations)]
        self.agents = [EV_Agent(i) for i in range(num_agents)]
        self.current_time_step = 0
        self.total_steps = SIMULATION_HOURS * (60 // TIME_STEP_MINUTES)
        
        # Metrics
        self.total_wait_time = 0
        self.successful_charges = 0
        self.failed_charges = 0

    def find_nearest_station(self, agent_location):
        """Find the closest charging station to a given location."""
        stations_by_distance = sorted(
            self.charging_stations,
            key=lambda s: haversine_distance(agent_location['lat'], agent_location['lon'], s.location['lat'], s.location['lon'])
        )
        return stations_by_distance

    def run_step(self):
        """Run one time step of the simulation."""
        current_hour = (self.current_time_step * TIME_STEP_MINUTES) // 60
        print(f"\n--- Time: Day {(current_hour // 24) + 1}, {current_hour % 24:02d}:{(self.current_time_step * TIME_STEP_MINUTES) % 60:02d} ---")

        for agent in self.agents:
            # Agent makes a decision based on the hour
            if agent.status not in ["charging", "seeking_charge"]:
                agent.decide_action(current_hour, self.charging_stations)

            # Handle agents seeking a charge
            if agent.status == "seeking_charge":
                available_stations = self.find_nearest_station(agent.location)
                has_started_charging = False
                for station in available_stations:
                    if station.occupy_port(agent.id):
                        agent.status = "charging"
                        agent.charging_station_id = station.id
                        self.successful_charges +=1
                        has_started_charging = True
                        break # Found a station
                
                if not has_started_charging:
                    # No available station, add to the queue of the nearest one
                    nearest_station = available_stations[0]
                    nearest_station.add_to_queue(agent.id)
                    self.total_wait_time += TIME_STEP_MINUTES
                    # For this prototype, the agent just waits. A more complex model
                    # could have them try another station after some time.

            # Handle agents that are currently charging
            elif agent.status == "charging":
                station = self.charging_stations[agent.charging_station_id]
                # Assuming a standard 22kW AC charger for simulation
                is_done = agent.charge(charge_rate_kw=22, time_step_minutes=TIME_STEP_MINUTES)
                if is_done:
                    agent.status = "at_home" if current_hour > 18 or current_hour < 8 else "at_work"
                    station.release_port()

        # Log station utilization at the end of the step
        for station in self.charging_stations:
            station.log_utilization()

        self.current_time_step += 1

    def run_simulation(self):
        """Run the full simulation from start to finish."""
        print("Starting EV Charging Simulation...")
        for _ in range(self.total_steps):
            self.run_step()
            # time.sleep(0.1) # Uncomment for a slower, step-by-step view
        self.print_report()

    def print_report(self):
        """Print a summary of the simulation results."""
        print("\n--- Simulation Report ---")
        print(f"Total Agents: {len(self.agents)}")
        print(f"Total Charging Stations: {len(self.charging_stations)}")
        print("-" * 25)
        print(f"Successful Charges Initiated: {self.successful_charges}")
        print(f"Total Wait Time (all agents): {self.total_wait_time} minutes")
        
        avg_wait = self.total_wait_time / self.successful_charges if self.successful_charges > 0 else 0
        print(f"Average Wait Time per Charge: {avg_wait:.2f} minutes")
        print("-" * 25)

        for station in self.charging_stations:
            if station.utilization_log:
                avg_utilization = sum(station.utilization_log) / len(station.utilization_log)
                max_utilization = max(station.utilization_log)
                print(f"Station {station.id}:")
                print(f"  - Capacity: {station.capacity} ports")
                print(f"  - Average Busy Ports: {avg_utilization:.2f} ({avg_utilization/station.capacity*100:.1f}%)")
                print(f"  - Peak Busy Ports: {max_utilization} ({max_utilization/station.capacity*100:.1f}%)")
                print(f"  - Agents left in queue: {len(station.queue)}")
                
# --- Main Execution ---
if __name__ == "__main__":
    simulation = Simulation(num_agents=NUM_EV_AGENTS, num_stations=NUM_CHARGING_STATIONS)
    simulation.run_simulation()

from chargingstations import ChargingStation
from evagents import EV_Agent
from functions import get_random_location, haversine_distance
from configurations import SIMULATION_HOURS, TIME_STEP_MINUTES

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
                
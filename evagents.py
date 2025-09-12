import random
from functions import get_random_location, haversine_distance

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
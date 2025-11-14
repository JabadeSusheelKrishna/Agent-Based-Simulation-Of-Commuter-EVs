import json
import matplotlib.pyplot as plt
import argparse
from collections import defaultdict

def load_simulation_data(filename):
    """Load simulation output JSON."""
    with open(filename, 'r') as f:
        return json.load(f)

def aggregate_battery_by_day(simulation_data):
    """
    Group battery percentage of each agent by day.
    Returns: {day: {agent_id: [(minute_of_day, battery_percent), ...]}}
    """
    minutes_per_day = 1440
    battery_data = defaultdict(lambda: defaultdict(list))

    for entry in simulation_data:
        time = entry["time"]
        day = time // minutes_per_day
        minute_of_day = time % minutes_per_day

        for agent in entry["agents"]:
            agent_id = agent["id"]
            battery = agent["battery_percentage"]
            battery_data[day][agent_id].append((minute_of_day, battery))

    return battery_data

def plot_battery_per_day(battery_data):
    """Plot charging percentage of different agents for each day."""
    for day, agents_data in battery_data.items():
        plt.figure(figsize=(12, 6))
        for agent_id, readings in agents_data.items():
            readings.sort(key=lambda x: x[0])
            times = [t for t, _ in readings]
            battery = [b for _, b in readings]
            plt.plot(times, battery, label=f"Agent {agent_id}")

        plt.title(f"Battery Percentage of Agents - Day {day}")
        plt.xlabel("Time of Day (minutes)")
        plt.ylabel("Battery Percentage (%)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="Visualize charging percentage of agents from simulation output JSON.")
    parser.add_argument("json_file", help="Path to simulation output JSON (e.g. simulation_output_nearest.json)")
    args = parser.parse_args()

    print(f"Loading {args.json_file}...")
    data = load_simulation_data(args.json_file)

    print("Aggregating battery data by day...")
    battery_data = aggregate_battery_by_day(data)

    print("Plotting battery percentage for each day...")
    plot_battery_per_day(battery_data)

if __name__ == "__main__":
    main()

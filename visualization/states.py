import json
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import argparse

def load_simulation_data(filename):
    """Load simulation JSON output."""
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def aggregate_states_by_day(simulation_data):
    """Aggregate average number of agents in each state per day."""
    minutes_per_day = 24 * 60
    num_agents = len(simulation_data[0]['agents'])
    state_counts = defaultdict(lambda: defaultdict(int))

    for entry in simulation_data:
        day = entry["time"] // minutes_per_day
        for agent in entry["agents"]:
            state_counts[day][agent["state"]] += 1

    # Normalize to get average number of agents in that state
    for day in state_counts:
        for state in state_counts[day]:
            state_counts[day][state] /= minutes_per_day

    return state_counts, num_agents

def aggregate_time_of_day(simulation_data):
    """Aggregate how many agents are in each state for each minute of the day (for heatmap & per-state plots)."""
    num_agents = len(simulation_data[0]['agents'])
    minutes_per_day = 1440
    state_names = sorted({agent["state"] for entry in simulation_data for agent in entry["agents"]})
    state_index = {state: i for i, state in enumerate(state_names)}

    # heatmap[state_index, minute_of_day] = average number of agents
    heatmap = np.zeros((len(state_names), minutes_per_day))

    for entry in simulation_data:
        minute = entry["time"] % minutes_per_day
        for agent in entry["agents"]:
            s = agent["state"]
            heatmap[state_index[s], minute] += 1

    # Average across days
    num_days = (simulation_data[-1]["time"] // minutes_per_day) + 1
    heatmap /= num_days

    return state_names, heatmap

def plot_state_counts(state_counts, num_agents):
    """Plot average number of agents in each state per day."""
    days = sorted(state_counts.keys())
    states = sorted({state for d in state_counts.values() for state in d.keys()})

    plt.figure(figsize=(12, 6))
    for state in states:
        values = [state_counts[d].get(state, 0) for d in days]
        plt.plot(days, values, marker='o', label=state)

    plt.title("Average Number of Agents in Each State per Day")
    plt.xlabel("Day")
    plt.ylabel("Average Number of Agents")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def plot_heatmap(state_names, heatmap):
    """Plot heatmap of average number of agents per state vs time of day."""
    plt.figure(figsize=(14, 6))
    plt.imshow(heatmap, aspect='auto', cmap='viridis', interpolation='nearest')
    plt.yticks(range(len(state_names)), state_names)
    plt.xticks(range(0, 1441, 120), [f"{h:02d}:00" for h in range(0, 25, 2)])
    plt.colorbar(label="Average Number of Agents")
    plt.title("Agent States by Time of Day (Averaged Over All Days)")
    plt.xlabel("Time of Day")
    plt.ylabel("Agent State")
    plt.tight_layout()
    plt.show()

def plot_state_time_series(state_names, heatmap):
    """Plot separate time-series for each state showing agent count through the day."""
    minutes = np.arange(1440)
    hours = minutes / 60.0

    for i, state in enumerate(state_names):
        plt.figure(figsize=(10, 4))
        plt.plot(hours, heatmap[i], label=state, linewidth=2)
        plt.title(f"Agents in State: {state}")
        plt.xlabel("Time of Day (hours)")
        plt.ylabel("Average Number of Agents")
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.legend()
        plt.tight_layout()
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="Visualize agent states from simulation output JSON.")
    parser.add_argument("json_file", help="Path to simulation output JSON (e.g. simulation_output_nearest.json)")
    args = parser.parse_args()

    print(f"Loading {args.json_file}...")
    data = load_simulation_data(args.json_file)

    print("Aggregating daily averages...")
    state_counts, num_agents = aggregate_states_by_day(data)
    plot_state_counts(state_counts, num_agents)

    print("Aggregating time-of-day patterns...")
    state_names, heatmap = aggregate_time_of_day(data)
    plot_heatmap(state_names, heatmap)

    print("Generating per-state time series plots...")
    plot_state_time_series(state_names, heatmap)

if __name__ == "__main__":
    main()

import json
import matplotlib.pyplot as plt
import networkx as nx
from ev_simulation import EVSimulation
import numpy as np

agents_count = 50

def visualize_network_and_stations():
    """Create a visualization of the road network and charging stations"""
    # Load the simulation
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    
    # Create agents to get home and office locations
    sim.create_agents(agents_count)
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # Plot 1: Road Network and Charging Stations
    pos = {}
    for node in sim.road_network.nodes():
        node_data = sim.road_network.nodes[node]
        pos[node] = (node_data['x'], node_data['y'])
    
    # Draw road network
    nx.draw_networkx_edges(sim.road_network, pos, ax=ax1, edge_color='gray', alpha=0.5, width=0.5)
    nx.draw_networkx_nodes(sim.road_network, pos, ax=ax1, node_color='lightblue', 
                          node_size=10, alpha=0.7)
    
    # Draw charging stations
    station_x = [station.location.lon for station in sim.charging_stations]
    station_y = [station.location.lat for station in sim.charging_stations]
    ax1.scatter(station_x, station_y, c='red', s=100, marker='s', 
               label=f'Charging Stations ({len(sim.charging_stations)})', zorder=5)
    
    # Draw home locations
    home_x = [agent.home.lon for agent in sim.agents]
    home_y = [agent.home.lat for agent in sim.agents]
    ax1.scatter(home_x, home_y, c='green', s=60, marker='o', 
               label=f'Home Locations ({len(set(zip(home_x, home_y)))})', zorder=4, alpha=0.8)
    
    # Draw office locations
    office_x = [agent.office.lon for agent in sim.agents]
    office_y = [agent.office.lat for agent in sim.agents]
    # Get unique office locations for better visualization
    unique_offices = list(set(zip(office_x, office_y)))
    office_unique_x = [loc[0] for loc in unique_offices]
    office_unique_y = [loc[1] for loc in unique_offices]
    ax1.scatter(office_unique_x, office_unique_y, c='blue', s=100, marker='^', 
               label=f'Office Locations ({len(unique_offices)})', zorder=4, alpha=0.8)
    
    ax1.set_title('Road Network with Agent Locations and Charging Stations')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Charging Station Capacity
    station_names = [station.name for station in sim.charging_stations]
    station_ports = [station.max_ports for station in sim.charging_stations]
    
    bars = ax2.bar(range(len(station_names)), station_ports, color='skyblue', alpha=0.7)
    ax2.set_title('Charging Station Capacity')
    ax2.set_xlabel('Charging Stations')
    ax2.set_ylabel('Number of Ports')
    ax2.set_xticks(range(len(station_names)))
    ax2.set_xticklabels([name.replace('charging_point_', 'CP') for name in station_names], 
                       rotation=45)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('network_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()

def run_and_visualize_simulation():
    """Run simulation and create time-series visualizations"""
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    sim.create_agents(agents_count)
    
    # Store simulation data
    time_data = []
    stats_data = []
    
    duration_hours = 48
    duration_minutes = duration_hours * 60
    
    print("Running simulation for visualization...")
    
    while sim.current_time < duration_minutes:
        sim.step()
        
        # Record data every hour
        if sim.current_time % 60 == 0:
            stats = sim.get_simulation_stats()
            time_data.append(sim.current_time / 60)  # Convert to hours
            stats_data.append(stats)
    
    # Create visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Extract data for plotting
    hours = time_data
    agents_home = [s['agents_at_home'] for s in stats_data]
    agents_office = [s['agents_at_office'] for s in stats_data]
    agents_commuting = [s['agents_commuting'] for s in stats_data]
    agents_charging = [s['agents_charging'] for s in stats_data]
    agents_waiting = [s['agents_waiting'] for s in stats_data]
    avg_battery = [s['avg_battery'] for s in stats_data]
    low_battery = [s['low_battery_agents'] for s in stats_data]
    occupied_ports = [s['occupied_ports'] for s in stats_data]
    total_ports = [s['total_charging_ports'] for s in stats_data]
    
    # Plot 1: Agent Locations
    ax1.plot(hours, agents_home, label='At Home', marker='o', linewidth=2)
    ax1.plot(hours, agents_office, label='At Office', marker='s', linewidth=2)
    ax1.plot(hours, agents_commuting, label='Commuting', marker='^', linewidth=2)
    ax1.plot(hours, agents_charging, label='Charging', marker='d', linewidth=2)
    ax1.plot(hours, agents_waiting, label='Waiting to Charge', marker='x', linewidth=2)
    
    ax1.set_title('Agent Distribution Over Time')
    ax1.set_xlabel('Time (Hours)')
    ax1.set_ylabel('Number of Agents')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, duration_hours)
    
    # Plot 2: Battery Levels
    ax2.plot(hours, avg_battery, label='Average Battery', color='green', linewidth=3)
    ax2.axhline(y=30, color='red', linestyle='--', label='Low Battery Threshold')
    ax2.fill_between(hours, 0, 30, alpha=0.2, color='red', label='Critical Zone')
    
    ax2.set_title('Average Battery Level Over Time')
    ax2.set_xlabel('Time (Hours)')
    ax2.set_ylabel('Battery Level (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, duration_hours)
    ax2.set_ylim(0, 100)
    
    # Plot 3: Low Battery Agents
    ax3.bar(hours, low_battery, alpha=0.7, color='orange', width=0.8)
    ax3.set_title('Agents with Low Battery (<30%)')
    ax3.set_xlabel('Time (Hours)')
    ax3.set_ylabel('Number of Agents')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, duration_hours)
    
    # Plot 4: Charging Infrastructure Utilization
    utilization = [occ/total * 100 if total > 0 else 0 for occ, total in zip(occupied_ports, total_ports)]
    ax4.plot(hours, occupied_ports, label='Occupied Ports', marker='o', linewidth=2)
    ax4.plot(hours, total_ports, label='Total Ports', linestyle='--', alpha=0.7)
    ax4_twin = ax4.twinx()
    ax4_twin.plot(hours, utilization, label='Utilization %', color='red', linewidth=2)
    
    ax4.set_title('Charging Infrastructure Usage')
    ax4.set_xlabel('Time (Hours)')
    ax4.set_ylabel('Number of Ports')
    ax4_twin.set_ylabel('Utilization (%)')
    ax4.legend(loc='upper left')
    ax4_twin.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, duration_hours)
    
    plt.tight_layout()
    plt.savefig('simulation_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print final statistics
    print("\n=== Final Simulation Summary ===")
    final_stats = stats_data[-1]
    print(f"Total agents: 20")
    print(f"Final average battery: {final_stats['avg_battery']:.1f}%")
    print(f"Agents with low battery: {final_stats['low_battery_agents']}")
    print(f"Peak charging port usage: {max(occupied_ports)}/{final_stats['total_charging_ports']}")
    print(f"Peak utilization: {max(utilization):.1f}%")

if __name__ == "__main__":
    print("Creating network visualization...")
    visualize_network_and_stations()
    
    print("\nRunning simulation with visualization...")
    run_and_visualize_simulation()

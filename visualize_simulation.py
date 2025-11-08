import json
import matplotlib.pyplot as plt
import networkx as nx
from ev_simulation import EVSimulation, CONFIG
import numpy as np
import os

# Load configuration
agents_count = CONFIG['agent']['count']
VIS_CONFIG = CONFIG['visualization']

def visualize_network_and_stations(use_locations_file: bool = True):
    """
    Create a visualization of the road network and charging stations
    
    Args:
        use_locations_file (bool): If True, load agent locations from Locations.json if it exists.
    """
    # Load the simulation
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    
    # Check for disconnected components
    components = list(nx.connected_components(sim.road_network))
    if len(components) > 1:
        print(f"Warning: Road network has {len(components)} disconnected components")
        print("Only the largest component will be used for visualization.")
        # Get the largest component
        largest_component = max(components, key=len)
        # Create a subgraph with only the largest component
        sim.road_network = sim.road_network.subgraph(largest_component).copy()
    
    # Create agents with optional locations file
    locations_file = 'Locations.json' if use_locations_file and os.path.exists('Locations.json') else None
    sim.create_agents(agents_count, locations_file=locations_file)
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIS_CONFIG['network_figsize'])
    
    # Plot 1: Road Network and Charging Stations
    pos = {}
    for node in sim.road_network.nodes():
        node_data = sim.road_network.nodes[node]
        pos[node] = (node_data['x'], node_data['y'])
    
    # Draw road network
    nx.draw_networkx_edges(
        sim.road_network, pos, ax=ax1, 
        edge_color=VIS_CONFIG['edge_color'], 
        alpha=VIS_CONFIG['edge_alpha'], 
        width=VIS_CONFIG['edge_width']
    )
    nx.draw_networkx_nodes(
        sim.road_network, pos, ax=ax1, 
        node_color=VIS_CONFIG['node_color'],
        node_size=VIS_CONFIG['node_size'], 
        alpha=VIS_CONFIG['node_alpha']
    )
    
    # Draw charging stations
    station_x = [station.location.lon for station in sim.charging_stations]
    station_y = [station.location.lat for station in sim.charging_stations]
    ax1.scatter(
        station_x, station_y, 
        c=VIS_CONFIG['station_color'], 
        s=VIS_CONFIG['station_size'], 
        marker=VIS_CONFIG['station_marker'],
        label=f'Charging Stations ({len(sim.charging_stations)})', 
        zorder=5
    )
    
    # Draw home locations
    home_x = [agent.home.lon for agent in sim.agents]
    home_y = [agent.home.lat for agent in sim.agents]
    ax1.scatter(
        home_x, home_y, 
        c=VIS_CONFIG['home_color'], 
        s=VIS_CONFIG['home_size'], 
        marker='o',
        label=f'Home Locations ({len(set(zip(home_x, home_y)))})', 
        zorder=4, 
        alpha=VIS_CONFIG['home_alpha']
    )
    
    # Draw office locations
    office_x = [agent.office.lon for agent in sim.agents]
    office_y = [agent.office.lat for agent in sim.agents]
    # Get unique office locations for better visualization
    unique_offices = list(set(zip(office_x, office_y)))
    office_unique_x = [loc[0] for loc in unique_offices]
    office_unique_y = [loc[1] for loc in unique_offices]
    ax1.scatter(
        office_unique_x, office_unique_y, 
        c=VIS_CONFIG['office_color'], 
        s=VIS_CONFIG['office_size'], 
        marker='^',
        label=f'Office Locations ({len(unique_offices)})', 
        zorder=4, 
        alpha=VIS_CONFIG['office_alpha']
    )
    
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
    # Save and show the figure
    plt.savefig(CONFIG['paths']['network_visualization'], dpi=300, bbox_inches='tight')
    plt.show()

def run_simulation_with_algorithm(algorithm_name, output_suffix=''):
    """Run simulation with a specific allocation algorithm"""
    # Set the allocation algorithm in config
    original_algorithm = CONFIG['allocation']['algorithm']
    CONFIG['allocation']['algorithm'] = algorithm_name
    
    # Create a copy of the simulation to avoid interference
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    sim.create_agents(agents_count)
    
    # Store simulation data
    time_data = []
    stats_data = []
    
    duration_hours = CONFIG['paths']['plots']['timeDuration']
    duration_minutes = duration_hours * 60
    
    print(f"\nRunning simulation with {algorithm_name} allocation algorithm...")
    
    while sim.current_time < duration_minutes:
        sim.step()
        
        # Record data every hour
        if sim.current_time % 60 == 0:
            stats = sim.get_simulation_stats()
            time_data.append(sim.current_time / 60)  # Convert to hours
            stats_data.append(stats)
    
    # Generate output paths with algorithm suffix
    output_paths = {}
    for plot_name, path in CONFIG['paths']['plots'].items():
        if plot_name != 'timeDuration':  # Skip timeDuration as it's not a file path
            base, ext = os.path.splitext(path)
            output_paths[plot_name] = f"{base}_{algorithm_name}{ext}"
    
    # Create visualizations
    create_visualizations(time_data, stats_data, output_paths, duration_hours)
    
    # Restore original algorithm
    CONFIG['allocation']['algorithm'] = original_algorithm
    
    return sim

def create_visualizations(time_data, stats_data, output_paths, duration_hours):
    """Create visualization plots from simulation data"""
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
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_paths['agent_distribution']) or '.', exist_ok=True)
    
    # Plot 1: Agent Locations
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(hours, agents_home, label='At Home', marker='o', linewidth=2, markersize=4)
    ax1.plot(hours, agents_office, label='At Office', marker='s', linewidth=2, markersize=4)
    ax1.plot(hours, agents_commuting, label='Commuting', marker='^', linewidth=2, markersize=4)
    ax1.plot(hours, agents_charging, label='Charging', marker='d', linewidth=2, markersize=4)
    ax1.plot(hours, agents_waiting, label='Waiting to Charge', marker='x', linewidth=2, markersize=4)
    
    ax1.set_title(f'Agent Distribution Over Time ({CONFIG["allocation"]["algorithm"]})', fontsize=12, pad=15)
    ax1.set_xlabel('Time (Hours)', fontsize=10)
    ax1.set_ylabel('Number of Agents', fontsize=10)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, duration_hours)
    plt.tight_layout()
    plt.savefig(output_paths['agent_distribution'], dpi=300, bbox_inches='tight')
    plt.close(fig1)
    
    # Plot 2: Battery Levels
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(hours, avg_battery, label='Average Battery', color='green', linewidth=3)
    ax2.axhline(y=30, color='red', linestyle='--', label='Low Battery Threshold')
    ax2.fill_between(hours, 0, 30, alpha=0.2, color='red', label='Critical Zone')
    
    ax2.set_title(f'Average Battery Level Over Time ({CONFIG["allocation"]["algorithm"]})', fontsize=12, pad=15)
    ax2.set_xlabel('Time (Hours)', fontsize=10)
    ax2.set_ylabel('Battery Level (%)', fontsize=10)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, duration_hours)
    ax2.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(output_paths['battery_levels'], dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # Plot 3: Low Battery Agents
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    ax3.bar(hours, low_battery, alpha=0.7, color='orange', width=0.8)
    ax3.set_title(f'Agents with Low Battery (<30%) ({CONFIG["allocation"]["algorithm"]})', fontsize=12, pad=15)
    ax3.set_xlabel('Time (Hours)', fontsize=10)
    ax3.set_ylabel('Number of Agents', fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_xlim(0, duration_hours)
    plt.tight_layout()
    plt.savefig(output_paths['low_battery_agents'], dpi=300, bbox_inches='tight')
    plt.close(fig3)
    
    # Plot 4: Charging Infrastructure Utilization
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    utilization = [occ/total * 100 if total > 0 else 0 for occ, total in zip(occupied_ports, total_ports)]
    
    # Plot primary y-axis (left)
    color = 'tab:blue'
    ax4.set_xlabel('Time (Hours)', fontsize=10)
    ax4.set_ylabel('Number of Ports', color=color, fontsize=10)
    ax4.plot(hours, occupied_ports, label='Occupied Ports', marker='o', linewidth=2, color=color, markersize=4)
    ax4.plot(hours, total_ports, label='Total Ports', linestyle='--', alpha=0.7, color=color)
    ax4.tick_params(axis='y', labelcolor=color)
    
    # Create secondary y-axis (right)
    ax4_twin = ax4.twinx()
    color = 'tab:red'
    ax4_twin.set_ylabel('Utilization (%)', color=color, fontsize=10)
    ax4_twin.plot(hours, utilization, label='Utilization %', color=color, linewidth=2, linestyle='-', alpha=0.7)
    ax4_twin.tick_params(axis='y', labelcolor=color)
    
    # Set title and grid
    ax4.set_title(f'Charging Infrastructure Usage ({CONFIG["allocation"]["algorithm"]})', fontsize=12, pad=15)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, duration_hours)
    
    # Combine legends from both axes
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, bbox_to_anchor=(1.1, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_paths['charging_infrastructure'], dpi=300, bbox_inches='tight')
    plt.close(fig4)
    
    # Print summary statistics
    print(f"\n=== {CONFIG['allocation']['algorithm']} Algorithm Summary ===")
    print(f"Peak agents charging: {max(agents_charging)}")
    print(f"Max agents waiting: {max(agents_waiting)}")
    print(f"Peak low battery agents: {max(low_battery)}")
    print(f"Peak charging port usage: {max(occupied_ports)}/{total_ports[0] if total_ports else 0}")
    print(f"Peak utilization: {max(utilization):.1f}%")
    print("=" * 40)

def run_and_visualize_simulation():
    """Run simulation and create time-series visualizations with the selected algorithm(s)"""
    algorithm = CONFIG['allocation']['algorithm']
    
    if algorithm.upper() == 'ALL':
        # Run all algorithms
        algorithms = ['nearest', 'queue_time', 'least_utilized', 'cost_based']
        for algo in algorithms:
            run_simulation_with_algorithm(algo)
    else:
        # Run with the specified algorithm
        run_simulation_with_algorithm(algorithm, output_suffix='')

if __name__ == "__main__":
    print("Creating network visualization...")
    visualize_network_and_stations()
    
    print("\nRunning simulation with visualization...")
    run_and_visualize_simulation()

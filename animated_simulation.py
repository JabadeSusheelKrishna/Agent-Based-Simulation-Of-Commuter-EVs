import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
from ev_simulation import EVSimulation
import numpy as np
from matplotlib.patches import Circle
import time

class AnimatedSimulation:
    """Create animated visualization of agent movement"""
    
    def __init__(self, roads_file: str, charging_points_file: str, num_agents: int = 10):
        self.sim = EVSimulation(roads_file, charging_points_file)
        self.sim.create_agents(num_agents)
        
        # Store simulation snapshots
        self.snapshots = []
        self.time_labels = []
        
        # Setup plot
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.setup_base_map()
        
    def setup_base_map(self):
        """Setup the base map with roads and fixed locations"""
        # Create position dictionary for road network
        self.pos = {}
        for node in self.sim.road_network.nodes():
            node_data = self.sim.road_network.nodes[node]
            self.pos[node] = (node_data['x'], node_data['y'])
        
        # Draw road network (static)
        nx.draw_networkx_edges(self.sim.road_network, self.pos, ax=self.ax, 
                              edge_color='gray', alpha=0.3, width=0.5)
        nx.draw_networkx_nodes(self.sim.road_network, self.pos, ax=self.ax, 
                              node_color='lightgray', node_size=5, alpha=0.5)
        
        # Draw charging stations (static)
        station_x = [station.location.lon for station in self.sim.charging_stations]
        station_y = [station.location.lat for station in self.sim.charging_stations]
        self.ax.scatter(station_x, station_y, c='red', s=150, marker='s', 
                       label='Charging Stations', zorder=3, edgecolors='black')
        
        # Draw home locations (static)
        home_x = [agent.home.lon for agent in self.sim.agents]
        home_y = [agent.home.lat for agent in self.sim.agents]
        self.ax.scatter(home_x, home_y, c='green', s=80, marker='o', 
                       label='Homes', zorder=2, alpha=0.7, edgecolors='darkgreen')
        
        # Draw office locations (static)
        office_x = [agent.office.lon for agent in self.sim.agents]
        office_y = [agent.office.lat for agent in self.sim.agents]
        unique_offices = list(set(zip(office_x, office_y)))
        office_unique_x = [loc[0] for loc in unique_offices]
        office_unique_y = [loc[1] for loc in unique_offices]
        self.ax.scatter(office_unique_x, office_unique_y, c='blue', s=120, marker='^', 
                       label='Offices', zorder=2, alpha=0.8, edgecolors='darkblue')
        
        # Setup plot properties
        self.ax.set_title('EV Agent Movement Simulation', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Longitude')
        self.ax.set_ylabel('Latitude')
        self.ax.legend(loc='upper right')
        self.ax.grid(True, alpha=0.3)
        
        # Initialize agent scatter plot (will be updated in animation)
        self.agent_scatter = self.ax.scatter([], [], s=100, c='orange', marker='o', 
                                           zorder=5, edgecolors='black', linewidth=1,
                                           label='EV Agents')
        
        # Add time and info text
        self.time_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes, 
                                     fontsize=12, verticalalignment='top',
                                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        self.info_text = self.ax.text(0.02, 0.85, '', transform=self.ax.transAxes, 
                                     fontsize=10, verticalalignment='top',
                                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    def run_simulation_and_capture(self, duration_days: int = 1, capture_interval: int = 30):
        """Run simulation and capture snapshots"""
        duration_minutes = duration_days * 24 * 60  # Convert days to minutes
        
        print(f"Running simulation for {duration_days} day(s) ({duration_days * 24} hours)...")
        print(f"Capturing snapshots every {capture_interval} minutes...")
        
        snapshot_count = 0
        while self.sim.current_time < duration_minutes:
            # Capture snapshot at intervals
            if self.sim.current_time % capture_interval == 0:
                snapshot = self.capture_snapshot()
                self.snapshots.append(snapshot)
                self.time_labels.append(self.sim.current_time)
                snapshot_count += 1
                
                if snapshot_count % 20 == 0:  # Print less frequently for longer simulations
                    day = self.sim.current_time // (24 * 60) + 1
                    hours = (self.sim.current_time % (24 * 60)) // 60
                    minutes = self.sim.current_time % 60
                    print(f"  Day {day}, {hours:02d}:{minutes:02d} - Captured {snapshot_count} snapshots")
            
            self.sim.step()
        
        print(f"Simulation complete! Captured {len(self.snapshots)} snapshots over {duration_days} day(s).")
    
    def capture_snapshot(self):
        """Capture current state of all agents"""
        snapshot = {
            'time': self.sim.current_time,
            'agents': []
        }
        
        for agent in self.sim.agents:
            agent_data = {
                'id': agent.agent_id,
                'x': agent.current_location.lon,
                'y': agent.current_location.lat,
                'battery': agent.current_battery,
                'state': agent.state,
                'needs_charging': agent.needs_charging()
            }
            snapshot['agents'].append(agent_data)
        
        # Add charging station info
        snapshot['charging_stats'] = {
            'occupied_ports': sum(s.occupied_ports for s in self.sim.charging_stations),
            'total_ports': sum(s.max_ports for s in self.sim.charging_stations),
            'queue_lengths': [len(s.queue) for s in self.sim.charging_stations]
        }
        
        return snapshot
    
    def animate_frame(self, frame_idx):
        """Animation function for each frame"""
        if frame_idx >= len(self.snapshots):
            return self.agent_scatter, self.time_text, self.info_text
        
        snapshot = self.snapshots[frame_idx]
        
        # Extract agent positions and states
        agent_x = [agent['x'] for agent in snapshot['agents']]
        agent_y = [agent['y'] for agent in snapshot['agents']]
        
        # Color agents based on their state and battery level
        colors = []
        for agent in snapshot['agents']:
            if agent['state'] == 'charging':
                colors.append('purple')  # Charging
            elif agent['state'] == 'waiting_to_charge':
                colors.append('orange')  # Waiting
            elif agent['needs_charging']:
                colors.append('red')     # Low battery
            elif 'commuting' in agent['state']:
                colors.append('yellow')  # Commuting
            elif agent['state'] == 'at_home':
                colors.append('lightgreen')  # At home
            else:  # at_office
                colors.append('lightblue')   # At office
        
        # Update agent positions
        if agent_x and agent_y:
            self.agent_scatter.set_offsets(np.column_stack((agent_x, agent_y)))
            self.agent_scatter.set_color(colors)
        
        # Update time display with day information
        total_minutes = snapshot['time']
        day = total_minutes // (24 * 60) + 1
        hours = (total_minutes % (24 * 60)) // 60
        minutes = total_minutes % 60
        time_str = f"Day {day}, {hours:02d}:{minutes:02d}"
        self.time_text.set_text(time_str)
        
        # Update info display
        stats = snapshot['charging_stats']
        state_counts = {}
        battery_levels = []
        
        for agent in snapshot['agents']:
            state = agent['state']
            if 'commuting' in state:
                state = 'commuting'
            state_counts[state] = state_counts.get(state, 0) + 1
            battery_levels.append(agent['battery'])
        
        avg_battery = np.mean(battery_levels) if battery_levels else 0
        low_battery_count = sum(1 for agent in snapshot['agents'] if agent['needs_charging'])
        
        info_lines = [
            f"Avg Battery: {avg_battery:.1f}%",
            f"Low Battery: {low_battery_count}",
            f"Charging: {stats['occupied_ports']}/{stats['total_ports']} ports",
            f"States:"
        ]
        
        for state, count in state_counts.items():
            info_lines.append(f"  {state}: {count}")
        
        self.info_text.set_text('\n'.join(info_lines))
        
        return self.agent_scatter, self.time_text, self.info_text
    
    def create_animation(self, interval: int = 500, save_gif: bool = True):
        """Create and optionally save animation"""
        print("Creating animation...")
        
        # Create animation
        anim = animation.FuncAnimation(
            self.fig, self.animate_frame, frames=len(self.snapshots),
            interval=interval, blit=False, repeat=True
        )
        
        # Add legend for agent colors
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', 
                      markersize=10, label='At Home'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', 
                      markersize=10, label='At Office'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', 
                      markersize=10, label='Commuting'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                      markersize=10, label='Low Battery'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='purple', 
                      markersize=10, label='Charging'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', 
                      markersize=10, label='Waiting to Charge')
        ]
        
        self.ax.legend(handles=legend_elements, loc='upper left', 
                      bbox_to_anchor=(0, 0.75), fontsize=9)
        
        if save_gif:
            print("Saving animation as GIF (this may take a while)...")
            anim.save('agent_movement_animation.gif', writer='pillow', fps=5)
            print("Animation saved as 'agent_movement_animation.gif'")
        
        plt.tight_layout()
        plt.show()
        
        return anim

def create_static_snapshots(duration_days: int = 1):
    """Create static snapshots at key times for quick viewing"""
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    sim.create_agents(15)
    
    # Key times to capture across multiple days: early morning, morning rush, midday, evening rush, night
    base_times = [6*60, 9*60, 12*60, 18*60, 21*60]  # 6AM, 9AM, 12PM, 6PM, 9PM
    key_times = []
    
    # Generate key times for each day
    for day in range(duration_days):
        for base_time in base_times:
            key_times.append(day * 24 * 60 + base_time)
    
    snapshots = []
    
    print(f"Creating static snapshots for {duration_days} day(s) at key times...")
    
    duration_minutes = duration_days * 24 * 60
    while sim.current_time <= duration_minutes and sim.current_time <= max(key_times):
        if sim.current_time in key_times:
            # Capture snapshot
            snapshot_data = {
                'time': sim.current_time,
                'agents': [(agent.current_location.lon, agent.current_location.lat, 
                           agent.state, agent.current_battery, agent.needs_charging()) 
                          for agent in sim.agents],
                'stats': sim.get_simulation_stats()
            }
            snapshots.append(snapshot_data)
        
        sim.step()
    
    # Create subplot grid - adjust based on number of snapshots
    num_snapshots = len(snapshots)
    cols = min(5, num_snapshots)
    rows = (num_snapshots + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3*rows))
    if num_snapshots == 1:
        axes = [axes]
    elif rows == 1:
        axes = axes if isinstance(axes, list) else [axes]
    else:
        axes = axes.flatten()
    
    for idx, snapshot in enumerate(snapshots):
        ax = axes[idx]
        
        # Draw base map
        pos = {}
        for node in sim.road_network.nodes():
            node_data = sim.road_network.nodes[node]
            pos[node] = (node_data['x'], node_data['y'])
        
        nx.draw_networkx_edges(sim.road_network, pos, ax=ax, 
                              edge_color='gray', alpha=0.3, width=0.5)
        
        # Draw charging stations
        station_x = [station.location.lon for station in sim.charging_stations]
        station_y = [station.location.lat for station in sim.charging_stations]
        ax.scatter(station_x, station_y, c='red', s=100, marker='s', zorder=3)
        
        # Draw agents with color coding
        agent_x = [agent[0] for agent in snapshot['agents']]
        agent_y = [agent[1] for agent in snapshot['agents']]
        
        colors = []
        for agent in snapshot['agents']:
            state, battery, needs_charging = agent[2], agent[3], agent[4]
            if state == 'charging':
                colors.append('purple')
            elif needs_charging:
                colors.append('red')
            elif 'commuting' in state:
                colors.append('yellow')
            elif state == 'at_home':
                colors.append('green')
            else:
                colors.append('blue')
        
        ax.scatter(agent_x, agent_y, c=colors, s=80, zorder=4, alpha=0.8)
        
        # Title with day, time and stats
        total_minutes = snapshot['time']
        day = total_minutes // (24 * 60) + 1
        hours = (total_minutes % (24 * 60)) // 60
        minutes = total_minutes % 60
        stats = snapshot['stats']
        
        title = f"Day {day}, {hours:02d}:{minutes:02d}\n"
        title += f"Avg Battery: {stats['avg_battery']:.1f}%\n"
        title += f"Charging: {stats['agents_charging']}, Commuting: {stats['agents_commuting']}"
        
        ax.set_title(title, fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Longitude', fontsize=8)
        ax.set_ylabel('Latitude', fontsize=8)
    
    # Remove empty subplots
    for idx in range(len(snapshots), len(axes)):
        axes[idx].remove()
    
    plt.tight_layout()
    plt.savefig('simulation_snapshots.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function to run animated simulation"""
    print("=== EV Agent Movement Animation ===")
    print("Choose visualization type:")
    print("1. Full animation (takes longer but shows complete movement)")
    print("2. Static snapshots (quick overview at key times)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    # Get duration in days
    try:
        days = int(input("Enter number of days to simulate (1-7): ").strip())
        days = max(1, min(7, days))  # Limit between 1-7 days
    except ValueError:
        days = 1
        print("Invalid input, using 1 day.")
    
    if choice == "2":
        create_static_snapshots(duration_days=days)
    else:
        # Create animated simulation
        anim_sim = AnimatedSimulation('roads.geojson', 'charging_points.geojson', num_agents=15)
        
        # Run simulation and capture data
        # Adjust capture interval based on duration to keep animation reasonable
        capture_interval = 30 if days == 1 else 60 if days <= 3 else 120
        print(f"Using capture interval of {capture_interval} minutes for {days} day(s)")
        
        anim_sim.run_simulation_and_capture(duration_days=days, capture_interval=capture_interval)
        
        # Create animation
        anim = anim_sim.create_animation(interval=800, save_gif=True)

if __name__ == "__main__":
    main()

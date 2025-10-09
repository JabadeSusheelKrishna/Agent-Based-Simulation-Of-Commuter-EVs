#!/usr/bin/env python3
"""
Debug script to test agent behavior and identify issues
"""

from ev_simulation import EVSimulation
import time

def debug_agent_behavior():
    """Debug agent behavior over time"""
    sim = EVSimulation('roads.geojson', 'charging_points.geojson')
    sim.create_agents(5)  # Use fewer agents for easier debugging
    
    print("=== Agent Behavior Debug ===")
    print(f"Created {len(sim.agents)} agents")
    
    # Print initial agent states
    print("\nInitial Agent States:")
    for i, agent in enumerate(sim.agents):
        print(f"Agent {i}: State={agent.state}, Battery={agent.current_battery:.1f}%, "
              f"Home=({agent.home.lat:.4f},{agent.home.lon:.4f}), "
              f"Office=({agent.office.lat:.4f},{agent.office.lon:.4f})")
    
    # Run simulation for 2 days with detailed logging
    duration_minutes = 2 * 24 * 60  # 2 days
    log_interval = 60  # Log every hour
    
    print(f"\nRunning simulation for 2 days...")
    print("Time | Agent States | Battery Levels")
    print("-" * 80)
    
    while sim.current_time < duration_minutes:
        # Log state every hour
        if sim.current_time % log_interval == 0:
            day = sim.current_time // (24 * 60) + 1
            hours = (sim.current_time % (24 * 60)) // 60
            minutes = sim.current_time % 60
            
            states = [agent.state for agent in sim.agents]
            batteries = [f"{agent.current_battery:.0f}%" for agent in sim.agents]
            
            state_counts = {}
            for state in states:
                simplified_state = state
                if 'commuting' in state:
                    simplified_state = 'commuting'
                state_counts[simplified_state] = state_counts.get(simplified_state, 0) + 1
            
            print(f"D{day} {hours:02d}:{minutes:02d} | {state_counts} | Avg: {sum(agent.current_battery for agent in sim.agents)/len(sim.agents):.1f}%")
            
            # Check if all agents are stuck in one state
            if len(set(states)) == 1 and states[0] not in ['at_home', 'at_office']:
                print(f"WARNING: All agents stuck in state: {states[0]}")
                break
        
        sim.step()
    
    print("\nFinal Agent States:")
    for i, agent in enumerate(sim.agents):
        print(f"Agent {i}: State={agent.state}, Battery={agent.current_battery:.1f}%, "
              f"Location=({agent.current_location.lat:.4f},{agent.current_location.lon:.4f})")

def test_time_logic():
    """Test the time-based scheduling logic"""
    print("\n=== Time Logic Test ===")
    
    # Test time calculations for multi-day simulation
    test_times = [0, 8*60, 12*60, 17*60, 23*60, 24*60, 32*60, 41*60]  # Various times across 2 days
    
    for time_minutes in test_times:
        day = time_minutes // (24 * 60) + 1
        hours = (time_minutes % (24 * 60)) // 60
        minutes = time_minutes % 60
        time_in_day = time_minutes % (24 * 60)
        
        # Check if it's morning commute time (8-10 AM)
        morning_start = 8 * 60
        is_morning_commute = morning_start <= time_in_day < morning_start + 120
        
        # Check if it's evening commute time (5-7 PM)
        evening_start = 17 * 60
        is_evening_commute = evening_start <= time_in_day < evening_start + 120
        
        print(f"Day {day}, {hours:02d}:{minutes:02d} (time_in_day={time_in_day}) -> "
              f"Morning: {is_morning_commute}, Evening: {is_evening_commute}")

if __name__ == "__main__":
    test_time_logic()
    debug_agent_behavior()

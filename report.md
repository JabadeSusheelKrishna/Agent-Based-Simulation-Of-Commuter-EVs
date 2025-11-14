# Agent-Based Simulation of Commuter EVs

## Overview

This project simulates the daily movement and charging behavior of commuter electric vehicles (EVs) in a city, using an agent-based approach. The simulation models agents (EVs) traveling between home, office, shops, and restaurants, interacting with a road network and charging stations. The simulation generates timestamped data for agents and charging stations under different charging station allocation algorithms.

---

## Key Features

### 1. Charging Station Allocation Algorithms

Three distinct algorithms are implemented to allocate charging stations to agents when their battery is low:

- **Nearest Station Allocation**:  
  Agents are assigned to the geographically closest charging station that can accept them. The shortest path is computed using Dijkstra's algorithm.

- **Random Station Allocation**:  
  Agents are assigned randomly to any available charging station with space in its queue.

- **Least Queue Allocation**:  
  Agents are assigned to the charging station with the smallest waiting queue, minimizing wait times.

Each method is run separately, and results are saved in different JSON files for comparison.

---

### 2. Dynamic Speed Based on Road Types

- The road network is modeled as nodes and edges, with each edge having a `speed_limit` property.
- When agents move, their speed is dynamically set according to the speed limit of the current road segment.
- The distance covered per time step and battery consumption are calculated based on this dynamic speed, making the simulation realistic.

---

### 3. Shops and Restaurants as New Features

- Each agent is assigned a unique shop and restaurant (distinct from home and office).
- Agents have scheduled visits to these locations, with random start times and durations.
- The simulation supports:
  - **Shop Visits**: Agents move from home to shop at a scheduled time, stay for a set duration, then proceed to the next activity.
  - **Restaurant Visits**: After the shop, agents may visit a restaurant, again with scheduled times and durations.

---

### 4. Dedicated Date and Time for Shop/Restaurant Visits

- Each agent is assigned a specific day of the week (0=Monday to 6=Sunday) for shop and restaurant visits.
- Visit times are randomized but consistent for each agent, ensuring realistic scheduling.
- The simulation tracks the agent’s state transitions (e.g., moving to shop, at shop, moving to restaurant, etc.) based on the current simulation time and agent schedule.

---

### 5. Timestamped Data Generation

- At every simulation time step (minute), the state of all agents and charging stations is recorded.
- Data includes:
  - Agent position, battery percentage, current state, target, shop/restaurant info, distance traveled, speed, etc.
  - Charging station status: available ports, charging agents, waiting queue, etc.
- Results are saved in JSON files (`simulation_output_nearest.json`, `simulation_output_random.json`, `simulation_output_least_queue.json`), enabling analysis and visualization.

---

## Simulation Process

1. **Initialization**:
   - Road network and charging stations are loaded from GeoJSON files.
   - Agents are initialized with random home/office locations, battery parameters, and shop/restaurant schedules.

2. **Main Loop**:
   - For each minute of the simulation period:
     - Agents check if they need to move (to office, home, shop, restaurant) based on their schedule.
     - If battery is low, agents are allocated a charging station using the selected algorithm.
     - Agents move along the computed path, updating position, speed, and battery.
     - Charging stations manage queues and charging processes.
     - All states are recorded with timestamps.

3. **Output**:
   - Simulation data is saved in JSON files for each allocation method.
   - Summary statistics are printed at the end of each run.

---
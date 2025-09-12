# Agent-Based Simulation of Commuter EVs

![Project Overview](./project.png)

## Overview

This project implements an **Agent-Based Model (ABM)** to simulate Electric Vehicle (EV) commuter behavior and charging infrastructure utilization in the Kondapur-Hitech City-Gachibowli corridor of Hyderabad. The simulation models realistic commuting patterns, battery consumption, and charging station dynamics to analyze EV adoption scenarios and infrastructure requirements.

## Features

### 🚗 EV Agent Modeling
- **Realistic Vehicle Properties**: Battery capacity (30-60 kWh), energy consumption (0.12-0.18 kWh/km)
- **Individual Behavior**: Personalized charging thresholds, home/work locations, and commuting patterns
- **State Machine**: Comprehensive status tracking (at_home, commuting, at_work, seeking_charge, charging)

### ⚡ Charging Infrastructure
- **Dynamic Charging Stations**: Variable capacity (2-6 ports per station)
- **Queue Management**: Realistic waiting systems when stations are full
- **22kW AC Charging**: Standard charging rates with time-based battery replenishment

### 📊 Simulation Analytics
- **Real-time Monitoring**: Step-by-step agent actions and station utilization
- **Performance Metrics**: Wait times, charging success rates, station efficiency
- **Utilization Reports**: Average and peak usage statistics for infrastructure planning

### 🌍 Geographic Modeling
- **Real Coordinates**: Kondapur-Hitech City-Gachibowli area (17.43-17.46°N, 78.33-78.38°E)
- **Haversine Distance**: Accurate distance calculations for energy consumption
- **Random Location Generation**: Realistic distribution of home/work locations

## Project Structure

```
├── main.py              # Entry point and simulation orchestration
├── configurations.py    # Simulation parameters and area bounds
├── evagents.py         # EV agent class with behavior logic
├── chargingstations.py # Charging station infrastructure model
├── simulations.py      # Main simulation engine and time management
├── functions.py        # Utility functions (distance, location generation)
└── project.png         # Project visualization
```

## Installation & Setup

### Prerequisites
- Python 3.7+
- Standard Python libraries (random, math, time)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-username/Agent-Based-Simulation-Of-Commuter-EVs.git
cd Agent-Based-Simulation-Of-Commuter-EVs

# Run the simulation
python3 main.py
```

## Configuration

Modify `configurations.py` to customize simulation parameters:

```python
# Simulation scale
NUM_EV_AGENTS = 50              # Number of EV commuters
NUM_CHARGING_STATIONS = 5       # Number of charging stations
SIMULATION_HOURS = 24           # Simulation duration
TIME_STEP_MINUTES = 15          # Time resolution

# Geographic area (Hyderabad IT corridor)
AREA_BOUNDS = {
    "min_lat": 17.43, "max_lat": 17.46,
    "min_lon": 78.33, "max_lon": 78.38
}
```

## Simulation Output

The simulation provides detailed logging including:
- Agent commuting and charging decisions
- Real-time battery state of charge (SOC) updates
- Charging station occupancy and queue status
- Comprehensive final report with utilization statistics

### Sample Output
```
--- Time: Day 1, 08:15 ---
Agent 12: Drove 8.3 km. SOC is now 67%.
Station 2: Port occupied by Agent 7. Available ports: 1/3
Agent 15: SOC at 23% is below threshold (30%). Seeking a charging station.

--- Simulation Report ---
Total Agents: 50
Total Charging Stations: 5
Successful Charges Initiated: 127
Average Wait Time per Charge: 8.45 minutes
Station 0: Average Busy Ports: 2.1 (70.0%), Peak: 3 (100.0%)
```

## Research Applications

This simulation framework supports research in:
- **EV Infrastructure Planning**: Optimal charging station placement and capacity
- **Grid Load Analysis**: Peak demand prediction and load balancing
- **Policy Impact Assessment**: Incentive programs and adoption scenarios
- **Urban Mobility**: Integration with public transport and ride-sharing

## Technical Details

### Agent Behavior Model
- **Morning Commute**: 8:00-9:00 AM (home → work)
- **Evening Commute**: 5:00-6:00 PM (work → home)
- **Charging Logic**: Threshold-based (20-40% SOC) with 90% target
- **Energy Consumption**: Distance-based with realistic efficiency factors

### Charging Station Logic
- **Port Management**: First-come-first-served with queue overflow
- **Charging Rate**: 22kW AC (typical public charging)
- **Utilization Tracking**: Continuous monitoring for capacity planning

## Future Enhancements

- [ ] Integration with real traffic data
- [ ] Dynamic pricing models
- [ ] Fast charging (DC) station support
- [ ] Multi-modal transportation options
- [ ] Machine learning for behavior prediction
- [ ] Visualization dashboard with maps and charts

## Academic Context

**BTech Project** - This repository contains the implementation of agent-based modeling techniques in Python for studying electric vehicle adoption and charging infrastructure in urban environments.

## Contributing

This is an academic project. For questions or collaboration opportunities, please open an issue or contact the project maintainers.

## License

This project is developed for educational and research purposes.

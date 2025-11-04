# Custom Charging Station Allocation Guide

This document explains how to implement custom charging station allocation algorithms in the EV simulation.

## Overview
The simulation uses a flexible architecture that allows you to implement different strategies for allocating charging stations to electric vehicles (EVs). The default implementation uses a simple nearest-station strategy, but you can create more sophisticated algorithms.

## Architecture

### Key Components

1. **ChargingAllocator** (Base Class)
   - Abstract base class that defines the interface for all allocation algorithms
   - Must implement the `allocate_charging_station` class method

2. **ChargingAllocationContext**
   - Data class containing all information needed for allocation decisions
   - Provides access to the agent, charging stations, road network, etc.

3. **NearestAllocator**
   - Default implementation that selects the nearest available charging station

## How to Implement a Custom Allocator

### 1. Create a New Allocator Class

Create a new Python class that inherits from `ChargingAllocator`:

```python
from chargingAllocator import ChargingAllocator, ChargingAllocationContext
from typing import Optional

class MyCustomAllocator(ChargingAllocator):
    """
    Custom charging station allocator that implements [your strategy].
    """
    
    @classmethod
    def allocate_charging_station(
        cls, 
        context: ChargingAllocationContext
    ) -> Optional['ChargingStation']:
        """
        Implement your custom allocation logic here.
        
        Args:
            context: Contains all necessary information for making the decision
            
        Returns:
            The selected ChargingStation, or None if no suitable station is found
        """
        # Your implementation here
        pass
```

### 2. Available Context Information

The `context` parameter provides access to:

- `context.agent`: The `EVAgent` that needs charging
  - `agent.current_location`: Current location of the agent
  - `agent.current_battery`: Current battery level (kWh)
  - `agent.battery_capacity`: Maximum battery capacity (kWh)
  - `agent.consumption_rate`: Energy consumption rate (kWh/km)
  - `agent.state`: Current state (e.g., 'charging', 'waiting_to_charge')

- `context.charging_stations`: List of all available `ChargingStation` objects
  - `station.location`: Location of the station
  - `station.is_available()`: Check if station has available ports
  - `station.occupied_ports`: Number of ports currently in use
  - `station.max_ports`: Maximum number of ports
  - `station.queue`: Queue of agents waiting to charge

- `context.current_time`: Current simulation time in minutes
- `context.road_network`: The road network (NetworkX graph)
- `context.additional_context`: Optional dictionary for additional data

### 3. Example: Load-Balanced Allocator

Here's an example of a load-balancing allocator that distributes EVs across stations:

```python
class LoadBalancedAllocator(ChargingAllocator):
    """
    Allocates charging stations based on current load (queue length + active chargers).
    Prefers stations with the least current load.
    """
    
    @classmethod
    def allocate_charging_station(
        cls, 
        context: ChargingAllocationContext
    ) -> Optional['ChargingStation']:
        if not context.charging_stations:
            return None
            
        # Filter to only available stations
        available_stations = [s for s in context.charging_stations if s.is_available()]
        if not available_stations:
            return None
            
        # Calculate load for each station (queue length + active chargers)
        def calculate_load(station):
            return len(station.queue) + station.occupied_ports
            
        # Return station with minimum load
        return min(available_stations, key=calculate_load)
```

### 4. Using Your Custom Allocator

To use your custom allocator, pass it to the `get_charging_station` function:

```python
from chargingAllocator import get_charging_station, ChargingAllocationContext
from my_custom_allocator import MyCustomAllocator

# When you need to allocate a charging station
station = get_charging_station(
    context=charging_context,
    allocator=MyCustomAllocator  # Your custom allocator class
)
```

### 5. Testing Your Allocator

1. Create test cases with different scenarios
2. Verify that your allocator behaves as expected
3. Compare performance with the default allocator using metrics like:
   - Average waiting time
   - Queue lengths
   - Battery levels when charging starts
   - Distance traveled to charging stations

## Best Practices

1. **Efficiency**: Keep your allocation algorithm efficient, especially for large numbers of stations/agents
2. **Thread Safety**: If you modify shared data, ensure thread safety
3. **Logging**: Add logging to help debug and analyze decisions
4. **Documentation**: Document your algorithm's behavior and any assumptions it makes
5. **Testing**: Test with various scenarios and edge cases

## Example Use Cases

1. **Time-Based Allocation**: Different strategies for peak vs off-peak hours
2. **Priority-Based**: Allocate based on agent priority (e.g., emergency vehicles first)
3. **Predictive Allocation**: Use historical data to predict station availability
4. **Cost-Based**: Consider electricity costs at different stations
5. **Battery-Aware**: Consider remaining battery and distance to stations

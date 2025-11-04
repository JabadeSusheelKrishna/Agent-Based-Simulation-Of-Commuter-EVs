"""
Charging station allocation module for EV simulation.

This module provides a flexible framework for implementing different charging station
allocation algorithms. The default implementation uses a simple nearest-station strategy,
but can be extended with more sophisticated algorithms.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar, TYPE_CHECKING
from dataclasses import dataclass

# Import types for type hints without circular imports
if TYPE_CHECKING:
    from ev_simulation import EVAgent, ChargingStation, Location

@dataclass
class ChargingAllocationContext:
    """Context class containing all the information needed for charging allocation decisions.
    This provides a single object that can be passed to allocation algorithms with all necessary data.
    """
    # Agent that needs charging
    agent: 'EVAgent'
    
    # List of all available charging stations
    charging_stations: List['ChargingStation']
    
    # Current simulation time in minutes
    current_time: int
    
    # Road network (NetworkX graph)
    road_network: Any
    
    # Optional: Additional context that might be needed by more complex algorithms
    # For example, current traffic conditions, historical usage patterns, etc.
    additional_context: Optional[Dict[str, Any]] = None


class ChargingAllocator:
    """Base class for all charging allocation algorithms.
    
    To implement a new allocation algorithm, subclass this and implement the allocate_charging_station method.
    """
    
    @classmethod
    def allocate_charging_station(cls, context: 'ChargingAllocationContext') -> Optional['ChargingStation']:
        """
        Allocate a charging station to the agent based on the given context.
        
        Args:
            context: ChargingAllocationContext containing all necessary information
            
        Returns:
            The selected ChargingStation, or None if no suitable station is found
        """
        raise NotImplementedError("Subclasses must implement this method")


class NearestAllocator(ChargingAllocator):
    """Simple allocator that selects the nearest available charging station."""
    
    @classmethod
    def allocate_charging_station(cls, context: 'ChargingAllocationContext') -> Optional['ChargingStation']:
        """Find the nearest charging station with available capacity."""
        if not context.charging_stations:
            return None
            
        min_distance = float('inf')
        nearest_station = None
        
        for station in context.charging_stations:
            distance = context.agent.current_location.distance_to(station.location)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
                
        return nearest_station


# Default allocator to use if none is specified
DEFAULT_ALLOCATOR = NearestAllocator

def get_charging_station(
    context: 'ChargingAllocationContext',
    allocator: Type['ChargingAllocator'] = DEFAULT_ALLOCATOR
) -> Optional['ChargingStation']:
    """
    Get a charging station for the given agent using the specified allocation strategy.
    
    This is the main entry point that should be used by the simulation.
    
    Args:
        context: ChargingAllocationContext containing all necessary information
        allocator: The allocator class to use (defaults to NearestAllocator)
        
    Returns:
        The selected ChargingStation, or None if no suitable station is found
    """
    return allocator.allocate_charging_station(context)

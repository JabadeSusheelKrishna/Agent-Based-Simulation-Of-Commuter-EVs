"""
Charging station allocation module for EV simulation.

This module provides a flexible framework for implementing different charging station
allocation algorithms. The default implementation uses a simple nearest-station strategy,
but can be extended with more sophisticated algorithms.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar, TYPE_CHECKING, Tuple
from dataclasses import dataclass
import heapq
import yaml
import os
from collections import defaultdict

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
        agent = context.agent
        min_distance = float('inf')
        best_station = None
        
        for station in context.charging_stations:
            if station.is_available():
                distance = agent.current_location.distance_to(station.location)
                if distance < min_distance:
                    min_distance = distance
                    best_station = station
                    
        return best_station


class NearestAvailableWithQueueTimeAllocator(ChargingAllocator):
    """
    Allocator that considers both distance and estimated waiting time.
    It calculates a score based on travel time + estimated queue time.
    """
    
    @classmethod
    def allocate_charging_station(cls, context: 'ChargingAllocationContext') -> Optional['ChargingStation']:
        agent = context.agent
        best_score = float('inf')
        best_station = None
        
        for station in context.charging_stations:
            # Get algorithm parameters from config
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ProjectConfigs.yaml')
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    params = config.get('allocation', {}).get('parameters', {})
                    queue_params = params.get('queue_time', {})
                    avg_charging_time = queue_params.get('average_charging_time', 30)
                    capacity_weight = queue_params.get('capacity_weight', 0.2)
            except (FileNotFoundError, yaml.YAMLError):
                avg_charging_time = 30
                capacity_weight = 0.2
            
            # Calculate travel time (assuming constant speed of 30 km/h for simplicity)
            distance_km = agent.current_location.distance_to(station.location) / 1000  # Convert to km
            travel_time = (distance_km / 30) * 60  # Convert to minutes
            
            # Estimate queue time (number in queue * average charging time)
            queue_time = len(station.queue) * avg_charging_time
            
            # If station has available ports, no queue time
            if station.is_available():
                queue_time = 0
            
            # Calculate total estimated time (travel + queue)
            total_time = travel_time + queue_time
            
            # Consider station capacity in the score
            capacity_factor = 1.0 - (station.occupied_ports / station.max_ports)
            score = total_time * (1.0 + (1 - capacity_weight) - (capacity_factor * capacity_weight))
            
            if score < best_score:
                best_score = score
                best_station = station
                
        return best_station


class LeastUtilizedAllocator(ChargingAllocator):
    """
    Allocator that prefers stations with more available ports and shorter queues.
    This helps balance the load across all charging stations.
    """
    
    @classmethod
    def allocate_charging_station(cls, context: 'ChargingAllocationContext') -> Optional['ChargingStation']:
        agent = context.agent
        best_score = -1
        best_station = None
        
        for station in context.charging_stations:
            # Calculate utilization score (higher is better)
            # More available ports = better
            available_ports = station.max_ports - station.occupied_ports
            
            # Shorter queue = better
            queue_length = len(station.queue)
            
            # Calculate score (prioritize available ports over queue length)
            if available_ports > 0:
                # If station has available ports, prioritize by available ports first
                score = available_ports * 1000 - queue_length
            else:
                # If no available ports, prioritize by shortest queue
                score = -queue_length
            
            # Slight preference for closer stations if scores are equal
            distance = agent.current_location.distance_to(station.location) / 1000  # km
            score -= distance * 0.1  # Small penalty for distance
            
            if score > best_score or (score == best_score and 
                                    best_station and 
                                    distance < agent.current_location.distance_to(best_station.location) / 1000):
                best_score = score
                best_station = station
                
        return best_station


class CostBasedAllocator(ChargingAllocator):
    """
    Allocator that considers charging cost, distance, and station utilization.
    Assumes that charging stations may have different pricing models.
    """
    
    @classmethod
    def get_charging_cost(cls, station: 'ChargingStation', kwh_needed: float) -> float:
        """Calculate the cost to charge at a station.
        This is a simple implementation - you can customize the pricing model as needed.
        """
        # Get cost parameters from config
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ProjectConfigs.yaml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                params = config.get('allocation', {}).get('parameters', {})
                cost_params = params.get('cost_based', {})
                base_rate = cost_params.get('base_charging_rate', 0.15)
                utilization_impact = cost_params.get('utilization_impact', 0.5)
        except (FileNotFoundError, yaml.YAMLError):
            base_rate = 0.15
            utilization_impact = 0.5
        
        # Dynamic pricing based on utilization
        utilization = station.occupied_ports / station.max_ports
        dynamic_multiplier = 1.0 + (utilization * utilization_impact)
        
        return kwh_needed * base_rate * dynamic_multiplier
    
    @classmethod
    def allocate_charging_station(cls, context: 'ChargingAllocationContext') -> Optional['ChargingStation']:
        agent = context.agent
        best_score = float('inf')
        best_station = None
        
        # Estimate battery needed (simplified - you might want to improve this)
        battery_needed = agent.battery_capacity - agent.current_battery
        kwh_needed = (battery_needed / 100) * agent.battery_capacity  # Convert % to kWh
        
        for station in context.charging_stations:
            # Calculate distance in km
            distance_km = agent.current_location.distance_to(station.location) / 1000
            
            # Get cost parameters from config
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ProjectConfigs.yaml')
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    params = config.get('allocation', {}).get('parameters', {})
                    cost_params = params.get('cost_based', {})
                    travel_cost_per_km = cost_params.get('travel_cost_per_km', 0.15)
                    time_value = cost_params.get('time_value', 0.2)
                    max_utilization_penalty = cost_params.get('utilization_penalty', 5.0)
            except (FileNotFoundError, yaml.YAMLError):
                travel_cost_per_km = 0.15
                time_value = 0.2
                max_utilization_penalty = 5.0
            
            # Calculate travel cost
            travel_cost = distance_km * travel_cost_per_km
            
            # Calculate charging cost
            charging_cost = cls.get_charging_cost(station, kwh_needed)
            
            # Calculate queue time cost (if any)
            avg_charging_time = 30  # minutes
            queue_time = len(station.queue) * avg_charging_time
            time_cost = queue_time * time_value
            
            # Calculate total cost
            total_cost = travel_cost + charging_cost + time_cost
            
            # Adjust score based on station utilization (prefer less utilized stations)
            utilization_penalty = (station.occupied_ports / station.max_ports) * max_utilization_penalty
            
            final_score = total_cost + utilization_penalty
            
            if final_score < best_score or (final_score == best_score and 
                                          best_station and 
                                          distance_km < agent.current_location.distance_to(best_station.location) / 1000):
                best_score = final_score
                best_station = station
                
        return best_station


# Mapping of algorithm names to their respective classes
ALLOCATOR_MAP = {
    'nearest': NearestAllocator,
    'queue_time': NearestAvailableWithQueueTimeAllocator,
    'least_utilized': LeastUtilizedAllocator,
    'cost_based': CostBasedAllocator
}

# Default allocator to use if none is specified
DEFAULT_ALGORITHM = 'queue_time'

def get_allocator_class(algorithm_name: str = None) -> Type['ChargingAllocator']:
    """
    Get the allocator class based on the algorithm name from config.
    
    Args:
        algorithm_name: Name of the algorithm to use. If None, reads from config.
        
    Returns:
        The corresponding allocator class
    """
    if algorithm_name is None:
        # Load from config file if not specified
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ProjectConfigs.yaml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                algorithm_name = config.get('allocation', {}).get('algorithm', DEFAULT_ALGORITHM)
        except (FileNotFoundError, yaml.YAMLError):
            algorithm_name = DEFAULT_ALGORITHM
    
    return ALLOCATOR_MAP.get(algorithm_name.lower(), NearestAvailableWithQueueTimeAllocator)

# Default allocator instance
DEFAULT_ALLOCATOR = get_allocator_class()

def get_charging_station(
    context: 'ChargingAllocationContext',
    allocator: Optional[Type['ChargingAllocator']] = None
) -> Optional['ChargingStation']:
    """
    Get a charging station for the given agent using the specified allocation strategy.
    
    This is the main entry point that should be used by the simulation.
    
    Args:
        context: ChargingAllocationContext containing all necessary information
        allocator: The allocator class to use (defaults to value from config)
        
    Returns:
        The selected ChargingStation, or None if no suitable station is found
    """
    if not context.charging_stations:
        return None
        
    # If no allocator is specified, use the one from config
    if allocator is None:
        allocator = get_allocator_class()
        
    return allocator.allocate_charging_station(context)

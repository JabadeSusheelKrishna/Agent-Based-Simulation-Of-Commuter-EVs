# This file contains visualization functions for simulation data

# Import necessary libraries
import json
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd

# Load simulation data
with open('simulation_output.json') as f:
    output_data = json.load(f)

with open('simulation_data2.json') as f:
    data2 = json.load(f)

with open('simulation_data3.json') as f:
    data3 = json.load(f)

# Load geo-coordinates
roads = gpd.read_file('roads.geojson')

# Function to visualize charging station usage

def plot_charging_station_usage(data):
    # Extract relevant data
    charging_data = data['charging_stations']
    # Create a bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(charging_data['station_id'], charging_data['usage'], color='blue')
    plt.title('Charging Station Usage')
    plt.xlabel('Charging Station ID')
    plt.ylabel('Usage Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Function to visualize agent locations

def plot_agent_locations(data):
    # Extract agent locations
    agent_locations = data['agents']
    plt.figure(figsize=(10, 6))
    plt.scatter(agent_locations['x'], agent_locations['y'], c='green', label='Agents')
    plt.title('Agent Locations')
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.legend()
    plt.tight_layout()
    plt.show()

# Function to visualize agent status

def plot_agent_status(data):
    status_counts = data['agent_status'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title('Agent Status Distribution')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.show()

# Call the plotting functions for each dataset
plot_charging_station_usage(output_data)
plot_agent_locations(output_data)
plot_agent_status(output_data)

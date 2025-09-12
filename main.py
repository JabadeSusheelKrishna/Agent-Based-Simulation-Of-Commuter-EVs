import random
import math
import time

from configurations import *
from functions import *
from chargingstations import *
from evagents import *
from simulations import *

# --- Main Execution ---
if __name__ == "__main__":
    simulation = Simulation(num_agents=NUM_EV_AGENTS, num_stations=NUM_CHARGING_STATIONS)
    simulation.run_simulation()

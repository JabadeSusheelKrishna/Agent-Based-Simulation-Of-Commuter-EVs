# --- Model Classes ---

class ChargingStation:
    """Represents a public EV charging station."""
    def __init__(self, station_id, location):
        self.id = station_id
        self.location = location
        self.capacity = random.randint(2, 6) # Number of charging ports
        self.available_ports = self.capacity
        self.queue = []
        self.utilization_log = []

    def is_available(self):
        """Check if a charging port is free."""
        return self.available_ports > 0

    def occupy_port(self, agent_id):
        """Occupy a port for charging."""
        if self.is_available():
            self.available_ports -= 1
            print(f"Station {self.id}: Port occupied by Agent {agent_id}. Available ports: {self.available_ports}/{self.capacity}")
            return True
        return False

    def release_port(self):
        """Release a port after charging."""
        if self.available_ports < self.capacity:
            self.available_ports += 1
        # Serve the next agent in the queue if any
        if self.queue and self.is_available():
            next_agent_id = self.queue.pop(0)
            # This logic would be handled by the simulation loop,
            # informing the agent it can now charge.
            print(f"Station {self.id}: Port released. Notifying Agent {next_agent_id} from queue.")

    def add_to_queue(self, agent_id):
        """Add an agent to the waiting queue."""
        self.queue.append(agent_id)
        print(f"Station {self.id}: All ports busy. Agent {agent_id} added to queue (Queue size: {len(self.queue)}).")
        
    def log_utilization(self):
        """Log the current utilization for reporting."""
        used_ports = self.capacity - self.available_ports
        self.utilization_log.append(used_ports)
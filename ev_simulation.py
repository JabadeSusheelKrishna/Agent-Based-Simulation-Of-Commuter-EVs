# define class Agents
    # agent has current position
    # office location
    # current charging percentage
    # charging drainage per distance
    # previous timestep position
    # charging threshhold
    # offset
    # current state of the agent
    # target of the agent
    # prev target
    
# define states :
    # AT HOME, AT OFFICE, MOVING TO OFFICE, MOVING TO HOME, CHARGING, WAITING TO CHARGE

# define class chargingstation
    # location
    # number of ports
    # current available ports
    # agent ids charging (an array or queue)
    # queue of some length who are waiting for charging
    
# define array of agents [length = 10]
# define array of charging stations [length = 3 (as per the chargingstations.geojson file)]

# get the roads data from the roads.geojson
# initialize the charging stations from chargingstations.geojson file
    # get all the data from the geojson file itself
# initialize the agents array with some random values
    # the current pos is some random road node
    # office location is some random road node
    # current charging percentage = random (50 to 70)
    # previous timestamp position = current position (initialization)
    # charging threshold = random(20 to 30)
    # charging drainage per distance = random
    # offset = random (20 to 60 (in minutes))
    # current state = AT HOME
    # target = None
    # prev target = None
    
# define schedule
    # office start time
    # office end time

# start time = 0
# run a while loop for the simulation
    # for eachagent in agents array:
        # if start time = office starttime + offset of that agent
            # update agent
            # make the agent to move
                # target according to the time ( to office )
        # if agent.current charging percentage < threshold:
            # change the prev target as current target
            # change the target to the charging station
        # make the agent to move towards their target.
        
        # if start time = office endtime + offset of that agent
            # update agent
            # make the agent to move
                # target according to the time ( to home )
        # if agent.current charging percentage < threshold:
            # change the prev target as current target
            # change the target to the charging station
            
        # if agent.location in chargingstations location array:
            # add the agent to the charging stations waiting queue (let the charging station decide whether to charge or not)
            # change the state to WAITING TO CHARGE
            
        # else : remain in the same state
    # for each chargingstation in charging stations array:
        # clear if any agent is charged
            # for eachAgent in the charging queue
                # if eachAgent's current charging percentage is above 80:
                    # update the agentstate according to the target
                    # remove agent from queue
                    # target = prevTarget
                    # add one to the available ports
        # allocate charging to new agent
            # if available ports
            # change the state of the agent
            # add the agent from the waiting queue to the charging queue
            # change the state of the agent
    
    
    # generate all this data for each time step in a json file. (we have array of objects (agents and stations))
    
# for making the agent to move, take the help of roads data and make sure that the agent moves along the road only.
# the speed of the agent is also defined according to the road.
    # if road is highway type, then speed is 30kmph
    # if road is residential type, then speed is 15kmph
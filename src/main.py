from modules import simulator

sim = simulator.Simulator()
print(sim.conn_str)

drone = sim.connect_to_vehicle()
print(drone.is_armable)

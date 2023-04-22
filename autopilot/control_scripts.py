import dronekit
import time

def transmit_text(vehicle, text : str):
    """
    Transmits the provided status string over the Mavlink Connection
    """
    vehicle.message_factory.statustext_send(severity=5, text=text.encode())
    
def takeoff(vehicle, target_altitude=10):
	"""Script to handle when RPi is set in Takeoff Mode"""
	
	if not vehicle.is_armable:
		transmit_text(vehicle, "Vehicle not Armable")
		return
	
	print("Starting Takeoff")
	
	vehicle.mode = dronekit.VehicleMode("GUIDED")
	vehicle.armed = True
	
	# Wait until arming is confirmed
	while not vehicle.armed:
		print("Waiting to arm")
		time.sleep(1)
	
	vehicle.simple_takeoff(target_altitude)
	
	while True:
		if vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
			break
		
		time.sleep(1)
	
	transmit_text(vehicle, "Takeoff Completed")
	
def follow_mission(vehicle):
	"""Script to handle when RPi is set in FOLLOW_MISSION Mode"""
	
	print("Setting Drone to Follow Waypoints")
	
	vehicle.mode = dronekit.VehicleMode("AUTO")
	
	transmit_text(vehicle, "Following Planned Waypoints")
	

def initiate_landing_search(vehicle):
	"""Script to handle when RPi is set in LANDING_SEARCH Mode"""
	
	print("Setting Drone to follow positions")
	
	vehicle.mode = dronekit.VehicleMode("GUIDED")
	
	transmit_text(vehicle, "Following Imaging Guidance")
	

def land(vehicle):
	"""Script to handle when RPi is set in LAND Mode"""
	
	print("Setting Drone to land in place")
	
	vehicle.mode = dronekit.VehicleMode("LAND")
	
	transmit_text(vehicle, "Drone is landing")

import time
import sys
import os
import threading
import math
import networkx as nx
import tkinter as tk
import logging
from Player_API.Car import Car, DeliveryStatus
from Player_API.Map import Map

# Setup logging to file
logging.basicConfig(
    filename='hackathon_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filemode='w'
)

####################################
# INPUT YOUR TEAM INFORMATION HERE #
userName = "TeamA" # Your team name
password = "123456789" # Your team password
Car_1_ID = 10 # Could be 10, or 12
Car_2_ID = 11 # Could be 11, or 13
####################################

# GLOBAL VARIABLES
TASK_CYCLE = 1 # seconds
packages_ready_event = threading.Event()  # Event to signal when packages are ready

def gui_thread_function(car_1, car_2):
    """Thread function to display GUI showing car routes"""
    try:
        root = tk.Tk()
        root.title("Car Routes Monitor")
        root.geometry("800x600")
        
        # Create text widgets for each car
        tk.Label(root, text="Car 1 Route:", font=("Arial", 12, "bold")).pack(pady=5)
        car1_text = tk.Text(root, height=10, width=80, wrap=tk.WORD)
        car1_text.pack(pady=5, padx=10)
        
        tk.Label(root, text="Car 2 Route:", font=("Arial", 12, "bold")).pack(pady=5)
        car2_text = tk.Text(root, height=10, width=80, wrap=tk.WORD)
        car2_text.pack(pady=5, padx=10)
        
        # Status labels
        car1_status_label = tk.Label(root, text="Car 1 Status: Unknown", font=("Arial", 10))
        car1_status_label.pack(pady=2)
        
        car2_status_label = tk.Label(root, text="Car 2 Status: Unknown", font=("Arial", 10))
        car2_status_label.pack(pady=2)
        
        def update_gui():
            try:
                # Update Car 1 route
                PACKAGE_STATUS_1  = int(map_instance.map_packages[str(car_1.target_package_id)]['status'])
                PACKAGE_STATUS_2  = int(map_instance.map_packages[str(car_2.target_package_id)]['status'])
                car1_text.delete(1.0, tk.END)
                if hasattr(car_1, 'route') and car_1.route:
                    route_str = f"Route: {car_1.route}\n"
                    route_str += f"Route Length: {len(car_1.route)}\n"
                    route_str += f"Target Package: {car_1.target_package_id}\n"
                    route_str += f"Package status {PACKAGE_STATUS_1}\n"
                    route_str += f"Position: {car_1.position_mm}\n"
                    car1_text.insert(1.0, route_str)
                else:
                    car1_text.insert(1.0, "No route available")
                
                # Update Car 2 route
                car2_text.delete(1.0, tk.END)
                if hasattr(car_2, 'route') and car_2.route:
                    route_str = f"Route: {car_2.route}\n"
                    route_str += f"Route Length: {len(car_2.route)}\n"
                    route_str += f"Target Package: {car_2.target_package_id}\n"
                    route_str += f"Package status {PACKAGE_STATUS_1}\n"
                    route_str += f"Position: {car_2.position_mm}\n"
                    car2_text.insert(1.0, route_str)
                else:
                    car2_text.insert(1.0, "No route available")
                
                # Update status labels
                car1_status_label.config(text=f"Car 1 Status: {car_1.delivery_status.name if hasattr(car_1, 'delivery_status') else 'Unknown'}")
                car2_status_label.config(text=f"Car 2 Status: {car_2.delivery_status.name if hasattr(car_2, 'delivery_status') else 'Unknown'}")
                
            except Exception as e:
                logging.error(f"Error updating GUI: {e}")
            
            # Schedule next update
            root.after(1000, update_gui)  # Update every 1 second
        
        # Start the update cycle
        update_gui()
        
        # Run the GUI
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Error in GUI thread: {e}")

def Update_Map_Packages(map_instance, car_1, car_2):
    while True:
        try:
            success_car1 = car_1.update_status()
            success_car2 = car_2.update_status()
            success_package = map_instance.get_package()
            
            if success_car1 and success_car2 and success_package:
                PACKAGE_LIST = map_instance.map_packages 
                if PACKAGE_LIST is not None: 
                # Sort packages by distance to car_1 and car_2
                    if car_1.position_mm is not None and car_2.position_mm is not None:
                        # Check if positions are valid iterables (lists/tuples with 2+ elements)
                        if (hasattr(car_1.position_mm, '__len__') and len(car_1.position_mm) >= 2 and
                            hasattr(car_2.position_mm, '__len__') and len(car_2.position_mm) >= 2):

                            sorted_for_car_1 = sorted((pkg for pkg in PACKAGE_LIST.values() if pkg['status'] == 0 and pkg['ownedBy'] == 0),
                                                    key=lambda pkg: math.dist(car_1.position_mm, pkg['position_start']))
                            sorted_for_car_2 = sorted((pkg for pkg in PACKAGE_LIST.values() if pkg['status'] == 0 and pkg['ownedBy'] == 0),
                                                    key=lambda pkg: math.dist(car_2.position_mm, pkg['position_start']))

                            CAR_1_PACKAGE = [pkg['id'] for pkg in sorted_for_car_1]
                            CAR_2_PACKAGE = [pkg['id'] for pkg in sorted_for_car_2]
                            # logging.info(PACKAGE_LIST)
                            car_1.update_package_list(CAR_1_PACKAGE)
                            car_2.update_package_list(CAR_2_PACKAGE)
                            if CAR_1_PACKAGE is not None and CAR_2_PACKAGE is not None:
                                packages_ready_event.set()  # Signal that packages are ready
                        else:
                            logging.info("Car positions are not valid coordinate pairs...")
                else:
                    logging.info("Waiting for both cars to have valid positions...")
            else:
                logging.info("Failed to update package list")
        except Exception as e:
            logging.error(f"Error in Update_Map_Packages thread: {e}")
        
        time.sleep(TASK_CYCLE)

def car_thread_function(map_instance, car, another_car):
    # Wait for packages to be ready before starting
    logging.info(f"Car {car.car_id} waiting for packages to be ready...")
    packages_ready_event.wait()
    time.sleep(car.cycle_time)  # Wait
    logging.info(f"Car {car.car_id} starting - packages are ready!")
    car.get_target_package(another_car.target_package_id)
    car.old_position = car.position_mm
    while True:
        try:     
            if car.target_package_id is not None:
                PACKAGE_START   = map_instance.map_packages[str(car.target_package_id)]['position_start']
                PACKAGE_END     = map_instance.map_packages[str(car.target_package_id)]['position_end']
                PACKAGE_STATUS  = int(map_instance.map_packages[str(car.target_package_id)]['status'])
                PACKAGE_OWNER   = int(map_instance.map_packages[str(car.target_package_id)]['ownedBy'])
                success = car.update_status()
                if success and car.control_command == 'STOP':
                    # If car is idle or has delivered the package, get a new target package
                    if car.delivery_status == DeliveryStatus.IDLE:
                        # Update delivery status if route update was successful
                        if car.update_root(map_instance, PACKAGE_START):
                            car.delivery_status = DeliveryStatus.PICKING_UP
                            logging.info(f"Car {car.car_id} started route to pick up package {car.target_package_id}")
                            continue
                        else:
                            # Handle failed route update
                            logging.warning(f"Car {car.car_id} failed to update route to package {car.target_package_id}")
                            car.target_package_id = None  # Reset target if routing fails
                            continue
                    
                    # If car is picking up the package and has arrived at the pick-up location
                    elif car.delivery_status == DeliveryStatus.PICKING_UP:
                        if PACKAGE_OWNER == car.car_id:
                            # Update delivery status if route update was successful
                            if car.update_root(map_instance, PACKAGE_END):
                                car.delivery_status = DeliveryStatus.DELIVERING
                                continue
                        else:
                            # If the package is not owned by this car, reset target and status
                            car.delivery_status = DeliveryStatus.IDLE
                            car.target_package_id = None
                            logging.info(f"Car {car.car_id} lost ownership of package {car.target_package_id}, resetting target.")
                            continue

                    # If car is delivering the package and has arrived at the delivery location        
                    elif car.delivery_status == DeliveryStatus.DELIVERING:
                        if PACKAGE_STATUS == 2:
                            # Package has been delivered
                            car.delivery_status = DeliveryStatus.IDLE
                            car.target_package_id = None
                            continue
                    
                    # Check if car is stuck
                    if car.Im_Stuck(map_instance):
                        logging.info(f"Car {car.car_id} seems to be stuck. Re-evaluating target package.")

                    car.old_position = car.position_mm    
    
                else:
                    if car.delivery_status == DeliveryStatus.PICKING_UP or car.delivery_status == DeliveryStatus.DELIVERING:
                        if ((PACKAGE_STATUS == 1 or PACKAGE_STATUS == 2) and PACKAGE_OWNER != car.car_id):
                            # Package has been delivered
                            car.delivery_status = DeliveryStatus.IDLE
                            car.get_target_package(another_car.target_package_id)         
            else:
                # Get next target package avoiding conflict with another car
                car.get_target_package(another_car.target_package_id)            

        except Exception as e:
            logging.error(f"Error in car {car.car_id} thread: {e} with car {car.delivery_status}")
        
        time.sleep(car.cycle_time)  # Wait before next cycle

if __name__ == "__main__":
    
    # Initialize map
    map_instance = Map('localhost',8080,userName,password)
    # Load map information with error handling
    if map_instance.map_info() and map_instance.get_package():
        logging.info("Map loaded successfully!")
        logging.info(f"Graph has {len(map_instance.map_graph.nodes)} nodes")
        logging.info(f"Graph has {len(map_instance.map_graph.edges)} edges")
        logging.info(f"Found {len(map_instance.map_packages)} packages")
    else:
        logging.error("Failed to load map. Cannot proceed with navigation.")
        exit(1)
    logging.info(map_instance.map_graph)
    # Create car instances    
    car_1 = Car(Car_1_ID, map_instance.client)
    car_2 = Car(Car_2_ID, map_instance.client)  

    # Create threads for each process
    package_thread   = threading.Thread(target=Update_Map_Packages, args=(map_instance,car_1,car_2), daemon=True)
    car_1_thread     = threading.Thread(target=car_thread_function, args=(map_instance,car_1,car_2), daemon=True)
    car_2_thread     = threading.Thread(target=car_thread_function, args=(map_instance,car_2,car_1), daemon=True)
    gui_thread       = threading.Thread(target=gui_thread_function, args=(car_1, car_2), daemon=True)
    
    # Start package thread first
    package_thread.start()
    
    # Start car threads (they will wait for packages to be ready)
    car_1_thread.start()
    car_2_thread.start()
    gui_thread.start()
    
    # Keep main thread alive to let daemon threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping threads...")
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

                            sorted_for_car_1 = sorted((pkg for pkg in PACKAGE_LIST.values() if pkg['status'] == 0),
                                                    key=lambda pkg: math.dist(car_1.position_mm, pkg['position_start']))
                            sorted_for_car_2 = sorted((pkg for pkg in PACKAGE_LIST.values() if pkg['status'] == 0),
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
                if car.update_status() and car.control_command == 'STOP':
                    # If car is idle or has delivered the package, get a new target package
                    if car.delivery_status == DeliveryStatus.IDLE:
                        # Plan route to pick up the target package
                        car.route = map_instance.get_root(car.position_mm, map_instance.map_packages[str(car.target_package_id)]['position_start']) if car.target_package_id else []
                        success   = map_instance.client.update_car_route(car.car_id, car.route, userName, password, timeout=5.0)

                        # Update delivery status if route update was successful
                        if success:
                            car.delivery_status = DeliveryStatus.PICKING_UP
                    
                    # If car is picking up the package and has arrived at the pick-up location
                    elif car.delivery_status == DeliveryStatus.PICKING_UP:
                        # print(map_instance.map_packages[str(car.target_package_id)]['ownedBy'])
                        if int(map_instance.map_packages[str(car.target_package_id)]['ownedBy']) == car.car_id:
                            # Plan route to deliver the package
                            car.route = map_instance.get_root(car.position_mm, map_instance.map_packages[str(car.target_package_id)]['position_end'])
                            success = map_instance.client.update_car_route(car.car_id, car.route, userName, password, timeout=5.0)

                            # Update delivery status if route update was successful
                            if success:
                                car.delivery_status = DeliveryStatus.DELIVERING
                        else:
                            # If the package is not owned by this car, reset target and status
                            car.delivery_status = DeliveryStatus.IDLE
                            car.get_target_package(another_car.target_package_id)
                            logging.info(f"Car {car.car_id} lost ownership of package {car.target_package_id}, resetting target.")

                    # If car is delivering the package and has arrived at the delivery location        
                    elif car.delivery_status == DeliveryStatus.DELIVERING:
                        PACKAGE_STATUS = int(map_instance.map_packages[str(car.target_package_id)]['status'])
                        print(PACKAGE_STATUS)
                        if PACKAGE_STATUS == 2:
                            # Package has been delivered
                            car.delivery_status = DeliveryStatus.IDLE
                            car.get_target_package(another_car.target_package_id)
                    
                    # Check if car is stuck
                    if car.Im_Stuck(map_instance):
                        logging.info(f"Car {car.car_id} seems to be stuck. Re-evaluating target package.")

                    # car.old_position = car.position_mm    
    
                else:
                    if car.delivery_status == DeliveryStatus.PICKING_UP or car.delivery_status == DeliveryStatus.DELIVERING:
                        if ((map_instance.map_packages[str(car.target_package_id)]['status'] == 1 or 
                             map_instance.map_packages[str(car.target_package_id)]['status'] == 2) and 
                             int(map_instance.map_packages[str(car.target_package_id)]['ownedBy']) != car.car_id):
                            # Package has been delivered
                            car.delivery_status = DeliveryStatus.IDLE
                            car.get_target_package(another_car.target_package_id)         
            else:
                # Get next target package avoiding conflict with another car
                car.get_target_package(another_car.target_package_id)            

        except Exception as e:
            logging.error(f"Error in car {car.car_id} thread: {e}")
        
        time.sleep(car.cycle_time)  # Wait before next cycle

if __name__ == "__main__":
    
    # Initialize map
    map_instance = Map()
    # Load map information with error handling
    if map_instance.map_info() and map_instance.get_package():
        logging.info("Map loaded successfully!")
        logging.info(f"Graph has {len(map_instance.map_graph.nodes)} nodes")
        logging.info(f"Graph has {len(map_instance.map_graph.edges)} edges")
        logging.info(f"Found {len(map_instance.map_packages)} packages")
    else:
        logging.error("Failed to load map. Cannot proceed with navigation.")
        exit(1)

    # Create car instances    
    car_1 = Car(Car_1_ID, map_instance.client)
    car_2 = Car(Car_2_ID, map_instance.client)  

    # Create threads for each process
    package_thread   = threading.Thread(target=Update_Map_Packages, args=(map_instance,car_1,car_2), daemon=True)
    car_1_thread     = threading.Thread(target=car_thread_function, args=(map_instance,car_1,car_2), daemon=True)
    car_2_thread     = threading.Thread(target=car_thread_function, args=(map_instance,car_2,car_1), daemon=True)
    
    # Start package thread first
    package_thread.start()
    
    # Start car threads (they will wait for packages to be ready)
    car_1_thread.start()
    car_2_thread.start()
    
    # Keep main thread alive to let daemon threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping threads...")
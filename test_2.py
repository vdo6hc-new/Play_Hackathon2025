import time
import sys
import os
import threading
import numpy as np
from indoor_localization.clientApi import LocalizationAPIClient
import math
import matplotlib.pyplot as plt
import networkx as nx

import tkinter as tk
from tkinter import ttk

class Car:
    def __init__(self, car_id, client, streets, points, map_graph):
        self.car_id = car_id
        self.client = client
        self.streets = streets
        self.points = points
        self.map_graph = map_graph
        self.target_package_id = None
        self.status = None
        self.position = None
        self.package_list = []
        
    def update_package_list(self, sorted_packages):
        """Update the car's assigned package list"""
        self.package_list = sorted_packages
        
    def get_target_package(self, other_car_target=None):
        """Get the next target package, avoiding conflicts with other car"""
        if len(self.package_list) > 0:
            target = self.package_list[0]
            # Avoid conflict with other car
            if other_car_target == target and len(self.package_list) > 1:
                target = self.package_list[1]
            elif other_car_target == target:
                target = None
            self.target_package_id = target
        else:
            self.target_package_id = None
        return self.target_package_id
    
    def update_status(self):
        """Update car status from server"""
        try:
            self.status = self.client.get_car_state(self.car_id, timeout=1)
            if self.status:
                self.position = self.status.position_mm
                return True
        except Exception as e:
            print(f"Error getting state for Car {self.car_id}: {e}")
        return False
    
    def send_route_to_package(self, package_list, target_type='pickup'):
        """Send route to pick up or deliver a package"""
        global userName, password
        
        if self.target_package_id is None or self.status is None:
            return False
            
        try:
            start = self.status.position_mm
            
            if target_type == 'pickup':
                end = package_list[self.target_package_id]['position_start']
                action = "pick up"
            else:  # delivery
                end = package_list[self.target_package_id]['position_end']
                action = "deliver"
            
            route = nx.shortest_path(self.map_graph, tuple(start), tuple(end), weight='weight')
            success = self.client.update_car_route(self.car_id, route, userName, password, timeout=5.0)
            
            if success:
                print(f"✓ Route update successful for Car {self.car_id} to {action} Package {self.target_package_id}!")
            
            return success
            
        except Exception as e:
            print(f"Error sending route for Car {self.car_id}: {e}")
            return False
    
    def run_control_loop(self, package_list, other_car):
        """Main control loop for the car"""
        if not self.update_status():
            return
            
        if self.status.control_command == 'STOP':
            if self.target_package_id is None:
                # Get new target package
                other_target = other_car.target_package_id if other_car else None
                self.get_target_package(other_target)
                print(f"Car {self.car_id} status: {self.status}")
                
                if self.target_package_id is not None:
                    self.send_route_to_package(package_list, 'pickup')
            else:
                # Check if we own the package (picked it up)
                if (self.target_package_id in package_list and 
                    package_list[self.target_package_id]['ownedBy'] == self.car_id):
                    self.send_route_to_package(package_list, 'delivery')

def car_thread_function(car, package_list_ref, other_car):
    """Thread function for car control"""
    # Add small offset to avoid simultaneous API calls
    initial_delay = 0.2 if car.car_id == Car_1_ID else 0.4
    time.sleep(initial_delay)
    
    while True:
        try:
            car.run_control_loop(package_list_ref[0], other_car)
        except Exception as e:
            print(f"Error in car {car.car_id} thread: {e}")
        
        time.sleep(0.5)  # Wait 0.5 seconds before next cycle

# ...existing code...

if __name__ == "__main__":
    # Create a client instance
    client = LocalizationAPIClient(server_host='localhost', server_port=8080)
    Init_Server(client)
    success, linestrings, intersections = client.get_road_information()
    if success:
        print("✓ Get MAP information successful!")
        Map = nx.Graph()
        for line in linestrings:
            s, e = tuple(line["start"]), tuple(line["end"])
            dist = math.dist(s, e)
            Map.add_edge(s, e, weight=dist)
    else:
        print("Get MAP information failed!")

    # Create Car instances
    car_1 = Car(Car_1_ID, client, linestrings, intersections, Map)
    car_2 = Car(Car_2_ID, client, linestrings, intersections, Map)
    
    # Package list reference for threads
    package_list_ref = [{}]  # Use list to make it mutable for threads

    def updated_get_package_list_thread(client, car_1, car_2, package_list_ref):
        """Updated thread function to work with Car class"""
        while True:
            try:
                success, temp_package_list = client.get_package_list()
                if success:
                    car_1_status = client.get_car_state(car_1.car_id, timeout=5)
                    car_2_status = client.get_car_state(car_2.car_id, timeout=5)
                    package_list_ref[0] = temp_package_list
                    
                    # Sort packages by distance for each car
                    available_packages = [pkg for pkg in temp_package_list.values() if pkg['status'] == 0]
                    
                    car_1_sorted = sorted(available_packages, 
                                        key=lambda pkg: math.dist(car_1_status.position_mm, pkg['position_start']))
                    car_2_sorted = sorted(available_packages, 
                                        key=lambda pkg: math.dist(car_2_status.position_mm, pkg['position_start']))
                    
                    # Update car package lists
                    car_1.update_package_list([pkg['id'] for pkg in car_1_sorted])
                    car_2.update_package_list([pkg['id'] for pkg in car_2_sorted])

                else:
                    print("Failed to get package list")
            except Exception as e:
                print(f"Error getting package list: {e}")

            time.sleep(PACKAGE_CYCLE)

    # Start threads
    package_thread = threading.Thread(target=updated_get_package_list_thread, 
                                     args=(client, car_1, car_2, package_list_ref), daemon=True)
    car_1_thread = threading.Thread(target=car_thread_function, 
                                   args=(car_1, package_list_ref, car_2), daemon=True)
    car_2_thread = threading.Thread(target=car_thread_function, 
                                   args=(car_2, package_list_ref, car_1), daemon=True)

    car_1_thread.start()
    car_2_thread.start()
    package_thread.start()
    
    # Keep main thread alive to let daemon threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping threads...")
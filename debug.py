import time
import sys
import os
import threading
import math
import networkx as nx
import tkinter as tk
from Player_API.Car import Car
from Player_API.Map import Map

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
            car_1.update_status()
            car_2.update_status()
            success = map_instance.get_package()
            
            if success:
                PACKAGE_LIST = map_instance.map_packages   
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
                        
                        car_1.update_package_list(CAR_1_PACKAGE)
                        car_2.update_package_list(CAR_2_PACKAGE)
                        if CAR_1_PACKAGE is not None and CAR_2_PACKAGE is not None:
                            packages_ready_event.set()  # Signal that packages are ready
                    else:
                        print("Car positions are not valid coordinate pairs...")
                else:
                    print("Waiting for both cars to have valid positions...")
            else:
                print("Failed to update package list")
        except Exception as e:
            print(f"Error in Update_Map_Packages thread: {e}")
        
        time.sleep(TASK_CYCLE)

def car_thread_function(map_instance, car, another_car):
    # Wait for packages to be ready before starting
    print(f"Car {car.car_id} waiting for packages to be ready...")
    packages_ready_event.wait()
    time.sleep(car.cycle_time)  # Wait
    print(f"Car {car.car_id} starting - packages are ready!")
    car.get_target_package(another_car.target_package_id) 
    
    while True:
        try:
            if car.target_package_id is not None:
                if car.update_status() and car.control_command == 'STOP':
                    print(f"Car {car.car_id} cycle time {car.cycle_time}s - Position: {car.position_mm}, Command: {car.control_command}, Target Package: {car.target_package_id}")
                    print(f"Car {car.car_id} assigned packages: {car.package_list}")
                    print(map_instance.map_packages[str(car.target_package_id)]['position_start'])
                    car.route = map_instance.get_root(car.position_mm, map_instance.map_packages[str(car.target_package_id)]['position_start']) if car.target_package_id else []
                    success = map_instance.client.update_car_route(car.car_id, car.route, userName, password, timeout=5.0)
                    if success:
                        print(f"✓ Route update successful for Car {car.car_id} to pick up Package {car.target_package_id} with {car.route} !")
            else:
                car.get_target_package(another_car.target_package_id)            

        except Exception as e:
            print(f"Error in car {car.car_id} thread: {e}")
        
        time.sleep(car.cycle_time)  # Wait before next cycle


class MapViewer(tk.Tk):
    def __init__(self, map_graph):
        super().__init__()
        self.title("Map Graph Viewer")
        self.geometry("900x700")

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.scale = 0.3  # shrink coordinates to fit canvas
        self.draw_graph(map_graph)

    def draw_graph(self, G):
        # Draw edges
        for u, v, data in G.edges(data=True):
            x1, y1 = u[0] * self.scale, u[1] * self.scale
            x2, y2 = v[0] * self.scale, v[1] * self.scale
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
            # Label weight
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            weight = f"{data.get('weight', 0):.1f}"
            self.canvas.create_text(mid_x, mid_y, text=weight, fill="gray")

        # Draw nodes
        for idx, (x, y) in enumerate(G.nodes()):
            x_scaled, y_scaled = x * self.scale, y * self.scale
            r = 5
            self.canvas.create_oval(x_scaled-r, y_scaled-r, x_scaled+r, y_scaled+r, fill="red")
            self.canvas.create_text(x_scaled+10, y_scaled, text=f"N{idx}", anchor="w", fill="blue")


if __name__ == "__main__":
    
    # Initialize map
    map_instance = Map()
    # Load map information with error handling
    if map_instance.map_info() and map_instance.get_package():
        print("Map loaded successfully!")
        print(f"Graph has {len(map_instance.map_graph.nodes)} nodes")
        print(f"Graph has {len(map_instance.map_graph.edges)} edges")
        print(f"Found {len(map_instance.map_packages)} packages")
    else:
        print("Failed to load map. Cannot proceed with navigation.")
        exit(1)
    app = MapViewer(map_instance.map_graph)
    app.mainloop()
    # Create car instances    
    car_1 = Car(Car_1_ID, map_instance.client)
    car_2 = Car(Car_2_ID, map_instance.client)  

    # Create threads for each process
    package_thread   = threading.Thread(target=Update_Map_Packages, args=(map_instance,car_1,car_2), daemon=True)
    # car_1_thread     = threading.Thread(target=car_thread_function, args=(map_instance,car_1,car_2), daemon=True)
    car_2_thread     = threading.Thread(target=car_thread_function, args=(map_instance,car_2,car_1), daemon=True)
    
    # Start package thread first
    package_thread.start()
    
    # Start car threads (they will wait for packages to be ready)
    # car_1_thread.start()
    car_2_thread.start()
    
    # Keep main thread alive to let daemon threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping threads...")
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

####################################
# INPUT YOUR TEAM INFORMATION HERE #
userName = "TeamA" # Your team name
password = "123456789" # Your team password
Car_1_ID = 10 # Could be 10, or 12
Car_2_ID = 11 # Could be 11, or 13
####################################

# GLOBAL VARIABLES
PACKAGE_CYCLE   = 2 # seconds
PACKAGE_LIST    = []
ENABLE_DEBUG    = True
CAR_1_PACKAGE   = None
CAR_2_PACKAGE   = None

# Add GUI variables
gui_root = None
package_tree = None
gui_thread = None

def create_package_gui():
    """Create GUI window to display package list"""
    global gui_root, package_tree
    
    gui_root = tk.Tk()
    gui_root.title("Package List Monitor")
    gui_root.geometry("1000x600")
    
    # Create main frame
    main_frame = ttk.Frame(gui_root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Title label
    title_label = ttk.Label(main_frame, text="Package List Status", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 10))
    
    # Create treeview for package data (NO SCROLLBAR)
    columns = ("ID", "Start Position", "End Position", "Points", "Owner", "Status")
    package_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
    
    # Configure column headings
    for col in columns:
        package_tree.heading(col, text=col)
        package_tree.column(col, width=150, anchor=tk.CENTER)
    
    # Pack treeview WITHOUT scrollbar
    package_tree.pack(fill=tk.BOTH, expand=True)
    
    # Add status labels for cars and packages
    status_frame = ttk.Frame(gui_root)
    status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    status_label = ttk.Label(status_frame, text="Status: Monitoring packages...", font=("Arial", 10))
    status_label.pack(side=tk.LEFT)
    
    # Update GUI initially
    update_package_gui()
    
    # Start GUI main loop
    gui_root.mainloop()

def update_package_gui():
    """Update GUI with current package list"""
    global gui_root, package_tree, PACKAGE_LIST
    
    if gui_root and package_tree and PACKAGE_LIST:
        # Clear existing items
        for item in package_tree.get_children():
            package_tree.delete(item)
        
        # Add package data
        for package_id, package_data in PACKAGE_LIST.items():
            start_pos = f"({package_data['position_start'][0]:.0f}, {package_data['position_start'][1]:.0f})"
            end_pos = f"({package_data['position_end'][0]:.0f}, {package_data['position_end'][1]:.0f})"
            
            # Status mapping
            status_map = {0: "Available", 1: "Picked Up", 2: "Delivered"}
            status_text = status_map.get(package_data['status'], "Unknown")
            
            # Owner mapping
            owner_text = "None" if package_data['ownedBy'] == 0 else f"Car {package_data['ownedBy']}"
            
            # Add color coding based on status
            item = package_tree.insert("", tk.END, values=(
                package_data['id'],
                start_pos,
                end_pos,
                package_data['point'],
                owner_text,
                status_text
            ))
            
            # Color coding
            if package_data['status'] == 0:  # Available
                package_tree.set(item, "Status", "🟢 Available")
            elif package_data['status'] == 1:  # Picked up
                package_tree.set(item, "Status", "🟡 Picked Up")
            elif package_data['status'] == 2:  # Delivered
                package_tree.set(item, "Status", "🔴 Delivered")
    
    # Schedule next update
    if gui_root:
        gui_root.after(1000, update_package_gui)  # Update every 1 second

def start_gui_thread():
    """Start GUI in a separate thread"""
    global gui_thread
    gui_thread = threading.Thread(target=create_package_gui, daemon=True)
    gui_thread.start()

#TODO


def Car_1_Job():
    print("Car 1 Job")

def Car_2_Job():
    print("Car 1 Job")

def Car_Thread(client, CAR_ID, STREETS, POINTS):
    global PACKAGE_LIST
    """Thread function to get car state continuously every 0.5 seconds"""
    # Add small offset to avoid simultaneous API calls
    initial_delay = 0.1 if CAR_ID == Car_1_ID else 0.3
    time.sleep(initial_delay)
    while True:
        try:
            CAR_STATUS = client.get_car_state(CAR_ID, timeout=5)
            if CAR_STATUS:
                print(f"Car {CAR_ID} State: Pos({CAR_STATUS.position_mm}")

            else:
                print(f"Failed to get state for Car {CAR_ID}")
        except Exception as e:
            print(f"Error getting state for Car {CAR_ID}: {e}")
        
        time.sleep(0.5)  # Wait 0.5 seconds before next cycle

def get_package_list_thread(client):
    """Thread function to get package list continuously every 2 seconds"""
    global PACKAGE_LIST
    while True:
        try:
            success, temp_package_list = client.get_package_list()
            if success:
                PACKAGE_LIST = temp_package_list
                # print(f"Package List: {PACKAGE_LIST}")
            else:
                print("Failed to get package list")
        except Exception as e:
            print(f"Error getting package list: {e}")
        
        time.sleep(PACKAGE_CYCLE)  # Wait 2 seconds before next cycle

def Init_Server(client):
    """Initialize and start the localization server"""
    print("=== Initializing Localization Server ===")
    
    # Try to connect to the server
    print("Attempting to connect to the localization server...")
    if not client.connect():
        print("Failed to connect to the server. Make sure the server is running.")
        print("You can start the server by running the localization system.")
        return
    
    print("✓ Successfully connected to the server!")
    
    # Test health check first
    print("\n=== Health Check ===")
    health = client.health_check()
    if health:
        print(f"Server Status: {health['status']}")
        print(f"Active Cars: {health['active_cars']}")
        print(f"Timestamp: {time.ctime(health['timestamp'])}")
    else:
        print("Health check failed")

if __name__ == "__main__":
    # Create a client instance
    client = LocalizationAPIClient(server_host='localhost', server_port=8080)
    Init_Server(client)
    # Get initial car states and map information
    car_1_state = client.get_car_state(Car_1_ID, timeout=5)
    car_2_state = client.get_car_state(Car_2_ID, timeout=5)
    success, streets, points = client.get_road_information()
    if success:
        print("✓ Get MAP information successful!")
    else:
        print("Get MAP information failed!")

    # Start GUI thread first
    start_gui_thread()
    time.sleep(1)  # Give GUI time to initialize

    package_thread = threading.Thread(target=get_package_list_thread, args=(client,), daemon=True)
    Can_1_Thread = threading.Thread(target=Car_Thread, args=(client,Car_1_ID,streets, points), daemon=True)
    Can_2_Thread = threading.Thread(target=Car_Thread, args=(client,Car_2_ID,streets, points), daemon=True)

    Can_1_Thread.start()
    Can_2_Thread.start()
    package_thread.start()
    
    # Keep main thread alive to let daemon threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping threads...")
        if gui_root:
            gui_root.quit()

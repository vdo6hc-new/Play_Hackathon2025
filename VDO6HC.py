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
PACKAGE_CYCLE       = 0.5 # seconds
PACKAGE_LIST        = []
CAR_1_PACKAGE       = []
CAR_2_PACKAGE       = []
CAR_TARGET_PACKAGE  = {Car_1_ID: None, Car_2_ID: None}





def Get_Target_Package(CAR_ID):
    global CAR_1_PACKAGE,CAR_2_PACKAGE,CAR_TARGET_PACKAGE             
    target_package_id = None
    if CAR_ID == Car_1_ID and len(CAR_1_PACKAGE) > 0:
        target_package_id = CAR_1_PACKAGE[0]
        if CAR_TARGET_PACKAGE[Car_2_ID] == target_package_id:
            if len(CAR_1_PACKAGE) > 1:
                target_package_id = CAR_1_PACKAGE[1]
            else:
                CAR_TARGET_PACKAGE[Car_1_ID] = None
    elif CAR_ID == Car_2_ID and len(CAR_2_PACKAGE) > 0:
        target_package_id = CAR_2_PACKAGE[0]
        if CAR_TARGET_PACKAGE[Car_1_ID] == target_package_id:
            if len(CAR_2_PACKAGE) > 1:
                target_package_id = CAR_2_PACKAGE[1]
            else:
                CAR_TARGET_PACKAGE[Car_2_ID] = None
    else:
        CAR_TARGET_PACKAGE[CAR_ID] = None
    CAR_TARGET_PACKAGE[CAR_ID] = target_package_id
def Car_1_Thread(client, CAR_ID, STREETS, POINTS, MAP):
    global PACKAGE_LIST,CAR_1_PACKAGE,CAR_2_PACKAGE
    """Thread function to get car state continuously every 0.5 seconds"""
    Start_Car_1 = []
    End_Car_1   = []
    Route       = []

def Car_Thread(client, CAR_ID, STREETS, POINTS, MAP):
    global PACKAGE_LIST,CAR_1_PACKAGE,CAR_2_PACKAGE
    """Thread function to get car state continuously every 0.5 seconds"""
    # Add small offset to avoid simultaneous API calls
    initial_delay = 0.2 if CAR_ID == Car_1_ID else 0.4
    time.sleep(initial_delay)
    Start       = []
    End         = []
    Route       = []
    CAR_STATUS  = None
    while True:
        try:
            CAR_STATUS = client.get_car_state(CAR_ID, timeout=1)
            if CAR_STATUS:              
                if CAR_STATUS.control_command == 'STOP':
                    if CAR_TARGET_PACKAGE[CAR_STATUS.id] is None:
                        Get_Target_Package(CAR_ID)
                        print(CAR_STATUS)
                        # print(PACKAGE_LIST[CAR_TARGET_PACKAGE[CAR_STATUS.id]]['position_start'])
                        if CAR_TARGET_PACKAGE[CAR_STATUS.id] is not None:
                            # Start = CAR_STATUS.position_mm
                            # print(Start)
                            # End = PACKAGE_LIST[CAR_TARGET_PACKAGE[CAR_STATUS.id]]['position_start']
                            # Route = nx.shortest_path(MAP, tuple(Start), tuple(End), weight='weight')
                            # success = client.update_car_route(CAR_ID, Route, userName, password, timeout=5.0)
                            if success:
                                print(f"✓ Route update successful for Car {CAR_ID} to pick up Package {CAR_TARGET_PACKAGE[CAR_STATUS.id]}!")
                    else:
                        if PACKAGE_LIST[CAR_TARGET_PACKAGE[CAR_STATUS.id]]['ownedBy'] == CAR_STATUS.id:
                            Start = CAR_STATUS.position_mm
                            # End = PACKAGE_LIST[CAR_TARGET_PACKAGE[CAR_STATUS.id]]['position_end']
                            # Route = nx.shortest_path(MAP, tuple(Start), tuple(End), weight='weight')
                            # success = client.update_car_route(CAR_ID, Route, userName, password, timeout=5.0)
                            if success:
                                print(f"✓ Route update successful for Car {CAR_ID} to pick up Package {CAR_TARGET_PACKAGE[CAR_STATUS.id]}!")
            else:
                print(f"Failed to get state for Car {CAR_ID}")
        except Exception as e:
            print(f"Error getting state for Car {CAR_ID}: {e}")
        
        time.sleep(0.5)  # Wait 0.5 seconds before next cycle

def get_package_list_thread(client,CAR_1_ID,CAR_2_ID):
    """Thread function to get package list continuously every 2 seconds"""
    global PACKAGE_LIST,CAR_1_PACKAGE,CAR_2_PACKAGE
    while True:
        try:
            success, temp_package_list = client.get_package_list()
            if success:
                CAR_1_STATUS = client.get_car_state(CAR_1_ID, timeout=5)
                CAR_2_STATUS = client.get_car_state(CAR_2_ID, timeout=5)
                PACKAGE_LIST = temp_package_list
                
                sorted_by_point     = sorted((pkg for pkg in PACKAGE_LIST.values() if pkg['status'] == 0),key=lambda pkg: math.dist(CAR_2_STATUS.position_mm, pkg['position_start']))
                sorted_by_distance  = sorted((pkg for pkg in PACKAGE_LIST.values() if pkg['status'] == 0),key=lambda pkg: math.dist(CAR_1_STATUS.position_mm, pkg['position_start']))
                CAR_1_PACKAGE       = [pkg['id'] for pkg in sorted_by_distance]
                CAR_2_PACKAGE       = [pkg['id'] for pkg in sorted_by_point]

            else:
                print("Failed to get package list")
        except Exception as e:
            print(f"Error getting package list: {e}")

        time.sleep(PACKAGE_CYCLE)  # Wait before next cycle

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

    package_thread = threading.Thread(target=get_package_list_thread, args=(client,Car_1_ID,Car_2_ID), daemon=True)
    Can_1_Thread = threading.Thread(target=Car_Thread, args=(client,Car_1_ID,linestrings, intersections,Map), daemon=True)
    Can_2_Thread = threading.Thread(target=Car_Thread, args=(client,Car_2_ID,linestrings, intersections,Map), daemon=True)

    Can_1_Thread.start()
    Can_2_Thread.start()
    package_thread.start()
    
    # Keep main thread alive to let daemon threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping threads...")

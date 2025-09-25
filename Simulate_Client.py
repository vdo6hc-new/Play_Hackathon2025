#!/usr/bin/env python3
"""
Simulate Client - Demo script to test the LocalizationAPIClient
"""
import time
import sys
import os
import numpy as np
from indoor_localization.clientApi import LocalizationAPIClient
import math

####################################
# INPUT YOUR TEAM INFORMATION HERE #
userName = "TeamA" # Your team name
password = "123456789" # Your team password
Car_1_ID = 10 # Could be 10, or 12
Car_2_ID = 11 # Could be 11, or 13
####################################

def main():
    """Main function to simulate a client connecting to the API server"""
    print("=== Localization API Client Simulation ===")
    
    # Create a client instance
    client = LocalizationAPIClient(server_host='localhost', server_port=8080)
    
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

    # Continuous monitoring loop
    print(f"\n=== Starting Continuous Monitoring for Car {Car_1_ID} and Car {Car_2_ID}===")
    print("Press Ctrl+C to stop monitoring...")
    
    loop_count = 0
    
    try:
        while True:
            loop_count += 1  
            # Getting Car State every cycle
            try:
                # Check if still connected before making request
                if not client.is_connected:
                    print("⚠ Client disconnected, attempting to reconnect...")
                    if not client.connect():
                        print("✗ Failed to reconnect")
                        continue
                car_1_state = client.get_car_state(Car_1_ID, timeout=5)
                car_2_state = client.get_car_state(Car_2_ID, timeout=5)
            except Exception as e:
                print(f"✗ Error while getting car state: {e}")

            if loop_count % 2 == 0:
                print("Try to get map data")
                success, streets, points = client.get_road_information()
                if success:
                    print("✓ Get MAP information successful!")
            if loop_count % 3 == 0:
                success, Package_List = client.get_package_list()
                if success:
                    print("✓ Get Package List information successful!")
                    for package_id, package in Package_List.items():
                        print(f"---- PACKAGE {package_id} INFORMATION ----")
                        print(f"Point : {package['point']}")
                        print(f"Pick Up Destination : {package['position_start']}")
                        print(f"Delivery Up Destination : {package['position_end']}")
                        print(f"Owned By Car ID : {package['ownedBy']}")
                        print(f"Status : {package['status']}")
                        print(f"---------------------")    
            if loop_count % 4 == 0:
                route_car_1 = []  # Initialize empty route if no path found
                route_car_2 = []  # Initialize empty route if no path found
                success = client.update_car_route(Car_1_ID, route_car_1, userName, password, timeout=5.0)
                success = client.update_car_route(Car_2_ID, route_car_2, userName, password, timeout=5.0)
                if success:
                    print("✓ Route update successful!")
                    # Get updated car state to verify route was set
                    time.sleep(1)  # Give server time to process
                    updated_state = client.get_car_state(Car_2_ID, timeout=5.0)
                    if updated_state and updated_state.route:
                        print(f"✓ Verified: Car now has {len(updated_state.route)} route points")
                        print("New route points:")
                        for i, (x, y) in enumerate(updated_state.route):
                            print(f"  {i+1}: ({x}, {y})")
                    else:
                        print("⚠ Warning: Could not verify route update")
                else:
                    print("✗ Route update failed!")
                
            print(f"\nSleeping for 1 seconds...")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n=== Monitoring stopped by user after {loop_count} loops ===")
    except Exception as e:
        print(f"\n✗ Unexpected error in monitoring loop: {e}")
    
    # Set up real-time callbacks for demonstration
    
    # Disconnect
    client.disconnect()
    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    # Check command line arguments
    main()
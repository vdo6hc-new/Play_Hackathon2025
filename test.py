import time
import sys
import os
import numpy as np
from Player_API.indoor_localization.clientApi import LocalizationAPIClient
import math
import matplotlib.pyplot as plt
import networkx as nx
start = (2064.95507812 , 187.07444763)
end = (1654.0, 190.0)
# Snap start/end to nearest nodes
def nearest_node(point, nodes):
    return min(nodes, key=lambda n: math.dist(n, point))
def map(segments,intersections):
    # Draw map
    plt.figure(figsize=(10, 10))
    for seg in segments :
        x_vals = [seg["start"][0], seg["end"][0]]
        y_vals = [seg["start"][1], seg["end"][1]]
        plt.plot(x_vals, y_vals, "k-", linewidth=2)  # black lines for roads
    # Draw intersections (red dots + labels)
    for idx, node in enumerate(intersections ):
        plt.scatter(node[0], node[1], c="red", s=40, zorder=3)
        plt.text(node[0] + 15, node[1] - 15, str(idx), fontsize=8, color="blue")
    # Formatting
    plt.gca().invert_yaxis()  # optional: flip Y to match screen coords
    plt.axis("equal")
    plt.title("Road Network Map")
    plt.show() 

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


    success_map, segments, intersections = client.get_road_information()
    if success_map:
        print("===========================================================")
        print(segments)
        print("===========================================================")
        print(intersections)
        print("===========================================================")
    else:
        print("error")
    success_package, Package_List = client.get_package_list()
    if success_package:
        print(Package_List)
        print("===========================================================")
        print(Package_List["7"]["ownedBy"])
        print("===========================================================")
    else:
        print("error")   
    
    G = nx.Graph()
    for seg in segments:
        s, e = tuple(seg["start"]), tuple(seg["end"])
        dist = math.dist(s, e)
        G.add_edge(s, e, weight=dist)

    start_node = nearest_node(start, [tuple(i) for i in intersections])
    end_node = nearest_node(end, [tuple(i) for i in intersections]) 
    print("Nearest start node:", start_node)
    print("Nearest end node:", end_node)

    # Shortest path
    path = nx.shortest_path(G, source=start_node, target=end_node, weight="weight")
    print("Route:", path)
    map(segments,intersections)

if __name__ == "__main__":
    # Check command line arguments
    main()
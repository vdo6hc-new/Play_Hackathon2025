from .indoor_localization.clientApi import LocalizationAPIClient
import networkx as nx
import math
import time

class Map:
    def __init__(self, server_host='localhost', server_port=8080):
        self.client = LocalizationAPIClient(server_host=server_host, server_port=server_port)
        self.map_graph      = None
        self.map_packages   = None
        self.linestrings    = None
        self.intersections  = None
        self.initServer()

    def initServer(self):
        """Initialize and start the localization server"""
        print("=== Initializing Localization Server ===")

        # Try to connect to the server
        print("Attempting to connect to the localization server...")
        if not self.client.connect():
            print("Failed to connect to the server. Make sure the server is running.")
            print("You can start the server by running the localization system.")
            return False

        print("✓ Successfully connected to the server!")

        # Test health check first
        print("\n=== Health Check ===")
        health = self.client.health_check()
        if health:
            print(f"Server Status: {health['status']}")
            print(f"Active Cars: {health['active_cars']}")
            print(f"Timestamp: {time.ctime(health['timestamp'])}")
            return True
        else:
            print("Health check failed")
            return False

    def map_info(self):
        """Load map data from the server and create a graph representation"""
        if not self.client:
            print("No client connection available")
            return False
            
        success_map_node, linestrings, intersections = self.client.get_road_information()
        success_package                              = self.get_package()
        self.linestrings = linestrings
        self.intersections = intersections

        if success_map_node and success_package:
            self.map_graph = nx.Graph()
            
            # Add road network edges
            for line in linestrings:
                s, e = tuple(line["start"]), tuple(line["end"])
                dist = math.dist(s, e)
                self.map_graph.add_edge(s, e, weight=dist)
            
            # Add package positions as nodes and connect them to nearest intersections
            if self.map_packages and self.intersections:
                for package_id, package_data in self.map_packages.items():
                    # Get package positions
                    start_pos = tuple(package_data['position_start'])
                    end_pos = tuple(package_data['position_end'])
                    
                    # Add package positions as nodes
                    self.map_graph.add_node(start_pos)
                    self.map_graph.add_node(end_pos)
                    
                    # Connect package positions to nearest intersections
                    nearest_start_intersection = min(self.intersections, key=lambda point: math.dist(start_pos, point))
                    nearest_end_intersection   = min(self.intersections, key=lambda point: math.dist(end_pos, point))
                    
                    # Add edges from package positions to nearest intersections
                    start_dist = math.dist(start_pos, nearest_start_intersection)
                    end_dist = math.dist(end_pos, nearest_end_intersection)
                    
                    self.map_graph.add_edge(start_pos, tuple(nearest_start_intersection), weight=start_dist)
                    self.map_graph.add_edge(end_pos, tuple(nearest_end_intersection), weight=end_dist)
            
            return True
        else:
            print("Get MAP information failed!")
            return False

    def get_package(self):
        """Load package data from the server"""
        if not self.client:
            print("No client connection available")
            return False
            
        success, packages = self.client.get_package_list()
        if success:
            self.map_packages = packages
            return True
        else:
            print("Failed to get package list")
            return False
        
    def get_root(self,start,end):
        route = []
        if self.map_graph and self.intersections:
            start_node = min(self.intersections, key=lambda point: math.dist(start, point))
            end_node = min(self.intersections, key=lambda point: math.dist(end, point))
            try:
                route = nx.shortest_path(self.map_graph, source=tuple(start_node), target=tuple(end_node), weight="weight")
            except nx.NetworkXNoPath:
                print("No path found between the specified points.")
        else:
            print("Map graph or intersections not available.")
        return route
from .indoor_localization.clientApi import LocalizationAPIClient
import networkx as nx
import math
import time

class Map:
    def __init__(self, server_host='localhost', server_port=8080, userName="TeamA", password="123456789"):
        self.client = LocalizationAPIClient(server_host=server_host, server_port=server_port)
        self.userName       = userName
        self.password       = password        
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
        # Check if client connection is available
        if not self.client:
            print("No client connection available")
            return False
            
        # Retrieve road network data from the localization server
        success_map_node, linestrings, intersections = self.client.get_road_information()
        success_map_package                          = self.get_package()
        
        # Store the raw map data as instance variables
        self.linestrings   = linestrings    # Road segments with start/end coordinates
        self.intersections = intersections  # Junction/intersection points
        
        # Process the map data if retrieval was successful
        if success_map_node and success_map_package:
            # Initialize a new undirected graph using NetworkX
            self.map_graph = nx.Graph()
            
            # Build the road network graph by adding edges for each road segment
            for line in linestrings:
                # Extract start and end coordinates as tuples
                s, e = tuple(line["start"]), tuple(line["end"])
                
                # Calculate Euclidean distance between start and end points
                dist = math.dist(s, e)
                
                # Add edge to graph with distance as weight for pathfinding
                self.map_graph.add_edge(s, e, weight=dist)
            
            # Add package positions and create new linestrings
            if self.map_packages and self.linestrings:
                # Get all existing nodes from linestrings
                existing_nodes = set()
                for line in self.linestrings:
                    existing_nodes.add(tuple(line["start"]))
                    existing_nodes.add(tuple(line["end"]))
                
                existing_nodes = list(existing_nodes)
                
                for package_id, package_data in self.map_packages.items():
                    start_pos = tuple(package_data['position_start'])
                    end_pos = tuple(package_data['position_end'])
                    
                    # Find 2 closest existing nodes for start position
                    start_distances = [(node, math.dist(start_pos, node)) for node in existing_nodes]
                    start_distances.sort(key=lambda x: x[1])
                    closest_start_nodes = [start_distances[0][0], start_distances[1][0]]
                    
                    # Find 2 closest existing nodes for end position
                    end_distances = [(node, math.dist(end_pos, node)) for node in existing_nodes]
                    end_distances.sort(key=lambda x: x[1])
                    closest_end_nodes = [end_distances[0][0], end_distances[1][0]]
                    
                    # Create 2 new linestrings for start position
                    for i, closest_node in enumerate(closest_start_nodes):
                        new_linestring_start = {
                            "start": list(start_pos),
                            "end": list(closest_node),
                            "package_id": package_data['id'],
                            "connection_type": f"start_connection_{i+1}"
                        }
                        self.linestrings.append(new_linestring_start)
                        
                        # Add to graph
                        dist = math.dist(start_pos, closest_node)
                        self.map_graph.add_edge(start_pos, closest_node, weight=dist)
                    
                    # Create 2 new linestrings for end position
                    for i, closest_node in enumerate(closest_end_nodes):
                        new_linestring_end = {
                            "start": list(end_pos),
                            "end": list(closest_node),
                            "package_id": package_data['id'],
                            "connection_type": f"end_connection_{i+1}"
                        }
                        self.linestrings.append(new_linestring_end)
                        
                        # Add to graph
                        dist = math.dist(end_pos, closest_node)
                        self.map_graph.add_edge(end_pos, closest_node, weight=dist)
            
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
                if route[-1] != tuple(end):
                    route.append(tuple(end)) 
            except nx.NetworkXNoPath:
                print("No path found between the specified points.")
            # Ensure end_node is at the end of the route
   
        else:
            print("Map graph or intersections not available.")
        return route
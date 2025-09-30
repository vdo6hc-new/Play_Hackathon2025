import time
import math
import random
import heapq
from Player_API.indoor_localization.clientApi import LocalizationAPIClient

"""
Simulate_Client_Fixed_Simple.py

Step-by-step function guide for segment-only car delivery simulation.

Usage:
    1. Call setup_config() to set car IDs, user, password
    2. Call setup_global_state() to initialize global variables
    3. Use helper functions for pathfinding, graph building, collision detection
    4. Call run_main_loop() to start the main control loop
    5. Status is printed every 15 loops
    6. KeyboardInterrupt or error will exit and disconnect
"""


# ===================== 1. CONFIGURATION =====================
def setup_config():
    """Step 1: Set car IDs, user, password."""
    global CAR_IDS, USER, PASSWORD
    CAR_IDS = [10, 11]
    USER = "TeamA"
    PASSWORD = "123456789"

# ===================== 2. GLOBAL STATE =====================
def setup_global_state():
    """Step 2: Prepare all global variables."""
    global Package_Handling, Package_List, streets_cache, points_cache, number_of_blocked
    Package_Handling = {}
    Package_List = {}
    streets_cache = []
    points_cache = []
    number_of_blocked = {}


# ===================== 3. HELPER FUNCTIONS =====================
def nearest_point(pos, points):
    """Step 3a: Find nearest point to pos from points."""
    return min(points, key=lambda p: math.hypot(pos[0] - p[0], pos[1] - p[1]))

def second_nearest_point(pos, points):
    """Step 3b: Find second nearest point to pos from points."""
    sorted_pts = sorted(points, key=lambda p: math.hypot(pos[0] - p[0], pos[1] - p[1]))
    return sorted_pts[1] if len(sorted_pts) > 1 else sorted_pts[0]

def dijkstra(graph, start, end, blocked):
    """Step 3c: Dijkstra pathfinding with optional blocked node."""
    queue = [(0, start, [start])]
    visited = set()
    while queue:
        cost, node, path = heapq.heappop(queue)
        if node == end:
            return path
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph[node]:
            if blocked != [0, 0] and neighbor == blocked:
                continue
            heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
    return None

def build_graph(streets, points):
    """Step 3d: Build graph from street segments and intersection points."""
    valid_points = [tuple(p) for p in points]
    graph = {p: [] for p in valid_points}
    for street in streets:
        s, e = tuple(street["start"]), tuple(street["end"])
        if s in valid_points and e in valid_points:
            length = math.hypot(e[0] - s[0], e[1] - s[1])
            graph[s].append((e, length))
            graph[e].append((s, length))
    return graph, valid_points

def init_car_handling():
    """Step 3e: Initialize car handling state."""
    for car_id in CAR_IDS:
        if car_id not in Package_Handling:
            Package_Handling[car_id] = {
                "PackageState": 0,  # 0=idle, 1=pickup, 2=delivery
                "PackageID": 0,
                "pickUpDestination": (),
                "deliverDestination": (),
                "RouteCalculated": 0,
                "ownedPackage": 0
            }
        if car_id not in number_of_blocked:
            number_of_blocked[car_id] = 0

def choose_nearest_packages(package_list, car_states):
    """Step 3f: Assign nearest available package to each car."""
    # Tối ưu: Ưu tiên package theo hướng di chuyển hiện tại của xe
    for cid in CAR_IDS:
        state = car_states[cid]
        if not state:
            continue
        h = Package_Handling[cid]
        # Nếu xe vừa giao hàng xong, dự đoán vị trí là điểm giao hàng
        if h["PackageState"] == 0 and h["deliverDestination"]:
            predicted_pos = h["deliverDestination"]
            heading = None
        else:
            predicted_pos = (state.position_mm[0], state.position_mm[1])
            # Tính hướng di chuyển hiện tại
            if hasattr(state, "speed_mm_per_s") and state.speed_mm_per_s > 10 and hasattr(state, "route") and state.route:
                # Lấy hướng từ vị trí hiện tại đến điểm tiếp theo trên route
                next_point = state.route[0] if len(state.route) > 0 else None
                if next_point:
                    dx = next_point[0] - predicted_pos[0]
                    dy = next_point[1] - predicted_pos[1]
                    heading = math.atan2(dy, dx)
                else:
                    heading = None
            else:
                heading = None

        best_pkg_id = None
        best_score = float('inf')
        for pkg_id, pkg in package_list.items():
            if pkg["status"] != 0:
                continue
            px, py = pkg["position_start"]
            dist = math.hypot(px - predicted_pos[0], py - predicted_pos[1])
            # Nếu có hướng di chuyển, ưu tiên package phía trước
            if heading is not None:
                dx = px - predicted_pos[0]
                dy = py - predicted_pos[1]
                angle = math.atan2(dy, dx)
                angle_diff = abs((angle - heading + math.pi) % (2*math.pi) - math.pi)
                # Nếu package nằm phía trước (góc lệch < 90 độ), ưu tiên
                if angle_diff < math.pi/2:
                    score = dist * 0.7  # Ưu tiên phía trước
                else:
                    score = dist * 1.5  # Phía sau, giảm ưu tiên
            else:
                score = dist
            if score < best_score:
                best_score = score
                best_pkg_id = pkg_id
        if best_pkg_id is not None:
            if h["PackageState"] == 0 and h["PackageID"] != best_pkg_id:
                h["PackageState"] = 1
                h["PackageID"] = best_pkg_id
                h["pickUpDestination"] = package_list[best_pkg_id]["position_start"]
                h["deliverDestination"] = package_list[best_pkg_id]["position_end"]
                h["RouteCalculated"] = 0
                print(f"Car {cid} chose package {best_pkg_id} (heading-optimized)")

def update_package_states(package_list):
    """Step 3g: Update car/package state based on server status."""
    for pkg_id, pkg in package_list.items():
        for cid in CAR_IDS:
            h = Package_Handling[cid]
            # Picked up
            if pkg["status"] == 1 and pkg["ownedBy"] == cid and h["PackageState"] == 1:
                h["ownedPackage"] = pkg_id
                h["PackageState"] = 2
                h["RouteCalculated"] = 0
                print(f"Car {cid} picked up package {pkg_id}")
            # Lost race
            elif pkg["status"] == 1 and h["PackageID"] == pkg_id and pkg["ownedBy"] != cid:
                print(f"Car {cid} lost package {pkg_id} to car {pkg['ownedBy']}")
                h["ownedPackage"] = 0
                h["PackageState"] = 0
                h["PackageID"] = 0
                h["RouteCalculated"] = 0
                h["pickUpDestination"] = ()
                h["deliverDestination"] = ()
            # Delivered
            elif pkg["status"] == 2 and pkg["ownedBy"] == cid and h.get("ownedPackage") == pkg_id:
                print(f"Car {cid} delivered package {pkg_id}")
                h["ownedPackage"] = 0
                h["PackageState"] = 0
                h["PackageID"] = 0
                h["RouteCalculated"] = 0
                h["pickUpDestination"] = ()
                h["deliverDestination"] = ()
                # Tối ưu: Sau khi trả hàng, gán package mới gần nhất vị trí giao hàng
                predicted_pos = h["deliverDestination"] if h["deliverDestination"] else None
                if predicted_pos:
                    nearest_pkg_id = None
                    nearest_dist = float('inf')
                    for new_pkg_id, new_pkg in package_list.items():
                        if new_pkg["status"] == 0:
                            px, py = new_pkg["position_start"]
                            dist = math.hypot(px - predicted_pos[0], py - predicted_pos[1])
                            if dist < nearest_dist:
                                nearest_dist = dist
                                nearest_pkg_id = new_pkg_id
                    if nearest_pkg_id is not None:
                        h["PackageState"] = 1
                        h["PackageID"] = nearest_pkg_id
                        h["pickUpDestination"] = package_list[nearest_pkg_id]["position_start"]
                        h["deliverDestination"] = package_list[nearest_pkg_id]["position_end"]
                        h["RouteCalculated"] = 0
                        print(f"Car {cid} auto-chose next nearest package {nearest_pkg_id} after delivery (optimized).")

def detect_collision(car_states, threshold=150.0):
    """Step 3h: Return car id to reroute if cars are too close."""
    s1, s2 = car_states[CAR_IDS[0]], car_states[CAR_IDS[1]]
    if not s1 or not s2:
        return None
    dx = s1.position_mm[0] - s2.position_mm[0]
    dy = s1.position_mm[1] - s2.position_mm[1]
    if math.hypot(dx, dy) < threshold:
        return random.choice(CAR_IDS)
    return None

def calculate_and_send_route(car_id, car_state, graph, valid_points, destination, client):
    """Step 3i: Calculate and send route for car."""
    if not car_state or not graph or not destination:
        return False
    Package_Handling[car_id]["RouteCalculated"] = 1
    car_pos = (car_state.position_mm[0], car_state.position_mm[1])
    end_node = nearest_point(destination, valid_points)
    # Blocked handling
    if car_state.control_command == "BLOCKED":
        number_of_blocked[car_id] += 1
    else:
        number_of_blocked[car_id] = 0
    start_node = nearest_point(car_pos, valid_points) if number_of_blocked[car_id] < 2 else second_nearest_point(car_pos, valid_points)
    blocked = car_state.route[1] if car_state.control_command == "BLOCKED" and car_state.route and len(car_state.route) > 1 else [0, 0]
    route = dijkstra(graph, start_node, end_node, blocked)
    route = route + [destination] if route else [destination]
    success = client.update_car_route(car_id, route, USER, PASSWORD, timeout=5.0) if route else False
    if success:
        state_name = "pickup" if Package_Handling[car_id]["PackageState"] == 1 else "delivery"
        print(f"Car {car_id} route updated ({len(route)} points) for {state_name}")
        return True
    print(f"Failed to update route for car {car_id}")
    return False


# ===================== 4. MAIN LOOP =====================
def run_main_loop():
    """Step 4: Main control loop for car delivery."""
    print("=== Localization API Client Simulation ===")
    client = LocalizationAPIClient(server_host='10.185.74.124', server_port=8080)
    print("Attempting to connect to the localization server...")
    if not client.connect():
        print("Failed to connect to the server. Make sure the server is running.")
        return
    print("✓ Successfully connected to the server!")
    print("\n=== Health Check ===")
    health = client.health_check()
    if health:
        print(f"Server Status: {health['status']}")
        print(f"Active Cars: {health['active_cars']}")
        print(f"Timestamp: {time.ctime(health['timestamp'])}")
    else:
        print("Health check failed")
    print(f"\n=== Starting Continuous Monitoring for Cars {CAR_IDS} ===")
    print("Press Ctrl+C to stop monitoring...")
    loop_count = 0
    try:
        while True:
            loop_count += 1
            car_states = {cid: None for cid in CAR_IDS}
            try:
                if not client.is_connected:
                    print("⚠ Client disconnected, attempting to reconnect...")
                    if not client.connect():
                        print("✗ Failed to reconnect")
                        continue
                for cid in CAR_IDS:
                    car_states[cid] = client.get_car_state(cid, timeout=3)
            except Exception as e:
                print(f"✗ Error while getting car state: {e}")
                continue
            # Step 4a: Update map every loop (faster refresh)
            success, streets, points = client.get_road_information()
            if success:
                streets_cache[:] = streets
                points_cache[:] = points
            # Step 4b: Update packages every loop (faster refresh)
            success, Package_List = client.get_package_list()
            if success:
                init_car_handling()
                # Update states and assign nearest packages
                update_package_states(Package_List)
                choose_nearest_packages(Package_List, car_states)
            # Step 4c: Collision detection
            collision_car = detect_collision(car_states)
            if collision_car is not None:
                print(f"⚔ Collision detected - Car {collision_car} will reroute")
                Package_Handling[collision_car]["RouteCalculated"] = 0
            # Step 4d: Calculate routes every loop or on collision
            if streets_cache and points_cache:
                graph, valid_points = build_graph(streets_cache, points_cache)
                for cid in CAR_IDS:
                    h = Package_Handling[cid]
                    state = car_states[cid]
                    # Route recalculation immediately after assignment or pickup
                    if state and (h["RouteCalculated"] == 0 or state.control_command == "BLOCKED" or collision_car == cid):
                        dest = h["pickUpDestination"] if h["PackageState"] == 1 else h["deliverDestination"] if h["PackageState"] == 2 else None
                        if dest:
                            calculate_and_send_route(cid, state, graph, valid_points, dest, client)
            # Step 4e: Status display every 2 loops (rất nhanh)
            if loop_count % 2 == 0:
                status = []
                for cid in CAR_IDS:
                    state = car_states[cid]
                    if state:
                        h = Package_Handling[cid]
                        s = h["PackageState"]
                        speed = state.speed_mm_per_s
                        pos = f"({int(state.position_mm[0])},{int(state.position_mm[1])})"
                        status.append(f"Car{cid}:S{s} {speed:.1f}mm/s {pos}")
                if status:
                    print(" | ".join(status))
            # Giảm thời gian sleep xuống 0.1 giây để xe phản hồi nhanh nhất
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n\n=== Monitoring stopped by user after {loop_count} loops ===")
    except Exception as e:
        print(f"\n✗ Unexpected error in monitoring loop: {e}")
    client.disconnect()
    print("\n=== Simulation Complete ===")

# ===================== 5. ENTRY POINT =====================
def main():
    """Step 5: Entry point - setup and run."""
    setup_config()
    setup_global_state()
    run_main_loop()

if __name__ == "__main__":
    main()
import socketio
import numpy as np
import threading
import time
from typing import Dict, Optional, Callable
from .models import CarState

class LocalizationAPIClient:
    """Socket.IO client to interact with the Localization API server"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8080):
        self.server_host = server_host
        self.server_port = server_port
        self.server_url = f'http://{self.server_host}:{self.server_port}'
        self.sio = socketio.Client()
        self.is_connected = False
        self.response_data = {}
        self.response_event = threading.Event()
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            print("Connected to Localization API server")
            self.is_connected = True
            
        @self.sio.event
        def disconnect():
            print("Disconnected from server")
            self.is_connected = False
            
        @self.sio.event
        def car_data(data):
            """Handle car data response"""
            self.response_data['car_data'] = data
            self.response_event.set()
            
        @self.sio.event
        def route_updated(data):
            """Handle route update response"""
            self.response_data['route_updated'] = data
            self.response_event.set()
        
        @self.sio.event
        def road_information(data):
            """Handle get road information response"""
            self.response_data['road_information'] = data
            self.response_event.set()
        
        @self.sio.event
        def teams_information(data):
            """Handle get teams information response"""
            self.response_data['teams_information'] = data
            self.response_event.set()

        @self.sio.event
        def package_data(data):
            """Handle get road information response"""
            self.response_data['package_data'] = data
            self.response_event.set()
            
        @self.sio.event
        def health_status(data):
            """Handle health check response"""
            self.response_data['health_status'] = data
            self.response_event.set()
            
        @self.sio.event
        def error(data):
            """Handle error response"""
            self.response_data['error'] = data
            self.response_event.set()
                
        @self.sio.event
        def car_updated(data):
            """Handle single car update"""
            if hasattr(self, 'on_car_updated') and self.on_car_updated:
                self.on_car_updated(data)
                
        @self.sio.event
        def car_route_changed(data):
            """Handle route change broadcasts"""
            if hasattr(self, 'on_route_changed') and self.on_route_changed:
                self.on_route_changed(data)
    
    def connect(self) -> bool:
        """Connect to the Socket.IO server"""
        try:
            self.sio.connect(self.server_url)
            # Wait a moment for connection to establish
            time.sleep(0.1)
            return self.is_connected
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.is_connected:
            self.sio.disconnect()
    
    def _wait_for_response(self, timeout: float = 1.0) -> Dict:
        """Wait for a response from the server"""
        self.response_event.clear()
        self.response_data.clear()
        
        if self.response_event.wait(timeout):
            return self.response_data.copy()
        else:
            return {'error': {'message': 'Request timeout'}}
    
    def get_car_state(self, car_id: int, timeout: float = 1.0) -> Optional[CarState]:
        """Get state of a specific car"""
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_car', {'car_id': car_id})
            response = self._wait_for_response(timeout)
            
            if 'car_data' in response:
                data = response['car_data']['data']
                return CarState(
                    id=data['id'],
                    position=np.array(data['position']) if data.get('position') is not None else np.array([0, 0]),
                    position_mm=np.array(data['position_mm']),
                    orientation=data['orientation'],
                    speed_mm_per_s=data['speed_mm_per_s'],
                    obstacles_abs=[(dist, angle) for dist, angle in data['obstacles_abs']],
                    control_command=data['control_command'],
                    desired_angle=data['desired_angle'],
                    route=[(x, y) for x, y in data['route']],
                    timestamp=data['timestamp']
                )
            elif 'error' in response:
                print(f"Error getting car state: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_road_information(self,  timeout: float = 1.0):
        """Get road information"""
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_road_information', {})
            response = self._wait_for_response(timeout)

            
            if 'road_information' in response:
                streets = response['road_information']['streets']
                points = response['road_information']['points']
                success = response['road_information']['success']
                return success, streets, points
            elif 'error' in response:
                print(f"Error getting road information: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_teams_information(self,  timeout: float = 1.0):
        """Get teams information"""
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_teams_information', {})
            response = self._wait_for_response(timeout)
   
            if 'teams_information' in response:
                info = response['teams_information']['info']
                success = response['teams_information']['success']
                return success, info
            elif 'error' in response:
                print(f"Error getting teams information: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_package_list(self, timeout: float = 1.0):
        """Get package list"""
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('get_package_list', {})
            response = self._wait_for_response(timeout)
            
            if 'package_data' in response:
                data = response['package_data']['packages']
                success = response['package_data']['success']
                return success, data
            elif 'error' in response:
                print(f"Error getting package list: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None

    def update_car_route(self, car_id: int, new_route: list, userName: str = '', password: str = '', timeout: float = 1.0) -> bool:
        """Update the route for a specific car"""
        if not self.is_connected:
            print("Not connected to server")
            return False
        
        try:
            self.sio.emit('update_route', {
                'car_id': car_id,
                'route': new_route,
                'userName': userName,
                'pwd': password
            })
            response = self._wait_for_response(timeout)
            
            if 'route_updated' in response:
                print(f"Successfully updated route for car {car_id}")
                return response['route_updated']['success']
            elif 'error' in response:
                print(f"Failed to update route: {response['error']['message']}")
                return False
            else:
                print("No response received")
                return False
                
        except Exception as e:
            print(f"Request error: {e}")
            return False
    
    def health_check(self, timeout: float = 5.0) -> Optional[Dict]:
        """Perform health check"""
        if not self.is_connected:
            print("Not connected to server")
            return None
        
        try:
            self.sio.emit('health_check')
            response = self._wait_for_response(timeout)
            
            if 'health_status' in response:
                return response['health_status']
            elif 'error' in response:
                print(f"Health check error: {response['error']['message']}")
                return None
            else:
                print("No response received")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def set_real_time_callbacks(self, 
                               on_cars_updated: Optional[Callable] = None,
                               on_car_updated: Optional[Callable] = None,
                               on_car_commands_updated: Optional[Callable] = None,
                               on_route_changed: Optional[Callable] = None):
        """Set callbacks for real-time updates"""
        self.on_cars_updated = on_cars_updated
        self.on_car_updated = on_car_updated
        self.on_car_commands_updated = on_car_commands_updated
        self.on_route_changed = on_route_changed

def create_client(server_url: str) -> LocalizationAPIClient:
    """Factory function to create a LocalizationAPIClient"""
    if '://' in server_url:
        # Remove protocol if present
        server_url = server_url.split('://', 1)[1]
    
    if ':' in server_url:
        host, port = server_url.split(':')
        return LocalizationAPIClient(server_host=host, server_port=int(port))
    else:
        return LocalizationAPIClient(server_host=server_url)

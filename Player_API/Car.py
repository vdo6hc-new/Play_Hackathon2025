from enum import Enum
class DeliveryStatus(Enum):
    IDLE        = "idle"
    PICKING_UP  = "picking_up"
    IN_TRANSIT  = "in_transit"
    DELIVERING  = "delivering"
    DELIVERED   = "delivered"
    FAILED      = "failed"
class Car:
    def __init__(self, car_id, client):
        self.car_id             = car_id
        self.client             = client
        self.status             = None
        self.target_package_id  = None
        self.control_command    = None
        self.position           = None
        self.delivery_status    = None
        self.package_list       = []
        self.route              = []
        self.cycle_time = 0.5 if (car_id == 10 or car_id == 12) else 0.75  # Default cycle time based on car ID
        
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
                self.position_mm     = self.status.position_mm
                self.control_command = self.status.control_command
                return True
        except Exception as e:
            print(f"Error getting state for Car {self.car_id}: {e}")
        return False

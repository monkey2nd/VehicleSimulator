from __future__ import annotations

from Class_dir.VehicleClass import Vehicle


class Accel:
    def __init__(self, accel, target_veh: Vehicle, desired_distance):
        self.accel = accel
        self.target_veh: Vehicle = target_veh
        self.desired_dis = desired_distance

    def __str__(self):
        return "accel: " + str(self.accel) + ", dd: " + str(self.desired_dis)

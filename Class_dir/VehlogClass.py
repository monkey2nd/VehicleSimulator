from __future__ import annotations

from typing import Dict, List, NamedTuple

from Class_dir.VehicleClass import Vehicle


class Vehtpl(NamedTuple):
    veh_id: int
    front: float
    lane: int
    vel: float
    vd: float
    accel: float
    accel_name: str
    vdcl: float
    distance: float
    desired_distance: float
    delta_v: float
    tau: float
    front_car_id: int | None
    back_car_id: int | None
    target_car_id: int | None
    app_car_id: int | None
    apped_car_id: int | None
    shift_front_veh_id: int | None
    shift_lane: bool
    shift_lane_to: int
    shift_begin_time: int
    shift_distance_go: float
    mode: int
    type: int
    ego: int

    @property
    def vel_h(self):
        return round(self.vel * 3.6, 2)

    @property
    def delta_v_h(self):
        return round(self.delta_v * 3.6, 2)

    @property
    def back(self):
        return self.front - 5

    @property
    def vd_h(self):
        return round(self.vd * 3.6, 2)

    @property
    def vdcl_h(self):
        return round(self.vdcl * 3.6, 2)


def make_vehtpl(veh_cls: Vehicle):
    return Vehtpl(veh_cls.veh_id, veh_cls.front, veh_cls.lane, veh_cls.vel, round(veh_cls.vd, 2),
                  round(veh_cls.accel, 2),
                  veh_cls.accel_name,
                  round(veh_cls.info.vdcl, 2),
                  round(veh_cls.distance, 1),
                  veh_cls.desired_distance, round(veh_cls.delta_v_h, 2), veh_cls.tau,
                  veh_cls.front_veh.veh_id if veh_cls.front_veh is not None else None,
                  veh_cls.back_veh.veh_id if veh_cls.back_veh is not None else None,
                  veh_cls.target_veh.veh_id if veh_cls.target_veh is not None else None,
                  veh_cls.app_veh.veh_id if veh_cls.app_veh is not None else None,
                  veh_cls.apped_veh.veh_id if veh_cls.apped_veh is not None else None,
                  veh_cls.shift_front_veh.veh_id if veh_cls.shift_front_veh is not None else None,
                  veh_cls.shift_lane, veh_cls.shift_lane_to, veh_cls.shift_begin_time, veh_cls.shift_distance_go,
                  veh_cls.info.mode, veh_cls.type, veh_cls.ego)


class Vehlog:
    def __init__(self):
        self.log: List[Dict[int, Vehtpl]] = []  # 時間軸ごとにnamedtupleが入る

    def set(self, tupdic: Dict[int, Vehtpl]) -> None:
        self.log.append(tupdic)

    def append(self, veh_ls: List[Vehicle]):
        log_dic: Dict[int, Vehtpl] = {}
        for vehicle in veh_ls:
            log_dic[vehicle.veh_id] = make_vehtpl(veh_cls=vehicle)
        self.set(tupdic=log_dic)

    def get_id_ls(self, time: int) -> List[int]:
        return list(self.log[time].keys())

    def get(self, time=None, veh_id=None) -> Vehtpl | dict[int, Vehtpl] | None:
        if time is not None:
            if veh_id is not None:
                if 0 <= time <= len(self.log) - 1 and veh_id in self.log[time].keys():
                    return self.log[time][veh_id]
                else:
                    return None
            else:
                return self.log[time]
        else:
            return None

    def get_logvalues(self, time):
        return self.log[time].values()

    def get_len(self, time):
        return len(self.log[time])

from __future__ import annotations

import random
from typing import Any, Dict, List

from Class_dir.Controller import Controller


class Vehicle:
    def __init__(self, veh_id) -> None:
        self.id: int = veh_id  # 0ID代入
        self.front = 0  # 1前方位置代入
        self.lane: int = -1  # 2車線代入
        self.vel: float = 0  # 3速度代入
        self.__vd: float = 0
        self.accel = 0  # 4加速度代入
        self.distance = 0  # 5車間距離代入
        self.desired_distance = 0
        self.delta_v = 0  # 6相対速度
        self.tau = 1.0
        self.front_veh: Vehicle | None = None  # 7 前方車両
        self.back_veh: Vehicle | None = None  # 8 後方車両
        self.target_veh: Vehicle | None = None  # 9 目標車両
        self.app_veh: Vehicle | None = None  # 10 基地局を用いたときに通信を行う合流車両クラス
        self.apped_veh: Vehicle | None = None  # 11 基地局を用いたときに通信を行う譲る車両クラス
        self.shift_front_veh: Vehicle | None = None  # 自社の目の前に車線変更してくる車両クラス
        self.shift_lane: bool = False  # 10 車線変更してる途中かどうか
        self.shift_lane_to = 0  # 11 どこの車線に変更しようとしてるか
        self.shift_begin_time = 0  # 12 車線変更開始時間
        self.shift_distance_go: float = 0  # 13 車線変更先車間距離
        self._control_mode = 0  # * 自動運転車両のみ使用する制御モード変数
        self.info: "VehicleInfo" = VehicleInfo(veh_id=veh_id)

    @property
    def back(self):
        return self.front - 5

    @property
    def list(self) -> List:
        return list(vars(self).values())

    @property
    def dict(self) -> Dict[str, Any]:
        return self.__dict__

    @property
    def vel_h(self) -> float:
        return self.vel * 3.6

    @property
    def vd(self) -> float:
        return self.__vd

    @property
    def vd_h(self) -> float:
        return self.__vd * 3.6

    @property
    def delta_v_h(self) -> float:
        return self.delta_v * 3.6

    @property
    def type(self) -> int:
        return self.info.type

    @property
    def ego(self) -> int:
        return self.info.ego

    @property
    def control_mode(self) -> int:
        """
        use_base_station == 2
        0:追従走行
        1:希望速度調整(50m)
        2:希望速度調整(75m)
        3:希望速度調整(100m)
        4:合流時加速制御
        5:合流時減速制御
        """
        return self._control_mode

    def set_vd(self, vd):
        vd = round(vd, 2)
        self.__vd = vd

    def change_tau(self, tau):
        self.tau = tau
        self.info.tau_changed_flag = True

    def init_tau(self):
        self.tau = 1.0
        self.info.tau_changed_flag = False

    def num_set(self, key, num) -> None:
        self.__dict__[key] = num

    def set_distance(self) -> None:
        # * front_carとの相対距離を求めdistanceに格納
        self.distance = self.front_veh.back - self.front

    def cal_delta_v(self) -> None:
        # * front_carとの相対速度を求めdelta_vに格納
        self.delta_v = self.vel - self.front_veh.vel

    @staticmethod
    def make_vd(min_vel, max_vel):
        return round(random.uniform(min_vel / 3.6, max_vel / 3.6), 2)

    def change_vd(self, controller: Controller, lane, extra_code=0):
        """
        車両生成時以外でvdを変化する関数
        """
        vd = 0
        if self.type == 0:
            if self.ego == 0:
                if lane == 0:
                    vd = self.make_vd(min_vel=86, max_vel=95)
                elif lane == 1:
                    vd = self.make_vd(min_vel=91, max_vel=100)
                elif lane == 2:
                    vd = self.make_vd(min_vel=101, max_vel=110)
                elif lane == 3:
                    vd = self.make_vd(min_vel=111, max_vel=120)
            elif self.ego == 1:
                if lane == 0:
                    vd = self.make_vd(min_vel=86, max_vel=95)
                elif lane == 1:
                    vd = self.make_vd(min_vel=91, max_vel=95)
                elif lane == 2:
                    vd = self.make_vd(min_vel=101, max_vel=105)
                elif lane == 3:
                    vd = self.make_vd(min_vel=111, max_vel=115)
        elif self.type == 1:
            if controller.speed_control:
                if extra_code == 0:
                    if lane == 0:
                        vd = round(80 / 3.6, 2)
                    elif lane == 1:
                        vd = round(85 / 3.6, 2)
                    elif lane == 2:
                        vd = self.make_vd(min_vel=101, max_vel=110)
                    elif lane == 3:
                        vd = self.make_vd(min_vel=111, max_vel=120)

                elif extra_code == 1:
                    if lane == 1:
                        vd = round(100 / 3.6, 2)
                elif extra_code == 2:
                    if lane == 1:
                        vd = round(93 / 3.6, 2)
                elif extra_code == 3:  # ? 追従走行用
                    if lane == 1:
                        vd = self.make_vd(min_vel=91, max_vel=100)

            elif controller.distance_control:
                if extra_code == 0:
                    if lane == 0:
                        vd = round(80 / 3.6, 2)
                        # self.vd = make_vd(min_vel=86, max_vel=95)
                    elif lane == 1:
                        vd = self.make_vd(min_vel=91, max_vel=100)
                    elif lane == 2:
                        vd = self.make_vd(min_vel=101, max_vel=110)
                    elif lane == 3:
                        vd = self.make_vd(min_vel=111, max_vel=120)
                if extra_code == 1:
                    vd = round(110 / 3.6, 2)
        self.set_vd(vd)

    def set_delta_v(self, acceleration_lane_end) -> None:
        # * front_carの存在を加味し適切なdelta_vを格納する関数
        if self.front_veh is None:
            if self.lane == 0 and (((self.vel ** 2) / 3.8) / 2 + 5 > (acceleration_lane_end - self.front)):
                self.delta_v = self.vel
            else:
                self.delta_v = 0
        else:
            self.cal_delta_v()

    def calculate_dd(self, target_car: 'Vehicle' = None) -> float:
        """
        希望車間距離
        target_carにCarクラスを入れるとその車両の後ろに合流するときの希望車間距離
        何も入れないと自分の前方車両との希望車間距離
        """
        run_car_info = self.info
        s0 = run_car_info.dis_stop
        v = self.vel
        t = self.tau
        treac = run_car_info.driver_reaction_time
        delta_v = self.delta_v if target_car is None else self.vel - target_car.vel
        a = run_car_info.max_accel
        b = run_car_info.desired_deceleration
        # ? s0:停止時最小車間距離　v:車両速度　t:安全車頭時間　treac:反応時間　delta_v:相対速度　a,最大加速度　b,希望減速度

        return round(s0 + v * (t + treac) + ((v * delta_v) / (((a * b) ** 0.5) * 2)), 1)

    def calculate_accel(self, desired_vehicle_distance=None, target_car: 'Vehicle' = None) -> float:
        """
        idmの計算式
        target_carにCarクラスを入れるとその車両の後ろに合流するときの加速度
        何も入れていないと前方車両に追従する加速度
        desired_vehicle_distance（希望車間距離）がなくても求めることができる
        """
        # ? a:最大加速度　v:車両速度　ss:希望車間距離　s:車間距離　vd:希望速度
        run_car_info = self.info
        a = run_car_info.max_accel
        v = self.vel
        ss = self.calculate_dd(
            target_car=target_car) if desired_vehicle_distance is None else desired_vehicle_distance
        s = self.distance if target_car is None else target_car.back - self.front
        vd = self.vd

        if s == 0:
            s = 0.1
        if ss < 0:
            ss = 0

        """if use_base_station == 2 and self.info.type == 1 and self.lane == 1 and acceleration_lane_start - 100 < self.front < acceleration_lane_start + 300:
            car_accel = min(0, car_accel)"""

        accel = round(a * min(1 - (v / vd) ** 4, 1 - (ss / s) ** 2), 2)
        if accel < -self.info.max_deceleration:
            accel = -self.info.max_deceleration

        return accel

    def shift_begin(self, shift_lane_to, time, follower: Vehicle | None = None) -> None:
        self.shift_lane = True
        self.shift_lane_to = shift_lane_to
        self.shift_begin_time = time
        if follower is not None:
            follower.shift_front_veh = self

    def canonicalize(self) -> None:
        self.distance = round(self.distance, 2)
        self.delta_v = round(self.delta_v, 2)

    def update_car(self, time) -> None:
        run_car_info = self.info
        self.canonicalize()
        self.vel = round(max(0.0, self.vel + self.accel / 10), 2)
        self.front = round(self.front + self.vel / 10, 2)
        self.accel = round(self.accel, 2)

        if self.shift_lane is True and time == self.shift_begin_time + 40:
            self.lane = self.shift_lane_to
            self.shift_lane_to = self.shift_begin_time = self.shift_distance_go = 0
            self.shift_lane = False
            run_car_info.mode = 0
            if self.app_veh is not None:
                self.info.mode = 0
                self.app_veh.info.mode = 0
                self.app_veh.apped_veh = None
                self.app_veh = None

        if self.shift_front_veh is self.front_veh:  # 前方に車線変更してくる車両が車線変更し終わったら
            self.shift_front_veh = None

        # ! 衝突時条件
        if self.front_veh is not None:
            if self.front_veh.back < self.front < self.front_veh.front:
                if self.vel > self.front_veh.vel:
                    self.vel = self.front_veh.vel


class VehicleInfo:
    def __init__(self, veh_id) -> None:
        self.id: int = veh_id  # 0:Id
        self.max_accel = 0  # 1:最大加速度
        self.max_deceleration = 1.5  # ? 最大限速度
        self.desired_deceleration = 0  # 2:希望減速度
        self.driver_reaction_time = 0  # 4:反応時間
        self.dis_stop = 1.65  # 5:停止時最低車間距離
        self.v_init = 0  # 6:初期速度
        self.type = -1  # ? 8 0:手動運転 1:自動運転
        self.ego = 0  # ? 車線変更時譲らない車両 0:譲る　1:譲らない
        self.occur_time = 0  # 9車両発生時刻
        self.mode = 0  # ? 現在の状態を表す変数(0:通常走行中,1:合流中,2:車線変更中,3加速制御,4:減速制御,5:減速軽減)
        self.shift_time = 0  # ? 15 手動運転車両が車線変更する時間
        self.min_vel = 0
        self.vdcl = 0  # ? vel diff to change lanes 車線変更を行う希望速度と走行速度の速度差
        self.vel_sensor_flag = 0  # ? 自動合流を行う際vel_sensor_pointを通過したかどうか
        self.second_flag = 0  # ? 第二制御（第二走行車線から第一走行車線に車線変更を行う制御）を行ったかどうか
        self.tau_changed_flag = False  # tauが初期状態から変更されているかを確認するフラグ

    @property
    def list(self) -> List:
        return list(self.__dict__.values())

    @property
    def dict(self) -> Dict:
        return self.__dict__

    @property
    def v_init_h(self):
        return self.v_init * 3.6

    @property
    def min_vel_h(self):
        return self.min_vel * 3.6

    @property
    def vdcl_h(self):
        return self.vdcl * 3.6

    def __str__(self) -> str:
        return str(self.dict)

    def num_set(self, key, num) -> None:
        self.__dict__[key] = num

    def ls_set(self, ls: List) -> None:
        if type(ls) == list:
            if len(ls) <= len(self.list):
                for key, num in zip(self.dict.keys(), ls):
                    self.num_set(key, num)

    def update_shift_time(self):
        if not self.shift_time == -1:
            self.shift_time += 20


class BaseStation:
    def __init__(self):
        self.csp = 0  # 0 Communication Start Place 通信開始位置
        self.cep = 0  # 1 Communication End Place 通信終了位置

    @property
    def list(self) -> List:
        return list(self.__dict__.values())

    @property
    def dict(self) -> Dict:
        return self.__dict__

    def __str__(self) -> str:
        return str(self.__dict__)


def make_car_info(veh_max) -> List[VehicleInfo]:
    return [VehicleInfo(id) for id in range(veh_max)]


def make_car(time_max, veh_max) -> List[List[Vehicle]]:
    return [[Vehicle(id_) for id_ in range(veh_max)] for _ in range(time_max)]


def make_base_station(veh_max) -> List[BaseStation]:
    return [BaseStation() for _ in range(veh_max)]

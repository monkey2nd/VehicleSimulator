from __future__ import annotations

from random import Random
from typing import List

from Class_dir.Controller import Controller
from Class_dir.DataCollect import DataCollect
from Class_dir.ParticularCar import InvisibleVehicle
from Class_dir.VehicleClass import Vehicle


# ? 車線情報管理クラス


class LaneManager:
    def __init__(self, lane_num: int, controller: Controller, merging_ratio, penetration, ego_ratio, seed) -> None:
        self.lane_num = lane_num  # ? 車線数
        self.run_vehicle_ls: List[Vehicle] = []  # ? 現在走行している車両のCarクラスリスト
        self.q_lane_ls = []  # ? 各車線を走行する合計車両数のリスト
        self.lane_vehicle_lists: List[List[Vehicle]] = [[] for _ in range(lane_num)]  # ? 現在走行している各車線ごとのCarリスト

        self.occur_num_ls = [0 for _ in range(lane_num)]  # ? 各車線ごとの車両発生数
        self.frequency_ls = []  # ? 各車線の車両発生感覚
        self.generate_time_ls: List[List] = []  # ? 車両発生時刻用リスト
        self.next_generate_car_id = 1  # ? 次に発生する車両id

        self.penetration = penetration
        self.merging_ratio = merging_ratio
        self.ego_ratio = ego_ratio
        self.lane_ratio = [0.3, 0.3, 0.4]  # ? 各車線の車両交通量
        # self.lane_ratio = [0.3, 0.3, 0.4]  # ? 各車線の車両交通量

        self.ms_start = 1200  # ? 加速車線開始位置
        self.ms_end = self.ms_start + 300  # ? 加速車線終了位置
        self.road_length = self.ms_end + 400  # ? 道路の長さ

        # self.vel_sensor_area = 10  # ? 合流車線を走る普通車両の速度検出を行うvel_sensorの検知範囲
        self.vel_sensor_point = 1100  # ? 通信開始位置
        self.communication_area = 30  # ? 通信範囲
        # self.communication_start_point = 800  # ? 通信開始位置

        self.second_control_point = 300  # ? 第二走行車線を走る自動運転車両を第一走行車線に車線変更させる処理開始地点
        self.second_control_car_ls = []  # ? 制御により左車線などに移動させた車両クラスリスト
        self.second_control_car_limit = 99

        self.third_control_point = 500  # ? 自動運転車両のtauを変更し始める地点
        self.no_lane_change_point = 100  # ? 車線変更禁止地点
        # self.car_ls_changed_alpha = []
        # self.car_limit_changed_alpha = 3
        self.controller: Controller = controller
        self.invisible_car = InvisibleVehicle(-1)  # ? 第1走行車線の先頭に置く

        self.random = Random()
        self.random.seed(seed)

    @property
    def car_max(self) -> int:
        return sum(self.q_lane_ls)

    def get_lane(self, lane: int) -> List[Vehicle]:  # ? 車線laneの先頭からの車両リストの取得
        return self.lane_vehicle_lists[lane]

    def get_q(self, lane: int) -> int:
        return self.q_lane_ls[lane]

    def get_generate_time_lane(self, lane: int) -> List:
        return self.generate_time_ls[lane]

    def occur_increment(self, lane: int) -> None:
        if self.occur_num_ls[lane] < self.q_lane_ls[lane] - 1:
            self.occur_num_ls[lane] += 1

    def next_id_increment(self) -> None:
        self.next_generate_car_id += 1

    def make_q_lane_ls(self, car_max, q_lane0) -> None:
        self.q_lane_ls.append(q_lane0)
        for ratio in self.lane_ratio:
            self.q_lane_ls.append(int(car_max * ratio))

    def set_frequency(self, time_max) -> None:
        for q_lane in self.q_lane_ls:
            self.frequency_ls.append(int(time_max / q_lane))

    def generate_time(self) -> None:
        for q_lane in self.q_lane_ls:
            self.generate_time_ls.append([0 for _ in range(q_lane)])

    def generate_random(self, per):
        return 1 if per > self.random.random() else 0

    def return_rand_frequency(self, frequency) -> int:
        return int(frequency * round(self.random.uniform(-0.5, 0.5), 2))

    def get_lcvd(self, min_vel=5, max_vel=10):
        return round(self.random.uniform(min_vel / 3.6, max_vel / 3.6), 2)

    def make_car_timetable(self) -> None:
        self.generate_time()
        for lane in range(self.lane_num):  # * 各車線ごとにループを回す
            lane_generate_time_ls = self.generate_time_ls[lane]
            prev_gen_time = 0  # 次のループで参照する１ループ前のgenerate_time
            for car_num in range(self.q_lane_ls[lane] - 1):
                gen_time = prev_gen_time + self.frequency_ls[lane]
                if not lane == 0:
                    gen_time += self.return_rand_frequency(self.frequency_ls[lane])
                prev_gen_time = gen_time
                lane_generate_time_ls[car_num + 1] = gen_time

    def init_lane_car_list(self) -> None:  # ? lane_id_lsを[[],[],...,[]]に初期化する関数
        self.lane_vehicle_lists = [[] for _ in range(self.lane_num)]

    def make_lane_car_ls(self) -> None:
        """
        各車線ごとの車両クラスリストを作成
        """
        lane_car_tmp = [[] for _ in range(self.lane_num)]
        self.init_lane_car_list()

        if len(self.run_vehicle_ls) > 0:

            for run_car in self.run_vehicle_ls:
                lane_car_tmp[run_car.lane].append([run_car, run_car.front])

            for lane in range(self.lane_num):
                lane_car_tmp[lane] = sorted(lane_car_tmp[lane], key=lambda x: x[1], reverse=True)

            for lane in range(self.lane_num):
                for car_front_ls in lane_car_tmp[lane]:
                    self.get_lane(lane).append(car_front_ls[0])

    def set_veh_param(self, veh: Vehicle, front_car: Vehicle, time, lane) -> None:
        veh_info = veh.info
        if lane == 0:
            if self.controller.merging_control:
                veh_info.type = self.generate_random(self.merging_ratio)
            else:
                veh_info.type = 0
        else:
            if not self.controller.use_control:
                veh_info.type = 0
            else:
                veh_info.type = self.generate_random(self.penetration)
            if veh_info.type == 0:
                veh_info.ego = self.generate_random(self.ego_ratio)

        self.set_vd(vehicle=veh, lane=lane)
        if lane == 0:
            v_measure = veh.vd
        else:
            if front_car is None:  # ? 前方に車両がない場合
                v_measure = veh.vd
            else:  # ? 前方に車両があった場合
                v_measure = min(front_car.vel, veh.vd)

        # ? 各値更新
        if veh.type == 0:
            veh_info.merging_interval = self.random.randint(30, 40)
        elif veh.type == 1:
            veh_info.merging_interval = self.random.randint(20, 30)
        veh_info.max_accel = round(self.random.uniform(0.55, 0.75), 2)
        # self.desired_Deceleration = round(random.uniform(0.5, 1), 2)
        veh_info.desired_deceleration = round(self.random.uniform(0.5, 1.5), 2)
        veh_info.driver_reaction_time = round(self.random.uniform(0.54, 0.74), 2)
        veh_info.v_init = veh.vel = v_measure
        veh_info.occur_time = time
        veh_info.shift_time = time + self.random.randint(1, 20)
        veh_info.min_vel = v_measure
        veh_info.vdcl = self.get_lcvd() if veh.ego == 0 else self.get_lcvd(min_vel=10, max_vel=15)
        veh.front = 5
        veh.vel = v_measure

    def generate_vehicle(self, dc: DataCollect, time: int) -> None:
        for lane in range(self.lane_num):  # * 各車線ごとに処理をループ
            generate_time_lane = self.get_generate_time_lane(lane)
            if time == generate_time_lane[self.occur_num_ls[lane]] and self.next_generate_car_id < self.car_max:
                next_gen_veh = Vehicle(veh_id=self.next_generate_car_id)
                next_gen_veh.lane = lane
                lane_ls = self.get_lane(lane)
                if not lane_ls:
                    next_gen_veh.front_veh = None
                    next_gen_veh.distance = 9999
                else:
                    next_gen_veh.front_veh = lane_ls[-1]
                    next_gen_veh.distance = next_gen_veh.front_veh.back - 5

                # self.set_vd(vehicle=next_gen_veh, lane=lane)

                self.set_veh_param(veh=next_gen_veh, front_car=next_gen_veh.front_veh, time=time, lane=lane)

                self.run_vehicle_ls.append(next_gen_veh)  # ? sort必要かも
                self.next_id_increment()  # ? next_idを+1
                self.occur_increment(lane)
                dc.dece_ls[next_gen_veh.veh_id].set_v_init(v_init=next_gen_veh.info.v_init)

    def make_vd(self, min_vel: int, max_vel: int) -> float:
        # この関数を変更する必要あり！
        return round(self.random.uniform(min_vel / 3.6, max_vel / 3.6), 2)

    def set_vd(self, vehicle: Vehicle, lane: int, extra_code=0) -> None:
        """
        車両生成時にのみvdを生成する関数
        """
        vd = 0
        if vehicle.type == 0:
            if vehicle.ego == 0:
                if lane == 0:
                    vd = self.make_vd(min_vel=85, max_vel=95)
                    # vd = self.make_vd(min_vel=80, max_vel=90)
                    # todo ここを変えると大きく変化
                elif lane == 1:
                    vd = self.make_vd(min_vel=91, max_vel=100)
                elif lane == 2:
                    vd = self.make_vd(min_vel=101, max_vel=110)
                elif lane == 3:
                    vd = self.make_vd(min_vel=111, max_vel=120)
            elif vehicle.ego == 1:
                if lane == 0:
                    vd = self.make_vd(min_vel=86, max_vel=95)
                elif lane == 1:
                    vd = self.make_vd(min_vel=91, max_vel=95)
                elif lane == 2:
                    vd = self.make_vd(min_vel=101, max_vel=105)
                elif lane == 3:
                    vd = self.make_vd(min_vel=111, max_vel=115)
        elif vehicle.type == 1:
            if self.controller.speed_control:
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

            elif self.controller.distance_control:
                if extra_code == 0:
                    if lane == 0:
                        vd = round(85 / 3.6, 2)
                        # self.vd = vd_make(min_vel=86, max_vel=95)
                    elif lane == 1:
                        vd = self.make_vd(min_vel=91, max_vel=100)
                        # vd = round(110 / 3.6, 2)
                    elif lane == 2:
                        vd = self.make_vd(min_vel=101, max_vel=110)
                    elif lane == 3:
                        vd = self.make_vd(min_vel=111, max_vel=120)
                if extra_code == 1:
                    vd = round(110 / 3.6, 2)
        vehicle.set_vd(vd)

    def remove_car(self):
        """
        道路を走り終えた車両の削除
        """
        for check_car in self.run_vehicle_ls:
            if check_car.front > self.road_length:
                self.run_vehicle_ls.remove(check_car)
                # check_car.lane = -1
                if check_car in self.second_control_car_ls:
                    self.second_control_car_ls.remove(check_car)
                del check_car
        """
            if check_car.shift_begin_time + 40 == time and check_car.lane == 0 and self.search_car(vehlog=vehlog, 
            time=time - 1, Id=check_car.Id).shift_lane == 1:
                if check_car.vel < 40 / 3.6 or self.search_car(vehlog=vehlog, time=time - 40, Id=check_car.Id).vel_h 
                - check_car.vel_h > 10:
                    self.run_vehicle_ls.remove(check_car)
                    check_car.lane = -1

            if check_car.shift_lane == 0 and check_car.front > 950 and check_car.lane == 0:
                self.run_vehicle_ls.remove(check_car)
                check_car.lane = -1
        """

    def set_car(self):
        """
        carクラスのfront_car,back_car,distance,delta_v,alphaを設定する関数
        """
        for lane in range(self.lane_num):
            lane_car_ls = self.get_lane(lane)
            for index_, check_car in enumerate(lane_car_ls):
                if index_ == 0:
                    if check_car.lane == 0:
                        check_car.distance = self.ms_end - check_car.front
                    else:
                        check_car.distance = float('infinity')

                    if not index_ == len(lane_car_ls) - 1:
                        check_car.back_veh = lane_car_ls[index_ + 1]

                    check_car.front_veh = None
                    check_car.set_delta_v(acceleration_lane_end=self.ms_end)

                elif index_ == len(lane_car_ls) - 1:
                    check_car.front_veh = lane_car_ls[index_ - 1]
                    check_car.back_veh = None
                    check_car.set_distance()
                    check_car.set_delta_v(acceleration_lane_end=self.ms_end)

                else:
                    check_car.front_veh = lane_car_ls[index_ - 1]
                    check_car.back_veh = lane_car_ls[index_ + 1]
                    check_car.set_distance()
                    check_car.set_delta_v(acceleration_lane_end=self.ms_end)

                    """
                    elif self.use_base_station == 1:
                    if check_car.type == 1 and check_car.lane == 1 and check_car.info.mode == 3 and self.acceleration_lane_start < check_car.front:
                        check_car.info.alpha = 0.3
                    else:
                        check_car.info.alpha = 1"""

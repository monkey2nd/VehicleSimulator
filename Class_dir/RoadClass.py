from typing import List, Tuple

from openpyxl import Workbook
from tqdm import tqdm

from Class_dir.Accel import Accel
from Class_dir.DataCollect import DataCollect
from Class_dir.LaneManager import LaneManager
from Class_dir.VehicleClass import Vehicle
from Class_dir.VehlogClass import Vehlog
from random_maker import generate_random
from save import create_avg_vel_log, create_log_sheet, create_merging_info_sheet, create_path, create_visual_sheet, \
    deceleration_log_sheet, \
    lane_penetration_log


# noinspection PyTypeChecker
class Road:
    def __init__(self, time_max, interval) -> None:
        self.dc = None
        self.vehlog: Vehlog = Vehlog()
        self.lm: LaneManager = None
        self.TIME_MAX = time_max * 10
        self.time = 0
        self.interval = interval
        self.second_ct_ls = []

    def lm_init(self, car_max, q_lane0, merging_ratio, penetration, ego, seed):
        self.lm = LaneManager(lane_num=4, merging_ratio=merging_ratio, penetration=penetration, ego_ratio=ego,
                              seed=seed)
        self.lm.make_q_lane_ls(car_max=car_max, q_lane0=q_lane0)
        self.lm.set_frequency(time_max=self.TIME_MAX, )
        self.lm.make_car_timetable()

    def car_init(self):
        self.dc = DataCollect(car_max=self.lm.car_max)

    def change_time_max(self):
        self.TIME_MAX += 1200  # ? ある程度の時間を加算しないと走行中にシミュレーションが終了してしまうため

    def set_time(self, time):
        self.time = time

    def canshift(self, vehicle: Vehicle, dst_lane) -> bool:
        """
        シナジーで使われている車線変更条件をPythonに置きなおしたもの（by koki）
        対象車両が車線変更できるときtrueを返しできないときFalseを返す
        """
        veh_info = vehicle.info
        leader: Vehicle = None  # ? 目的車線先行車両
        leader_dis = float("infinity")  # ? ↑との車間距離

        follower: Vehicle = None  # ? 目的車線追従車両
        follower_dis = float("infinity")  # ? ↑との車間距離

        for dst_lane_car in self.lm.get_lane(dst_lane):  # ? 車線変更先(dst_lane)のレーンリスト
            distance_front = dst_lane_car.back - vehicle.front
            distance_back = vehicle.back - dst_lane_car.front

            if distance_front >= 0:
                leader = dst_lane_car
                leader_dis = min(leader_dis, distance_front)

            elif distance_front < 0 and distance_back < 0:  # ? 並走条件
                return False

            elif distance_back >= 0:
                follower = dst_lane_car
                follower_dis = min(distance_back, follower_dis)
                break

        if leader is not None and vehicle.vel > leader.vel:
            # ? 最小車間距離
            min_front_distance = (vehicle.vel - leader.vel) ** 2 / veh_info.desired_Deceleration / 2 + veh_info.dis_stop
            if min_front_distance > leader_dis:
                return False

        if follower is not None:
            min_back_distance = (follower.vel - vehicle.vel) ** 2 / follower.info.desired_Deceleration / 2 + \
                                follower.info.dis_stop
            if min_back_distance > follower_dis:
                return False

        return True

    def getneighbors(self, vehicle: Vehicle, dst_lane) -> Tuple[Vehicle, Vehicle]:
        """
        対象車両(vehicle)の近くを走行する車両(dst_laneを走行しているものとする)leader,follower を取得する,
        leaderは先行車両,followerは後続車両
        """
        leader: Vehicle = None
        leader_dis = float("infinity")

        follower: Vehicle = None
        follower_dis = float("infinity")

        for dst_lane_car in self.lm.get_lane(dst_lane):
            dis_front = dst_lane_car.front - vehicle.front
            dis_back = vehicle.back - dst_lane_car.back

            if dis_front >= 0:
                leader = dst_lane_car
                leader_dis = min(leader_dis, dis_front)

            elif dis_back >= 0:
                follower = dst_lane_car
                follower_dis = min(dis_back, follower_dis)
                break
        return leader, follower

    def manual_shift_to_R(self, vehicle: Vehicle):
        run_car_info = vehicle.info
        if vehicle.vel_h < vehicle.vd_h - vehicle.info.vdcl_h:  # (希望速度-vdcl_h) km/h より遅いか
            if vehicle.accel <= 0 and vehicle.front_car is not None:
                # 前方に車両がある（なければその車線を走ってれば加速できるため）かつ減速している（加速している場合はその車線を走れば速度が上がるため）
                if vehicle.front_car.shift_lane is False:
                    next_car, prev_car = self.getneighbors(vehicle=vehicle,
                                                           dst_lane=vehicle.lane + 1)  # next_carのみ必要（next_car:車線変更先の前方車両）
                    if next_car is None or next_car.vel_h - vehicle.front_car.vel_h > run_car_info.vdcl_h:  # ?
                        # 車線変更先の前方車両が現在の前方車両より 5km/h　以上速い場合
                        if self.canshift(vehicle=vehicle, dst_lane=vehicle.lane + 1):  # ? 物理的に車線変更できるか
                            if generate_random(per=0.5):  # ? みんながみんな車線変更するわけではないので確率を当てる
                                vehicle.shift_lane = True
                                vehicle.shift_lane_to = vehicle.lane + 1
                                vehicle.change_vd(use_base_station=self.lm.use_base_station, lane=vehicle.lane + 1)
                                vehicle.shift_begin_time = self.time
                                run_car_info.mode = 2

                                return True
        return False

    def calculate_accel(self, run_car: Vehicle):
        """
        run_carの加速度を決定する関数
        """
        # ** 全車両対応追従用加速度計算
        run_car_info = run_car.info
        lm = self.lm
        use_base_station = lm.use_base_station
        accel_ls: List[Accel] = []

        target_car = run_car.front_car
        dd = run_car.calculate_dd()
        car_accel = run_car.calculate_accel()

        accel_ls.append(Accel(accel=car_accel, target_veh=target_car, desired_distance=dd))

        # ** 基地局を用いない合流の車両加速度計算
        if run_car.lane == 0 and lm.acceleration_lane_start < run_car.front < lm.acceleration_lane_end and car_accel >= 0:  # * 合流可能な範囲に入って前方車両がいなければ最大加速度で加速する
            if (run_car.vel ** 2 / 3.8) / 2 + 5 < (lm.acceleration_lane_end - run_car.front):
                if self.canshift(vehicle=run_car, dst_lane=run_car.lane + 1):
                    car_accel = run_car_info.max_accel
                else:
                    car_accel = 0
                leader, follower = self.getneighbors(vehicle=run_car, dst_lane=1)
                dd = run_car.calculate_dd(target_car=leader)
                accel_ls.append(Accel(accel=car_accel, target_veh=leader, desired_distance=dd))

        if not run_car.lane == 0:

            if run_car.shift_lane is True:  # * 本線を走行してかつ車線変更をしようとしている車両
                leader, follower = self.getneighbors(vehicle=run_car, dst_lane=run_car.shift_lane_to)
                target_car = leader if leader is not None else lm.invisible_car

                distance_next_car = target_car.back - run_car.front
                dd_next_veh = run_car.calculate_dd(target_car=target_car)
                car_accel = -0.5 if distance_next_car < 0 else run_car.calculate_accel(
                    desired_vehicle_distance=dd_next_veh, target_car=target_car)

                if dd_next_veh > distance_next_car and (run_car.delta_v <= 0 or
                                                        run_car.distance / run_car.vel >
                                                        run_car.shift_begin_time + 40 - self.time):
                    run_car.shift_distance_go = distance_next_car
                    accel_ls.append(Accel(accel=car_accel, target_veh=target_car, desired_distance=dd_next_veh))

            elif run_car.shift_lane is False:  # *　本線を走行してかつ車線変更していない車両
                if not run_car.ego == 1:
                    leader, follower = self.getneighbors(vehicle=run_car,
                                                         dst_lane=run_car.lane - 1)  # ! lane - 1としているのは合流部において右側にしか車線変更しない条件化でのみ有効
                    if leader is not None \
                            and leader.shift_lane_to == run_car.lane \
                            and leader.target_car == run_car.front_car:

                        distance_next_car = leader.back - run_car.front
                        dd_next_car = run_car.calculate_dd(target_car=leader)

                        if distance_next_car < 0:
                            car_accel = -0.5
                        else:
                            car_accel = run_car.calculate_accel(target_car=leader,
                                                                desired_vehicle_distance=dd_next_car)

                        if dd_next_car < distance_next_car:
                            accel_ls.append(Accel(accel=car_accel, target_veh=target_car, desired_distance=dd_next_car))
        # 次回　この続きをやる（accellsを用いてaccel適切か）
        # **以下は基地局を使った譲るなどを考慮したになにか入れる)
        # ** 加速車線の車両
        if use_base_station == 1 or use_base_station == 2:
            if run_car.lane == 0:
                if run_car_info.type == 1:  # * 合流車両が自動運転車両の時
                    app_car = run_car.app_car
                    if app_car is not None:  # * 譲ってくれる車両が存在するとき and 自車（合流車両）が自動運転車両の時(手動の時は制御なし)
                        if app_car.lane == 1:  # * app_carが第一走行車線にいるとき
                            if app_car.info.mode == 4:  # * app_carが減速制御を行っている場合
                                app_front_car = app_car.front_car

                                if app_front_car is None:
                                    app_front_car = lm.invisible_car
                                distance_app_front_car = app_front_car.back - run_car.front  # ?app_front_carとの車間距離
                                dd_app_front_car = run_car.calculate_dd(target_car=app_front_car)

                                if distance_app_front_car < 0:
                                    car_accel = -1.0
                                else:
                                    car_accel = run_car.calculate_accel(target_car=app_front_car,
                                                                        desired_vehicle_distance=dd_app_front_car)

                                accel_ls.append(Accel(accel=car_accel,
                                                      target_veh=app_front_car,
                                                      desired_distance=dd_app_front_car))

                            elif app_car.info.mode == 3:  # * app_carが加速制御を行っている場合
                                distance_app_car = app_car.back - run_car.front
                                dd_app_car = run_car.calculate_dd(target_car=app_car)
                                if distance_app_car < 0:
                                    car_accel_tmp = -1.0
                                else:
                                    car_accel_tmp = run_car.calculate_accel(target_car=app_car,
                                                                            desired_vehicle_distance=dd_app_car)

                                accel_ls.append(Accel(accel=car_accel, target_veh=app_car, desired_distance=dd_app_car))
                        else:  # *app_carが第一走行車線にいないとき(基本的にない)
                            run_car.app_car.apped_car = None
                            run_car.app_car = None

            elif run_car.lane == 1:
                if run_car_info.type == 1:
                    apped_car = run_car.apped_car
                    if apped_car is not None:
                        if apped_car.lane == 0:
                            if run_car_info.mode == 4:  # * 自車（譲る車両）が減速制御を行っているとき
                                distance_merge_car = apped_car.back - run_car.front
                                if distance_merge_car < 0:  # * 自車（譲る車両）が前方にいるとき
                                    car_accel = -1.0
                                else:
                                    car_accel = run_car.calculate_accel(target_car=apped_car)

                                dd = run_car.calculate_dd(target_car=apped_car)
                                accel_ls.append(Accel(accel=car_accel, target_veh=apped_car, desired_distance=dd))

                            elif run_car_info.mode == 3:  # *自車（譲る車両）が加速制御を行っている場合
                                distance_merge_car = run_car.back - apped_car.front
                                if distance_merge_car < 0:
                                    accel_ls.append(Accel(accel=1.0, target_veh=run_car.front_car,
                                                          desired_distance=run_car.calculate_dd()))

                        else:  # * 合流車両が合流車線にいないとき（↑と比べてこっちは合流終了時にこの条件に入る）
                            run_car.apped_car.app_car = None
                            run_car.apped_car = None
                            target_car = run_car.front_car
                            run_car.info.mode = 0

        if run_car_info.type == 0 and run_car.lane == 0 and run_car.front < lm.acceleration_lane_start:
            car_accel = max(car_accel, 0)
        min_accel: Accel = min(accel_ls, key=lambda x: x.accel)
        run_car.accel = min_accel.accel
        run_car.target_car = min_accel.target_veh
        run_car.desired_distance = min_accel.desired_dis

    def check_flag(self, run_car: Vehicle):
        """
        最大加速度で自動運転車両が加速したとき合流車両を追い越すことができるか判定する関数
        """
        apped_car = run_car.apped_car
        run_car_info = run_car.info

        if run_car.apped_car is not None:

            x1 = self.lm.acceleration_lane_start - apped_car.back
            t1 = x1 / apped_car.vel

            x2 = run_car_info.max_accel * t1 ** 2 / 2 + run_car.vel * t1

            if not x2 > self.lm.acceleration_lane_start + 5 or run_car.calculate_dd() > run_car.distance:
                return False

        return True

    def simulation(self):
        lm = self.lm
        dc = self.dc
        use_base_station = lm.use_base_station
        for time in tqdm(range(self.TIME_MAX), desc="simu"):
            self.set_time(time=time)
            lm.make_lane_car_ls()
            lm.set_car()  # ? front_car,back_car,distance_delta_v,alpha
            second_control_car_ls_tmp: List[Vehicle] = []  # ?　第二走行車線から第一走行車線に車線変更を行った自動運転車両の車両クラスリスト

            for vehicle in lm.run_vehicle_ls:
                vehicle_info = vehicle.info

                self.calculate_accel(run_car=vehicle)

                if vehicle.shift_lane is False:  # *　車線変更を開始していないとき
                    if vehicle_info.type == 0:  # * 手動運転車両の挙動
                        if vehicle.lane == 0:
                            if lm.acceleration_lane_start < vehicle.back:
                                if self.canshift(vehicle=vehicle, dst_lane=vehicle.lane + 1):
                                    vehicle.shift_begin(shift_lane_to=vehicle.lane + 1, time=self.time)

                            elif lm.acceleration_lane_start < vehicle.front and vehicle_info.mode != 1:
                                prev_vd = vehicle.vd
                                vehicle.change_vd(lane=vehicle.lane + 1, use_base_station=use_base_station)
                                if vehicle.vd < prev_vd:
                                    vehicle.set_vd(prev_vd)
                                vehicle_info.mode = 1  # modeを合流中に変更
                                del prev_vd

                            elif (lm.vel_sensor_point < vehicle.front and
                                  vehicle_info.vel_sensor_flag == 0 and
                                  use_base_station != 0):
                                vehicle_info.vel_sensor_flag = 1
                                if vehicle.app_car is None:
                                    cep = vehicle.front + 10
                                    csp = vehicle.back - lm.communication_area

                                    app_ls: List[List[Vehicle, float]] = []
                                    for app_car in lm.get_lane(1):
                                        if (csp < app_car.front and app_car.back < cep and
                                                app_car.info.type == 1):
                                            app_ls.append([app_car, round(vehicle.front - app_car.front, 0)])

                                    if not app_ls == []:
                                        app_ls.sort(key=lambda x: x[1])
                                        app_car = app_ls[0][0]
                                        app_car.apped_car = vehicle
                                        dc.set_cd(id=vehicle.id, csp=csp, cep=cep)

                        elif vehicle.lane == 1:
                            if not vehicle_info.shift_time == -1 and vehicle_info.shift_time == time and vehicle_info.ego == 0:
                                if self.manual_shift_to_R(vehicle=vehicle):
                                    vehicle_info.shift_time = -1
                                else:
                                    vehicle_info.update_shift_time()

                        elif vehicle.lane == 2:
                            if not vehicle_info.shift_time == -1 and vehicle_info.shift_time == time and vehicle_info.ego == 0:
                                if self.manual_shift_to_R(vehicle=vehicle):
                                    vehicle_info.shift_time = -1
                                else:
                                    vehicle_info.update_shift_time()
                        elif vehicle.lane == 3:
                            pass

                    elif vehicle_info.type == 1:  # * 自動運転車両の挙動
                        if vehicle.lane == 0:
                            if lm.acceleration_lane_start < vehicle.back:
                                if self.canshift(vehicle=vehicle, dst_lane=vehicle.lane + 1):
                                    vehicle.shift_begin(shift_lane_to=vehicle.lane + 1, time=self.time)

                            elif lm.acceleration_lane_start < vehicle.front and vehicle_info.mode != 1:
                                prev_vd = vehicle.vd
                                vehicle.change_vd(lane=vehicle.lane + 1, use_base_station=use_base_station)
                                if vehicle.vd < prev_vd:
                                    vehicle.set_vd(prev_vd)
                                vehicle_info.mode = 1
                                del prev_vd

                            elif (lm.vel_sensor_point < vehicle.front and
                                  vehicle_info.vel_sensor_flag == 0 and
                                  use_base_station != 0):
                                vehicle_info.vel_sensor_flag = 1
                                if vehicle.app_car is None:
                                    cep = vehicle.front + 10
                                    csp = vehicle.back - lm.communication_area

                                    app_ls: List = []
                                    for app_car in lm.get_lane(1):
                                        if (csp < app_car.front and app_car.back < cep and
                                                app_car.info.type == 1):
                                            app_ls.append([app_car, round(vehicle.front - app_car.front, 0)])

                                    if not app_ls == []:
                                        app_ls.sort(key=lambda x: x[1])
                                        app_car = app_ls[0][0]
                                        vehicle.app_car = app_car
                                        app_car.apped_car = vehicle
                                        dc.set_cd(id=vehicle.id, csp=csp, cep=cep)

                        elif vehicle.lane == 1:
                            if use_base_station == 1:
                                if vehicle.back > lm.vel_sensor_point:
                                    if vehicle_info.mode == 0 or vehicle_info.mode == 5:
                                        vehicle.change_vd(use_base_station=use_base_station, lane=vehicle.lane,
                                                          extra_code=1)
                                        if vehicle.apped_car is not None:
                                            apped_car = vehicle.apped_car
                                            if apped_car.info.type == 0:
                                                if (apped_car.back - vehicle.front < 5 and
                                                        vehicle.vel > apped_car.vel):  # ? 加速して後ろに譲る
                                                    vehicle_info.mode = 3  # modeを加速制御中に変更
                                                    vehicle.set_vd(vehicle.vd + 20 / 3.6)
                                                else:
                                                    vehicle_info.mode = 4
                                            else:
                                                vehicle_info.mode = 4
                                        else:
                                            vehicle_info.mode = 3
                                            vehicle.set_vd(vehicle.vd + 20 / 3.6)

                                elif vehicle.front > lm.vel_sensor_point - 100:
                                    if vehicle_info.mode == 0:
                                        vehicle.change_vd(use_base_station=use_base_station, lane=vehicle.lane,
                                                          extra_code=2)
                                        vehicle_info.mode = 5

                            elif use_base_station == 2:
                                if vehicle.info.tau_changed_flag is False:
                                    if lm.third_control_point < vehicle.front < lm.vel_sensor_point and vehicle.apped_car is None:
                                        if vehicle.back_car is not None and vehicle.back_car.type == 0:
                                            vehicle.change_tau(2.0)

                                if vehicle.apped_car is not None:
                                    apped_car = vehicle.apped_car
                                    if apped_car.back - vehicle.front < 5 and vehicle.vel > apped_car.vel:
                                        vehicle_info.mode = 3
                                        vehicle.change_tau(1.0)
                                        vehicle.set_vd(vehicle.vd + 20 / 3.6)
                                    else:
                                        vehicle_info.mode = 4
                                else:
                                    if vehicle.back > lm.vel_sensor_point:
                                        vehicle_info.mode = 3
                                        vehicle.change_tau(1.0)
                                        vehicle.set_vd(vehicle.vd + 20 / 3.6)


                        elif vehicle.lane == 2:
                            if use_base_station == 1 or use_base_station == 2:
                                if lm.second_control_point < vehicle.front and vehicle_info.second_flag == 0:
                                    vehicle_info.second_flag = 1
                                    next_car, prev_car = self.getneighbors(vehicle=vehicle,
                                                                           dst_lane=vehicle.lane - 1)

                                    if ((next_car is not None and prev_car is not None) and
                                            (next_car.info.type == 0 and prev_car.info.type == 0) and
                                            (next_car.vel_h > 90 and prev_car.vel_h > 90)):

                                        if self.canshift(vehicle=vehicle, dst_lane=vehicle.lane - 1):
                                            second_control_car_ls_tmp.append(vehicle)

                        elif vehicle.lane == 3:
                            pass

                dc.set_min_vel(id=vehicle.id, vel=vehicle.vel)

                vehicle.update_car(time=time)

            if not second_control_car_ls_tmp == [] and len(lm.second_control_car_ls) < lm.second_control_car_limit:
                check_car = second_control_car_ls_tmp[-1]
                check_car.shift_begin(shift_lane_to=check_car.lane - 1, time=time)
                check_car.change_vd(use_base_station=lm.use_base_station, lane=1)
                check_car.info.mode = 2
                lm.second_control_car_ls.append(check_car)
                self.second_ct_ls.append(check_car.id)

            if time % self.interval == 0:
                self.vehlog.append(lm.run_vehicle_ls)
            lm.generate_vehicle(dc=dc, time=time)
            lm.remove_car()

    def save(self, interval, seed, dir_name) -> None:
        vehlog = self.vehlog
        lm = self.lm
        time_max = int(self.TIME_MAX / 10)
        dc = self.dc

        path = create_path(seed=seed, lm=lm, dir_name=dir_name)
        wb = Workbook()
        # create_info_sheet(wb=wb, lm=lm, time_max=time_max)

        # create_lane_vel_sheet(wb=wb, vehlog=vehlog, lm=lm, time_max=time_max, interval=interval)
        create_merging_info_sheet(wb=wb, vehlog=vehlog, dc=dc, lm=lm, time_max=time_max)
        create_visual_sheet(wb=wb, vehlog=vehlog, lm=lm, time_max=time_max)  # 可視化
        create_log_sheet(wb=wb, vehlog=vehlog, time_max=time_max)
        create_avg_vel_log(wb=wb, vehlog=vehlog, lm=lm)
        if not self.second_ct_ls == []:
            create_avg_vel_log(wb=wb, vehlog=vehlog, lm=lm, id_ls=self.second_ct_ls, sheet_title="制御車両平均速度")

        # create_avg_vel_log(wb=wb, vehlog=vehlog, lm=lm,
        #                    id_ls=[155, 209, 218, 221, 233, 256, 317, 342, 387, 452, 459, 472, 542, 571, 612, 645, 693],
        #                    sheet_title="制御車両平均速度")
        # time_vel_sheet(wb, vehlog, lm.car_max, time_max, interval * 10)
        # time_avgvel_sheet(wb, vehlog, lm.car_max, time_max, interval)
        # moving_avg_sheet(wb=wb, vehlog=vehlog, lm=lm, time_max=time_max, interval=interval)
        # tracking_log(wb=wb, vehlog=vehlog, id_list=self.second_ct_ls, time_max=time_max)
        deceleration_log_sheet(dc=dc, wb=wb, lm=lm)
        if not lm.use_base_station == 0:
            lane_penetration_log(wb=wb, vehlog=self.vehlog, lm=lm, time_max=time_max)
        print(self.second_ct_ls)
        print(path + " を保存中...")
        wb.save(path)
        print("保存終了")

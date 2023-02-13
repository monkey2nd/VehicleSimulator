from datetime import datetime

import result
from Class_dir.Controller import Controller
from Class_dir.LaneChangeMemo import LaneChangeMemo
from pathlib import Path
from cal import simulation


def sim(car_max, merging_ratio, penetration, ego, seed, dir_path, q_lane0, interval, controller: Controller,
        second_ctrl_ls):
    if penetration == 0:
        merging_ratio = 0
    else:
        merging_ratio = penetration
    return simulation(veh_max=car_max, q_lane0=q_lane0, merging_ratio=merging_ratio, penetration=penetration, ego=ego,
                      seed=seed, dir_path=dir_path, interval=interval, controller=controller,
                      second_ctrl_ls=second_ctrl_ls)


if __name__ == "__main__":

    # veh_max_ls = [650, 700]
    # penetration_ls = [0, 0.05, 0.1, 0.2, 0.3]
    # merging_ratio_ls = [0.5]  # ** 合流車両の普及率(0-1)
    # seed_ls = range(10)
    # q_lane0_ls = [50, 80]

    veh_max_ls = [600, 650, 700]
    penetration_ls = [0, 0.05, 0.1, 0.2, 0.3]
    merging_ratio_ls = [0.5]
    seed_ls = range(10)
    q_lane0_ls = [50]
    ego_ls = [0]
    # penetration==0用のcfg
    default_cfg = {"speed_control": False, "distance_control": False, "lc_control": False, "merging_control": False}
    controller_cfgs = [
        # {"speed_control": False, "distance_control": True, "lc_control": "right", "merging_control": True},
        {"speed_control": False, "distance_control": True, "lc_control": False, "merging_control": True}
        ]

    sim_time = 1  # ? シミュレーションを行っている回数

    sim_time_max = 0
    sim_time_max += len(veh_max_ls) * len(merging_ratio_ls) * len(seed_ls) * len(q_lane0_ls) * len(ego_ls) \
                    * len([_ for _ in penetration_ls if _ != 0]) * len(controller_cfgs)
    if 0 in penetration_ls:
        sim_time_max += len(veh_max_ls) * len(merging_ratio_ls) * len(seed_ls) * len(q_lane0_ls) * len(ego_ls)
    print("シミュレーション予定回数：", sim_time_max)

    now = datetime.now()
    # ? 保存するディレクトリ名
    tmp_dir_name = input("フォルダ名を指定する：")
    dir_path = Path().cwd() / "Data_dir"
    if not tmp_dir_name == "":
        dir_path /= tmp_dir_name
    else:
        dir_path /= str(now.month).zfill(2) + str(now.day).zfill(2) + "_" + str(now.hour).zfill(2) \
                    + str(now.minute).zfill(2) + str(now.second).zfill(2)
    interval_log = 10
    lc_memo = LaneChangeMemo()
    for merging_ratio in merging_ratio_ls:
        for q_lane0 in q_lane0_ls:
            for veh_max in veh_max_ls:
                for penetration in penetration_ls:
                    for ego in ego_ls:
                        for seed in seed_ls:
                            if penetration == 0:
                                controller = Controller(**default_cfg)
                                print("実行中... " + str(sim_time) + "/" + str(sim_time_max))
                                second_ctrl_id_ls_tmp = []
                                sim(car_max=veh_max,
                                    merging_ratio=merging_ratio,
                                    penetration=penetration,
                                    ego=ego,
                                    seed=seed,
                                    dir_path=dir_path,
                                    q_lane0=q_lane0,
                                    interval=interval_log,
                                    controller=controller,
                                    second_ctrl_ls=second_ctrl_id_ls_tmp)
                                sim_time += 1
                            else:
                                for ctl_cfg in controller_cfgs:
                                    controller = Controller(**ctl_cfg)
                                    print("実行中... " + str(sim_time) + "/" + str(sim_time_max))
                                    second_ctrl_id_ls = []
                                    if not ctl_cfg["lc_control"]:
                                        second_ctrl_id_ls = lc_memo.get(veh_max=veh_max, merging_ratio=merging_ratio,
                                                                        seed=seed, q_lane0=q_lane0, ego=ego,
                                                                        penetration=penetration)

                                    second_ctrl_id_ls = sim(car_max=veh_max,
                                                            merging_ratio=merging_ratio,
                                                            penetration=penetration,
                                                            ego=ego,
                                                            seed=seed,
                                                            dir_path=dir_path,
                                                            q_lane0=q_lane0,
                                                            interval=interval_log,
                                                            controller=controller,
                                                            second_ctrl_ls=second_ctrl_id_ls)
                                    if controller.lc_control_right:
                                        lc_memo.set(veh_max=veh_max, merging_ratio=merging_ratio, seed=seed,
                                                    q_lane0=q_lane0, ego=ego, penetration=penetration,
                                                    id_ls=second_ctrl_id_ls)
                                    sim_time += 1

    result.make_result(dir_path=dir_path, penetration_ls=penetration_ls, car_max_ls=veh_max_ls, seed_ls=seed_ls,
                       ctrl_cfgs=controller_cfgs, merging_ls=q_lane0_ls)
    # line.notify()
    print("終了")

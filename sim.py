from datetime import datetime

from Class_dir.Controller import Controller
from Class_dir.LaneChangeMemo import LaneChangeMemo
from cal import simulation


def sim(car_max, merging_ratio, penetration, ego, seed, dir_name, q_lane0, interval, controller: Controller,
        second_ctrl_ls):
    if penetration == 0:
        merging_ratio = 0
    return simulation(veh_max=car_max, q_lane0=q_lane0, merging_ratio=merging_ratio, penetration=penetration, ego=ego,
                      seed=seed, dir_name=dir_name, interval=interval, controller=controller,
                      second_ctrl_ls=second_ctrl_ls)


if __name__ == "__main__":
    now = datetime.now()
    # ? 保存するディレクトリ名
    dir_name = str(now.month).zfill(2) + str(now.day).zfill(2) + "_" + str(now.hour).zfill(2) \
               + str(now.minute).zfill(2) + str(now.second).zfill(2)
    print("フォルダ名を指定する：", end="")
    tmp_dir_name = input()
    if not tmp_dir_name == "":
        dir_name = tmp_dir_name

    # car_max_ls = [600, 650, 550]  # ? 本線車両数
    # penetration_ls = [0.3, 0.5, 0.7]  # ? 本線の自動運転車両割合(0~1)（0にすると手動運転車両のみになる）
    # merging_ratio_ls = [40, 60]  # ? 合流車両の自動運転車両割合(0~1)
    # seed_ls = [1, 11]  # ? シード値

    # **TESTZORN
    # car_max_ls = range(450, 550 + 1, 50)
    # car_max_ls = range(500, 601, 50)
    # car_max_ls = [750]
    # todo veh_max_lsにて車両数を増やし事故が発生するパターンを確認するまた手動運転車両の挙動についても確認
    # todo 合流した車両が合流後希望速度20/3.6+されてしまっている => control_mode と　mode 使い分けないと難しいかも(一応終了)
    # todo 乱数の種類を増やしたうえで結果を出す
    # todo lc制御無しのほうが結果が良くなってしまっている訳を可視化で確認(10%において結果が出すぎている）
    # todo 合流車両に対して各制御方式においてどの程度自動運転車両が対応しているか

    veh_max_ls = [700]

    penetration_ls = [0, 0.1, 0.3]

    merging_ratio_ls = [0.5]  # ** 合流車両の普及率(0-1)

    # seed_ls = range(10)
    seed_ls = [11]

    q_lane0_ls = [50, 80]

    ego_ls = [0]
    default_cfg = {"speed_control": False, "distance_control": False, "lc_control": False,
                   "merging_control": False}  # penetration==0用のcfg
    controller_cfgs = [{"speed_control": False, "distance_control": True, "lc_control": True, "merging_control": True},
                       {"speed_control": False, "distance_control": True, "lc_control": False, "merging_control": True}]

    sim_time = 1  # ? シミュレーションを行っている回数

    sim_time_max = 0

    sim_time_max += len(veh_max_ls) * len(merging_ratio_ls) * len(seed_ls) * len(q_lane0_ls) * len(ego_ls) \
                    * len([_ for _ in penetration_ls if _ != 0]) * len(controller_cfgs)
    if 0 in penetration_ls:
        sim_time_max += len(veh_max_ls) * len(merging_ratio_ls) * len(seed_ls) * len(q_lane0_ls) * len(ego_ls)

    interval_log = 10  # (0.1s)
    lc_memo = LaneChangeMemo()

    for veh_max in veh_max_ls:
        for penetration in penetration_ls:
            for merging_ratio in merging_ratio_ls:
                for ego in ego_ls:
                    for seed in seed_ls:
                        for q_lane0 in q_lane0_ls:
                            if penetration == 0:
                                controller = Controller(**default_cfg)
                                print("実行中... " + str(sim_time) + "/" + str(sim_time_max))
                                second_ctrl_id_ls_tmp = []
                                sim(car_max=veh_max,
                                    merging_ratio=merging_ratio,
                                    penetration=penetration,
                                    ego=ego,
                                    seed=seed,
                                    dir_name=dir_name,
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
                                                            dir_name=dir_name,
                                                            q_lane0=q_lane0,
                                                            interval=interval_log,
                                                            controller=controller,
                                                            second_ctrl_ls=second_ctrl_id_ls)
                                    if controller.lc_control:
                                        lc_memo.set(veh_max=veh_max, merging_ratio=merging_ratio, seed=seed,
                                                    q_lane0=q_lane0, ego=ego, penetration=penetration,
                                                    id_ls=second_ctrl_id_ls)
                                    sim_time += 1

    # result.make_result(dir_name=dir_name, penetration_ls=penetration_ls, car_max_ls=veh_max_ls, seed_ls=seed_ls,
    #                    ctrl_cfgs=controller_cfgs)
    # line.notify()
    print("終了")

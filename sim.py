from datetime import datetime

import Line_notification as line
from cal import simulation


def sim(CAR_MAX, merging_ratio, penetration, ego, seed, dir_name, q_lane0, interval):
    def calculate(CAR_MAX,
                  merging_ratio,  # ?制御車両割合
                  penetration,
                  ego,
                  q_lane0,  # ? 合流車線交通量
                  seed,  # ?シード値
                  dir_name,
                  interval,
                  time_max=600,  # ?シミュレーションを行う時間の長さ[s]
                  ):
        simulation(time_max,
                   CAR_MAX,
                   q_lane0,
                   merging_ratio,
                   penetration,
                   ego,
                   seed,
                   dir_name,
                   interval)

    # ####シミュレーション設定#####
    # calculate(q_lane0=50, q_lane2=280, q_lane3=200, merging_ratio=merging_ratio, penetration=penetration, seed=seed, dir_name=dir_name)

    calculate(CAR_MAX=CAR_MAX, merging_ratio=merging_ratio, penetration=penetration, ego=ego, q_lane0=q_lane0,
              seed=seed,
              dir_name=dir_name, interval=interval)


if __name__ == "__main__":
    now = datetime.now()
    # ? 保存するディレクトリ名
    dir_name = str(now.month).zfill(2) + str(now.day).zfill(2) + "_" + str(now.hour).zfill(2) + str(now.minute).zfill(
        2) + str(now.second).zfill(2)
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
    car_max_ls = [700]

    penetration_ls = [0]

    merging_ratio_ls = [0]  # ** 合流車両の普及率(0-1)

    # seed_ls = range(10)
    seed_ls = [11]

    q_lane0_ls = [50]

    ego_ls = [0]

    sim_time = 1  # ? シミュレーションを行っている回数

    sim_time_max = len(car_max_ls) * len(penetration_ls) * len(merging_ratio_ls) * len(seed_ls) * len(q_lane0_ls) * len(
        ego_ls)
    interval_log = 10  # (0.1s)
    # todo 各制御ごとに制御オプションを追加
    for CAR_MAX in car_max_ls:
        for penetration in penetration_ls:
            for merging_ratio in merging_ratio_ls:
                for ego in ego_ls:
                    for seed in seed_ls:
                        for q_lane0 in q_lane0_ls:
                            print("実行中... " + str(sim_time) + "/" + str(sim_time_max))
                            sim(CAR_MAX=CAR_MAX,
                                merging_ratio=merging_ratio,
                                penetration=penetration,
                                ego=ego,
                                seed=seed,
                                dir_name=dir_name,
                                q_lane0=q_lane0,
                                interval=interval_log)
                            sim_time += 1

    # result.make_result(dir_name=dir_name, penetration_ls=penetration_ls, car_max_ls=car_max_ls, seed_ls=seed_ls)
    line.notify()
    print("終了")
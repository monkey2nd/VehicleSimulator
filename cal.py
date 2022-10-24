import random

from Class_dir.RoadClass import Road


def simulation(
        CAR_MAX,  # 最大車両数
        q_lane0,  # 加速車線交通量
        merging_ratio,  # 制御車両比率
        penetration,  # 普及率
        ego,  # ego車両割合
        seed: int,  # シード値
        dir_name,  # ディレクトリ名
        interval,  # logの保存間隔
        controller,
        TIME_MAX=600,  # シミュレーション時間
):
    # ** 初期宣言部分開始
    print("パラメータを初期化中")
    random.seed(seed)  # ! 必ず一番上に記載しておくこと
    road = Road(time_max=TIME_MAX, interval=interval, controller=controller)
    road.lm_init(car_max=CAR_MAX, q_lane0=q_lane0, merging_ratio=merging_ratio, penetration=penetration, ego=ego,
                 seed=seed)
    road.car_init()
    road.change_time_max()
    print("初期化終了")

    road.simulation()

    road.save(interval=10, seed=seed, dir_name=dir_name)

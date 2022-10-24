from .VehicleClass import Vehicle


# ? 特殊な車両クラス
# ? 車線変更先に前方車両がないときに目標とする車両クラス


class Invisible_Vehicle(Vehicle):
    def __init__(self) -> None:
        self.id: int = 0  # 0ID代入
        self.front = 9999  # 1前方位置代入
        self.lane = 1  # 3車線代入
        self.vel = 120 / 3.6  # 4速度代入
        self.accl = 0  # 5加速度代入
        self.distance = 0  # 6車間距離代入
        self.delta_v = 0  # 7相対速度
        self.front_car: Vehicle = None  # 8 前方車両
        self.back_car: Vehicle = None  # 9 後方車両
        self.target_car: Vehicle = None  # 10 目標車両
        self.shift_lane = 0  # 11 車線変更してる途中かどうか
        self.shift_lane_to = 0  # 12 どこの車線に変更しようとしてるか
        self.shift_begin = 0  # 13 車線変更開始時間
        self.shift_distance_go: float = 0  # 14 車線変更先車間距離
        self.shift_id_go = -1  # 15 車線変更先前方車両ID

class Controller:
    def __init__(self):
        self.speed_control = False  # 速度制御
        self.distance_control = True  # 車間距離制御
        self.lc_control = True  # 車線変更制御
        self.merging_control = True  # 合流制御

    @property
    def use_control(self):
        if True in self.__dict__.values():
            return True
        else:
            return False

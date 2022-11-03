class Controller:
    def __init__(self, **kwargs):
        self.speed_control: bool = kwargs["speed_control"]  # 速度制御
        self.distance_control: bool = kwargs["distance_control"]  # 車間距離制御
        self.lc_control: bool = kwargs["lc_control"]  # 車線変更制御
        self.merging_control: bool = kwargs["merging_control"]  # 合流制御

    def dont_use_control(self):
        for control_key in self.__dict__:
            self.__dict__[control_key] = False

    @property
    def use_control(self) -> bool:
        if True in self.__dict__.values():
            return True
        else:
            return False

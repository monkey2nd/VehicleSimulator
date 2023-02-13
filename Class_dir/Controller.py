import warnings


class Controller:
    def __init__(self, **kwargs):
        self.speed_control: bool = kwargs["speed_control"]  # 速度制御
        self.distance_control: bool = kwargs["distance_control"]  # 車間距離制御
        self.merging_control: bool = kwargs["merging_control"]  # 合流制御
        if kwargs["lc_control"] is not False:
            if kwargs["lc_control"] == "right":
                self.lc_control_right = True
                self.lc_control_left = False
            elif kwargs["lc_control"] == "left":
                self.lc_control_left = True
                self.lc_control_right = False
            else:
                warnings.warn("An inappropriate lc_control option was inputted")
        else:
            self.lc_control_right = False
            self.lc_control_left = False

    def dont_use_control(self):
        for control_key in self.__dict__:
            self.__dict__[control_key] = False

    @property
    def use_control(self) -> bool:
        if True in self.__dict__.values():
            return True
        return False

    @property
    def use_lc_control(self) -> bool:
        if self.lc_control_right or self.lc_control_left:
            return True
        return False

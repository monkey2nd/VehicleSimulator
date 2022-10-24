class CommunicationData:
    def __init__(self) -> None:
        self.csp = 0  # * 車両の通信位置等の情報を記
        self.cep = 0

    def set_data(self, csp=None, cep=None) -> None:
        if csp is not None:
            self.csp = csp
        if cep is not None:
            self.cep = cep


class DecelerationData:
    def __init__(self) -> None:
        self.min_vel = float("infinity")
        self.v_init = 0

    @property
    def v_diff(self):
        return self.v_init - self.min_vel

    @property
    def v_diff_h(self):
        return self.v_diff * 3.6

    @property
    def min_vel_h(self):
        return self.min_vel * 3.6

    @property
    def v_init_h(self):
        return self.v_init * 3.6

    def __set_min_vel(self, min_vel):
        self.min_vel = min_vel

    def set_min_vel(self, vel):
        if self.min_vel > vel:
            self.__set_min_vel(min_vel=vel)

    def set_v_init(self, v_init):
        self.v_init = v_init


class DataCollect:
    def __init__(self, car_max) -> None:
        self.cd_ls = [CommunicationData() for _ in range(car_max)]  # ? 車両の通信位置等の情報を記録
        self.dece_ls = [DecelerationData() for _ in range(car_max)]

    def set_cd(self, id, csp=None, cep=None) -> None:
        self.cd_ls[id].set_data(csp=csp, cep=cep)

    def get_cd(self, id):
        return self.cd_ls[id]

    def set_min_vel(self, id, vel):
        self.dece_ls[id].set_min_vel(vel=vel)

    def set_v_init(self, id, v_init):
        self.dece_ls[id].set_v_init(v_init=v_init)

    def get_v_diff(self, id):
        return self.dece_ls[id].v_diff

    def get_v_diff_h(self, id):
        return self.dece_ls[id].v_diff_h

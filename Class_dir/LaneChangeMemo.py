from __future__ import annotations

from typing import Dict, List


class LaneChangeMemo:
    """
    車線変更制御により車線変更した車両idリストを記録しておき
    車線変更制御を行わなかったシミュレーションに渡すクラス
    """

    def __init__(self):
        self.lc_memo: Dict[str, List] = {}

    @staticmethod
    def get_key(veh_max, merging_ratio, seed, q_lane0, ego, penetration) -> str:
        return str(veh_max) + str(merging_ratio) + str(seed) + str(q_lane0) + str(ego) + str(penetration)

    def set(self, veh_max, merging_ratio, seed, q_lane0, ego, penetration, id_ls: list):
        key = self.get_key(veh_max, merging_ratio, seed, q_lane0, ego, penetration)
        self.lc_memo[key] = id_ls

    def get(self, veh_max, merging_ratio, seed, q_lane0, ego, penetration) -> List | None:
        key = self.get_key(veh_max, merging_ratio, seed, q_lane0, ego, penetration)
        if key in self.lc_memo.keys():
            return self.lc_memo[key]
        else:
            return None

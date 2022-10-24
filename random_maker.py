import random


def generate_random(per) -> int:
    return 1 if per > random.random() else 0


def vd_make(min_vel: int, max_vel: int) -> int:
    return round(random.uniform(min_vel / 3.6, max_vel / 3.6), 2)


def generate_shifttime():
    return random.randint(1, 20)


def get_clvd(min_vel=3, max_vel=10):
    return round(random.uniform(min_vel / 3.6, max_vel / 3.6), 2)






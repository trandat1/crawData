import time
from random import uniform


def human_sleep(a: float = 3, b: float = 8):
    time.sleep(uniform(a, b))


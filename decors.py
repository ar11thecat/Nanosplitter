from functools import wraps
import os
import time
from typing import Callable


def timeit(logger, separate=False) -> Callable:
    def timeit(f: Callable) -> Callable:
        @wraps(f)
        def inner(*args, **kwargs):
            start = time.time()
            z = f(*args, **kwargs)
            finish = time.time()
            if separate:
                print(f"{'- '*(os.get_terminal_size().columns // 2)}")
            logger.info(f"'{f.__name__.upper()}' took {(finish - start):.3f} secs")
            return z
        return inner
    return timeit


def embellish(logger, message='', prfx='', appx='') -> Callable:
    def embellish(f: Callable) -> Callable:
        @wraps(f)
        def inner(*args, **kwargs):
            print(prfx, end='')
            logger.info(f"Applying '{f.__name__.upper()}': {message}")
            z = f(*args, **kwargs)
            print(appx, end='')
            return z
        return inner
    return embellish

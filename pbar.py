import math
import time

from . import utils as u


class PBar:

    def __init__(self,
                 unit_type: str,
                 refresh=0.1,
             ):
        self.i = 0
        self.unit_type = unit_type
        self.refresh = refresh
        self.tick = 0
        self.start = None
        self.length = 50


    def make(self, total: int):
        self.total = total
        self.start = time.time()
        self._render(0)


    def add(self, a: int):
        self.i += a
        now = time.time()
        elapsed = now - self.start

        if (curr_tick := elapsed // self.refresh) != self.tick:
            self.tick = curr_tick
            self._render(elapsed)

        if self.i == self.total:
            self._final(elapsed)
        

    def _render(self, elapsed: int):
        time_left = elapsed * (self.total - self.i) / self.i if self.i is not 0 else 0
        chunks = (self.length * self.i) // self.total

        print(f"[{"="*chunks}>{" "*(self.length - chunks)}] "\
              f"{u.unit(self.i, self.unit_type)} / {u.unit(self.total, self.unit_type)} "\
              f"Remaining time: {u.unit(time_left, "time")}"\
              "    ",
              end='\r')

    def _final(self, elapsed: int):
        
        print(f"[{"="*self.length}>] "\
              f"{u.unit(self.i, self.unit_type)} / {u.unit(self.total, self.unit_type)} "\
              f"Total time: {u.unit(elapsed, "time")}"\
              "    ")

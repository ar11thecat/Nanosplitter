import math
from pathlib import Path
import time


def find_exts(dir: Path, exts: list[str]) -> list[Path]:

    find = []

    for d in dir.iterdir():
        if not all(not d.name.endswith(ext) for ext in exts):
            find.append(d)

    return find


def find_exts_rec(dir: Path, exts: list[str]) -> list[Path]:

    find = []

    for d in dir.iterdir():
        if d.is_dir():
            find.extend(find_exts_rec(dir=d, exts=exts))
        else:
            if not all(not d.name.endswith(ext) for ext in exts):
                find.append(d)

    return find


def unit(count: int, type: str) -> str:

    sign = True if count >= 0 else False
    count = abs(count)

    unit = {
        "bin": [("B", "KB", "MB", "GB", "TB"), 1024,],
        "dec": [("", "K", "M", "B", "T"), 1000,],
        "time": [("s", "m", "h"), 60],
    }

    if count == 0:
        return "0" + unit[type][0][0]

    log_magnitude = max(
        min(
            int(math.floor(math.log(count, unit[type][1]))),
            len(unit[type][0]) - 1,
        ),
        0,
    )
    lin_magnitude = int(math.pow(unit[type][1], log_magnitude))
    measure = count / lin_magnitude

    return f"{'-' if not sign else ''}{measure:.1f}{unit[type][0][log_magnitude]}"


def make_progress_bar(total: int, type: str, refresh=0.1):

    start_time = time.time()
    i = 0

    tick = 0

    length = 50
    chunk = total // length

    print()
    
    def progress_bar(add=0, assign=0, finish=False):
        nonlocal i
        nonlocal tick

        elapsed = time.time() - start_time
        i += add
        i = max(i, assign) # makes sure the bar never goes back

        if i <= total:

            if math.floor(elapsed/refresh) != tick:
                tick = math.floor(elapsed/refresh)
                chunks = i // chunk
                remaining_time = elapsed * (total-i) / (i)

                print(f"\r[{"="*chunks}>{" "*(length-chunks)}] "\
                      f"{unit(i, type)} / {unit(total, type)} "\
                      f"Remaining time: {unit(remaining_time, "time")}"\
                      "    ",
                      end='')

            if i == total or finish:
                print(f"\r[{"="*length}>] "\
                      f"{unit(i, type)} / {unit(total, type)} "\
                      f"Total time: {unit(elapsed, "time")}"\
                      "    ",
                      end='')
                print('\n')
                return

    return progress_bar

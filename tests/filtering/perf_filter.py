import cProfile
import functools
import io
import multiprocessing
import pstats
import re

import sheraf
from ZODB.DemoStorage import DemoStorage

# ------------------------------------------------------
# Models
# ------------------------------------------------------


class A1(sheraf.Model):
    table = "a1_objects"
    x1 = sheraf.SimpleAttribute()


# class A1I(sheraf.Model):
#     table = "a1i_objects"
#     x1 = sheraf.SimpleAttribute().index()


# ------------------------------------------------------
# Profiling functions
# ------------------------------------------------------


def init_data(clazz, max_data):
    with sheraf.connection(commit=True):
        for i in range(0, max_data):
            clazz.create(x1=i)


def profiled_filter(clazz, filter_value, do_something=lambda _: None):
    profile = cProfile.Profile()
    with sheraf.connection():
        if callable(filter_value):
            f = clazz.filter(filter_value)
        else:
            f = clazz.filter(x1=filter_value)
        profile.enable()
        [do_something(data) for data in f]
        profile.disable()

    s = io.StringIO()
    ps = pstats.Stats(profile, stream=s)
    ps.strip_dirs().sort_stats("cumtime").print_stats(
        1
    )  # Python3+ : pstats.SortKey.CUMULATIVE
    result = s.getvalue()
    first_line = result.split("\n")[0]
    ncalls, npcalls, cumtime, = re.split(
        r"[^0-9.]+", first_line
    )[1:-1]
    return cumtime


def profiled_filter_with_demostorage(numdata, clazz, filter_value):
    sheraf.Database(storage=DemoStorage(name="demo"))
    init_data(clazz, numdata)
    result = profiled_filter(clazz, filter_value)
    nzeros = str(numdata).count("0")
    print(f"10^{nzeros} objects : {result} secs")
    return (f"10^{nzeros}", result)


def profiled_filter_bench(clazz, filter_value, max_units=5):
    args = [
        10**pos - (10 ** (pos - 1) if pos > 1 else 0)
        for pos in range(1, max_units + 1)
    ]
    pool = multiprocessing.Pool(len(args))
    cumtimes = pool.map_async(
        functools.partial(
            profiled_filter_with_demostorage, clazz=clazz, filter_value=filter_value
        ),
        args,
    )
    pool.close()
    pool.join()
    return cumtimes.get()


if __name__ == "__main__":
    import time

    start = time.time()
    print(profiled_filter_bench(A1, 3))
    # profiled_filter_bench(A1, lambda x: x % 3 == 0)
    print("Exec. time (seconds):", time.time() - start)

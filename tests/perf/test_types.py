import threading

import sheraf
import sheraf.types

LENGTH = 100
THREADS = ("A", "B", "C")


def test_threading(self, sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root.list = sheraf.types.LargeList()

    class Writer(threading.Thread):
        def __init__(self, name):
            super().__init__()
            self.failed = False
            self.name = name

        def run(self):
            try:
                with sheraf.connection() as c:
                    for i in range(LENGTH):
                        sheraf.attempt(
                            lambda: c.root.list.append(self.name + str(i)), attempts=10
                        )
            except BaseException as ex:
                self.failed = ex

    writers = [Writer(i) for i in THREADS]
    [w.start() for w in writers]

    [w.join() for w in writers]
    for w in (w for w in writers if w.failed):
        assert not w.failed

    with sheraf.connection() as c:
        assert len(c.root.list) == len(THREADS) * LENGTH
        for name in THREADS:
            for i in range(LENGTH):
                assert str(name) + str(i) in c.root.list

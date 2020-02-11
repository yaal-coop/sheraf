import multiprocessing

from BTrees.OOBTree import OOBTree

import sheraf


class PerfConcurrentDB:
    NUM_PROCESS = 55
    DATABASE_URI = "zeo://localhost:9999"
    PROVOKE_CONFLICTS = True

    @classmethod
    def concurrent_creation(cls):
        class ModelForTest(sheraf.Model):
            table = "ModelForTest"
            status = sheraf.SimpleAttribute()

        first_id = None
        # Create the table if needed:
        database = sheraf.Database(cls.DATABASE_URI)

        try:
            with sheraf.connection(commit=True) as conn:
                if conn.root().get(ModelForTest.table) is None:
                    first_id = ModelForTest.create(status=1)

            def process(uri, barrier):
                sheraf.Database(uri)
                with sheraf.connection(commit=True):
                    ModelForTest.read(first_id.id)
                    barrier.wait()
                    ModelForTest.create(status=1)

            processes = []

            barrier = multiprocessing.Barrier(cls.NUM_PROCESS)

            for i in range(0, cls.NUM_PROCESS):
                processes.append(
                    multiprocessing.Process(
                        target=process, args=(cls.DATABASE_URI, barrier)
                    )
                )

            for i in range(0, cls.NUM_PROCESS):
                processes[i].start()

            for i in reversed(range(0, cls.NUM_PROCESS)):
                processes[i].join(timeout=10)

            for i in range(0, cls.NUM_PROCESS):
                assert 0 == processes[i].exitcode

        finally:
            if cls.PROVOKE_CONFLICTS:
                pass
            else:
                with sheraf.databases.connection(commit=True) as conn:
                    for key in list(conn.root().keys()):
                        del conn.root()[key]
                database.close()


class BTreePerf:
    @classmethod
    def overbalancing(cls):
        t = OOBTree()
        t.update({1: "red", 2: "blue"})


if __name__ == "__main__":
    PerfConcurrentDB.concurrent_creation()
    # BTreePerf.overbalancing()

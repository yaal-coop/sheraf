from unittest import mock

import sheraf


def test_storage():
    from ZODB.DemoStorage import DemoStorage

    demo_storage = DemoStorage(name="demo")

    pool = sheraf.Database(storage=demo_storage)

    with sheraf.connection() as C:
        db = C.db()
        assert db.storage is demo_storage

    pool.close()

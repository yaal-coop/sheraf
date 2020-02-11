import mock

import sheraf


@mock.patch("ZODB.DB")
@mock.patch("sheraf.databases.DemoStorage")
def test_storage_argument(DemoStorage, DB):
    pool = sheraf.Database(storage=DemoStorage(name="demo"))
    pool.close()

    DemoStorage.assert_called_once_with(name="demo")


def test_storage():
    demo_storage = sheraf.databases.DemoStorage(name="demo")

    pool = sheraf.Database(storage=demo_storage)

    with sheraf.connection() as C:
        db = C.db()
        assert db.storage is demo_storage

    pool.close()

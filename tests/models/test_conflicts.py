import multiprocessing

import pytest
import ZODB

import sheraf


@pytest.mark.parametrize(
    "database",
    [
        pytest.lazy_fixture("sheraf_database"),
        pytest.lazy_fixture("sheraf_zeo_database"),
        #    pytest.lazy_fixture("sheraf_pgsql_relstorage_database"),
    ],
)
class TestMonoprocessConflict:
    sheraf_database_extra_kwargs = {"nestable": True}

    def test_empty_model_no_conflict(self, database):
        class MyModel(sheraf.AutoModel):
            pass

        with sheraf.connection(commit=True):
            m = MyModel.create()

        with sheraf.connection(commit=True):
            m1 = MyModel.read(m.id)

            with sheraf.connection(commit=True):
                m2 = MyModel.read(m.id)
                m2.save()

            m1.save()

    def test_same_simple_attribute_same_modification_no_conflict(self, database):
        class MyModel(sheraf.AutoModel):
            something = sheraf.attributes.simples.SimpleAttribute()
            stuff = sheraf.LargeListAttribute(lazy_creation=False)

        with sheraf.connection(commit=True):
            m = MyModel.create()

        with sheraf.connection(commit=True):
            m1 = MyModel.read(m.id)

            with sheraf.connection(commit=True):
                m2 = MyModel.read(m.id)
                m2.something = "YOLO"

            m1.something = "YOLO"

    def test_different_simple_attribute_modification_no_conflict(self, database):
        class MyModel(sheraf.AutoModel):
            something = sheraf.attributes.simples.SimpleAttribute()
            something_else = sheraf.attributes.simples.SimpleAttribute()
            stuff = sheraf.LargeListAttribute(lazy_creation=False)

        with sheraf.connection(commit=True):
            m = MyModel.create()

        with sheraf.connection(commit=True):
            m1 = MyModel.read(m.id)

            with sheraf.connection(commit=True):
                m2 = MyModel.read(m.id)
                m2.something = "YOLO"

            m1.something_else = "YEAH"

    def test_same_simple_attribute_different_modification_conflict(self, database):
        class MyModel(sheraf.AutoModel):
            something = sheraf.attributes.simples.SimpleAttribute()
            stuff = sheraf.LargeListAttribute(lazy_creation=False)

        with sheraf.connection(commit=True):
            m = MyModel.create()
            mid = m.id

        with pytest.raises(ZODB.POSException.ConflictError):
            with sheraf.connection(commit=True):
                m1 = MyModel.read(m.id)

                with sheraf.connection(commit=True):
                    m2 = MyModel.read(m.id)
                    m2.something = "connection 2"

                m1.something = "connection 1"

        with sheraf.connection():
            m = MyModel.read(mid)
            assert "connection 2" == m.something


@pytest.mark.parametrize(
    "database",
    [
        pytest.lazy_fixture("sheraf_zeo_database"),
        #    pytest.lazy_fixture("sheraf_pgsql_relstorage_database"),
    ],
)
class TestMultiprocessConflict:
    def test_empty_model_no_conflict(self, database):
        class ModelForTest(sheraf.AutoModel):
            pass

        def process(uri, model_id, barrier):
            sheraf.Database(uri)

            with sheraf.connection(commit=True):
                m = ModelForTest.read(model_id)
                barrier.wait()
                m.save()

        with sheraf.connection(commit=True):
            m = ModelForTest.create()

        barrier = multiprocessing.Barrier(2)
        process1 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier)
        )
        process2 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier)
        )

        process1.start()
        process2.start()

        process2.join(timeout=10)
        process1.join(timeout=10)

        assert 0 == process1.exitcode
        assert 0 == process2.exitcode

    def test_same_simple_attribute_same_modification_conflict(self, database):
        class ModelForTest(sheraf.AutoModel):
            order = sheraf.SimpleAttribute()
            stuff = sheraf.LargeListAttribute(lazy_creation=False)

        def process(uri, model_id, barrier):
            sheraf.Database(uri)

            with sheraf.connection(commit=True):
                m = ModelForTest.read(model_id)
                barrier.wait()
                m.order = "YOLO"

        with sheraf.connection(commit=True):
            m = ModelForTest.create()

        barrier = multiprocessing.Barrier(2)
        process1 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier)
        )
        process2 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier)
        )

        process1.start()
        process2.start()

        process2.join(timeout=10)
        process1.join(timeout=10)

        assert 0 == process1.exitcode
        assert 0 == process2.exitcode

    def test_different_simple_attribute_modification_no_conflict(self, database):
        class ModelForTest(sheraf.AutoModel):
            something = sheraf.SimpleAttribute()
            something_else = sheraf.SimpleAttribute()
            stuff = sheraf.LargeListAttribute(lazy_creation=False)

        def process(uri, model_id, barrier, queue, lock):
            sheraf.Database(uri)

            with sheraf.connection(commit=True):
                m = ModelForTest.read(model_id)
                barrier.wait()

                with lock:
                    order = queue.get()

                    if order == "first":
                        m.something = "YEAH"

                    elif order == "second":
                        m.something_else = "YOH"

        with sheraf.connection(commit=True):
            m = ModelForTest.create()

        barrier = multiprocessing.Barrier(2)
        lock = multiprocessing.Lock()
        queue = multiprocessing.Queue()
        queue.put("first")
        queue.put("second")
        process1 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier, queue, lock)
        )
        process2 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier, queue, lock)
        )

        process1.start()
        process2.start()

        process2.join(timeout=10)
        process1.join(timeout=10)

        assert 0 == process1.exitcode
        assert 0 == process2.exitcode

    def test_same_simple_attribute_different_modification_conflict(self, database):
        class ModelForTest(sheraf.AutoModel):
            order = sheraf.SimpleAttribute()
            stuff = sheraf.LargeListAttribute(lazy_creation=False)

        def process(uri, model_id, barrier, queue, lock):
            sheraf.Database(uri)

            with sheraf.connection() as conn:
                m = ModelForTest.read(model_id)
                barrier.wait()

                with lock:
                    order = queue.get()
                    m.order = order

                    if order == "first":
                        conn.transaction_manager.commit()

                    elif order == "second":
                        with pytest.raises(ZODB.POSException.ConflictError):
                            conn.transaction_manager.commit()

        with sheraf.connection(commit=True):
            m = ModelForTest.create()

        barrier = multiprocessing.Barrier(2)
        lock = multiprocessing.Lock()
        queue = multiprocessing.Queue()
        queue.put("first")
        queue.put("second")
        process1 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier, queue, lock)
        )
        process2 = multiprocessing.Process(
            target=process, args=(database.uri, m.id, barrier, queue, lock)
        )

        process1.start()
        process2.start()

        process2.join(timeout=10)
        process1.join(timeout=10)

        assert 0 == process1.exitcode
        assert 0 == process2.exitcode

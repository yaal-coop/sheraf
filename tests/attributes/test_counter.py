import multiprocessing

import BTrees
import pytest
import sheraf
import tests
import ZODB


class Model(tests.UUIDAutoModel):
    counter = sheraf.CounterAttribute(default=0)
    useless = sheraf.InlineModelAttribute(
        sheraf.InlineModel(
            foo=sheraf.SimpleAttribute(default="bar", lazy=False),
        ),
        lazy=False,
    )


def test_increment_decrement(sheraf_database):
    with sheraf.connection(commit=True):
        m = Model.create()
        assert 0 == m.counter

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        assert 0 == m.counter
        m.counter.increment(10)
        assert 10 == m.counter

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        assert 10 == m.counter
        m.counter.decrement(10)
        assert 0 == m.counter

    with sheraf.connection():
        m = Model.read(m.id)
        assert 0 == m.counter


def test_assignment(sheraf_database):
    with sheraf.connection(commit=True):
        m = Model.create()

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        m.counter = 10
        assert 10 == m.counter
        assert isinstance(m.counter, sheraf.types.counter.Counter)

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        assert 10 == m.counter

        n = Model.create()
        n.counter = 200
        m.counter = n.counter
        assert 200 == m.counter
        assert isinstance(m.counter, sheraf.types.counter.Counter)

        n.counter.increment(1)
        assert 201 == n.counter
        assert 200 == m.counter

    with sheraf.connection():
        m = Model.read(m.id)
        assert 200 == m.counter


def test_monoprocess_double_increment_no_conflict(sheraf_database):
    sheraf_database.nestable = True

    with sheraf.connection(commit=True):
        m = Model.create()

    with sheraf.connection(commit=True):
        m1 = Model.read(m.id)

        with sheraf.connection(commit=True):
            m2 = Model.read(m.id)
            m2.counter.decrement(10)

        m1.counter.increment(100)

    with sheraf.connection():
        m3 = Model.read(m.id)
        assert 90 == m3.counter


def test_monoprocess_double_assignment_conflict(sheraf_database):
    sheraf_database.nestable = True

    with sheraf.connection(commit=True):
        m = Model.create()

    with pytest.raises(ZODB.POSException.ConflictError):
        with sheraf.connection(commit=True):
            m1 = Model.read(m.id)

            with sheraf.connection(commit=True):
                m2 = Model.read(m.id)
                m2.counter = 10

            m1.counter = 20


def test_monoprocess_assignment_increment_conflict(sheraf_database):
    sheraf_database.nestable = True

    with sheraf.connection(commit=True):
        m = Model.create()

    with pytest.raises(ZODB.POSException.ConflictError):
        with sheraf.connection(commit=True):
            m1 = Model.read(m.id)

            with sheraf.connection(commit=True):
                m2 = Model.read(m.id)
                m2.counter = 10

            m1.counter.increment(100)


@pytest.mark.skip
def test_multiprocessing_conflict_nominal_case(sheraf_zeo_database):
    class Model(tests.UUIDAutoModel):
        counter = sheraf.SimpleAttribute(default=0)

    def process(uri, model_id, barrier, queue, lock, addition):
        sheraf.Database(uri)

        with sheraf.connection() as conn:
            m = Model.read(model_id)

            barrier.wait()
            m.counter += addition

            with lock:
                value = queue.get()
                if value == "first":
                    conn.transaction_manager.commit()

                if value == "second":
                    with pytest.raises(ZODB.POSException.ConflictError):
                        conn.transaction_manager.commit()

    with sheraf.connection(commit=True):
        m = Model.create()

    barrier = multiprocessing.Barrier(2)
    queue = multiprocessing.Queue()
    lock = multiprocessing.Lock()
    queue.put("first")
    queue.put("second")

    process1 = multiprocessing.Process(
        target=process, args=(sheraf_zeo_database.uri, m.id, barrier, queue, lock, 10)
    )
    process2 = multiprocessing.Process(
        target=process, args=(sheraf_zeo_database.uri, m.id, barrier, queue, lock, 100)
    )

    process1.start()
    process2.start()

    process2.join(timeout=10)
    process1.join(timeout=10)

    assert 0 == process1.exitcode
    assert 0 == process2.exitcode

    with sheraf.connection():
        m = Model.read(m.id)
        assert m.counter in (10, 100)


@pytest.mark.skip
def test_multiprocessing_int_conflict_resolution(sheraf_zeo_database):
    class IntModel(tests.UUIDAutoModel):
        counter = sheraf.CounterAttribute()

    def process(uri, model_id, barrier, addition):
        sheraf.Database(uri)

        with sheraf.connection(commit=True):
            m = IntModel.read(model_id)
            assert 0 == m.counter

            barrier.wait()
            m.counter.increment(addition)

    with sheraf.connection(commit=True):
        m = IntModel.create()

    nb_process = 3
    barrier = multiprocessing.Barrier(nb_process)
    processes = [
        multiprocessing.Process(
            target=process, args=(sheraf_zeo_database.uri, m.id, barrier, i)
        )
        for i in range(0, nb_process)
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join(timeout=10)
        assert 0 == process.exitcode

    with sheraf.connection():
        m = IntModel.read(m.id)
        assert sum(i for i in range(0, nb_process)) == m.counter


@pytest.mark.skip
def test_multiprocessing_float_conflict_resolution(sheraf_zeo_database):
    class FloatModel(tests.UUIDAutoModel):
        counter = sheraf.CounterAttribute(default=0.5)

    def process(uri, model_id, barrier, addition):
        sheraf.Database(uri)

        with sheraf.connection(commit=True):
            m = FloatModel.read(model_id)
            barrier.wait()
            m.counter.increment(addition)

    with sheraf.connection(commit=True):
        m = FloatModel.create()

    nb_process = 3
    barrier = multiprocessing.Barrier(nb_process)
    processes = [
        multiprocessing.Process(
            target=process, args=(sheraf_zeo_database.uri, m.id, barrier, i + 0.5)
        )
        for i in range(0, nb_process)
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join(timeout=10)
        assert 0 == process.exitcode

    with sheraf.connection():
        m = FloatModel.read(m.id)
        assert 0.5 + sum(i + 0.5 for i in range(0, nb_process)) == m.counter


class SimpleModel(sheraf.Model):
    table = "model_test_simple_attribute_replacement"
    unique_table_name = False
    counter = sheraf.SimpleAttribute()


class BTreesLengthModel(sheraf.Model):
    table = "model_test_simple_attribute_replacement"
    unique_table_name = False
    counter = sheraf.SimpleAttribute(default=BTrees.Length.Length)


class CounterModel(sheraf.Model):
    table = "model_test_simple_attribute_replacement"
    unique_table_name = False
    counter = sheraf.CounterAttribute()


def test_simple_attribute_replacement(sheraf_database):
    with sheraf.connection(commit=True):
        m = SimpleModel.create()
        m.counter = 100
        assert isinstance(m.counter, int)

    with sheraf.connection(commit=True):
        m = CounterModel.read(m.id)
        assert 100 == m.counter
        assert isinstance(m.counter, sheraf.types.counter.Counter)
        m.counter.increment(10)
        assert 110 == m.counter

    with sheraf.connection():
        m = CounterModel.read(m.id)
        assert 110 == m.counter
        assert isinstance(m.counter, sheraf.types.counter.Counter)


def test_btrees_length_replacement(sheraf_database):
    with sheraf.connection(commit=True):
        m = BTreesLengthModel.create()
        m.counter.set(100)
        assert isinstance(m.counter, BTrees.Length.Length)

    with sheraf.connection(commit=True):
        m = CounterModel.read(m.id)
        assert 100 == m.counter
        assert isinstance(m.counter, sheraf.types.counter.Counter)
        m.counter.increment(10)
        assert 110 == m.counter

    with sheraf.connection():
        m = CounterModel.read(m.id)
        assert 110 == m.counter
        assert isinstance(m.counter, sheraf.types.counter.Counter)

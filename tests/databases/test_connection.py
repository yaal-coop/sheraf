import multiprocessing
import threading

import mock
import pytest
from ZODB.POSException import ConflictError

import sheraf


class AModel(sheraf.AutoModel):
    field = sheraf.SimpleAttribute()


def test_connection(sheraf_database):
    sheraf_database.connection = mock.Mock(side_effect=sheraf_database.connection)

    with sheraf.connection(commit=True):
        sheraf_database.connection.assert_called_with(
            commit=True, cache_minimize=False, _trackeback_shift=2,
        )
        m = AModel.create(field="foo")

    @sheraf.connection()
    def read(mid):
        m = AModel.read(mid)
        assert "foo" == m.field

    read(m.id)
    sheraf_database.connection.assert_called_with(
        commit=False, cache_minimize=False, _trackeback_shift=2,
    )

    @sheraf.connection(commit=True, cache_minimize=True)
    def update(mid):
        m = AModel.read(mid)
        assert "foo" == m.field
        m.field = "bar"

    update(m.id)
    sheraf_database.connection.assert_called_with(
        commit=True, cache_minimize=True, _trackeback_shift=2,
    )

    with sheraf.connection():
        sheraf_database.connection.assert_called_with(
            commit=False, cache_minimize=False, _trackeback_shift=2,
        )

        m = AModel.read(m.id)
        assert "bar" == m.field


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_current_connection(cacheMinimize, sheraf_database):
    assert sheraf.Database.current_connection() is None
    assert sheraf.Database.current_name() is None

    with sheraf.connection() as conn:
        assert sheraf.Database.current_connection() is conn
        assert sheraf.Database.DEFAULT_DATABASE_NAME == sheraf.Database.current_name()

    assert sheraf.Database.current_connection() is None
    assert sheraf.Database.current_name() is None

    with sheraf.connection() as conn:
        assert sheraf.Database.current_connection() is conn
        assert sheraf.Database.DEFAULT_DATABASE_NAME == sheraf.Database.current_name()

    assert sheraf.Database.current_connection() is None
    assert sheraf.Database.current_name() is None


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_without_args(cacheMinimize, sheraf_database):
    with sheraf.connection(commit=True):
        m = AModel.create()

    with sheraf.connection():
        m.field = "yeah"

    with sheraf.connection():
        m = AModel.read(m.id)
        assert not m.field
    assert not cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_without_args_and_with_exception(cacheMinimize, sheraf_database):
    with sheraf.connection(commit=True):
        m = AModel.create()

    try:
        with sheraf.connection():
            m.field = "yeah"
            raise ValueError()
    except ValueError:
        pass

    with sheraf.connection():
        m = AModel.read(m.id)
        assert not m.field
    assert not cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_with_commit(cacheMinimize, sheraf_database):
    with sheraf.connection(commit=True):
        m = AModel.create()

    with sheraf.connection(commit=True):
        m.field = "yeah"

    with sheraf.connection():
        m = AModel.read(m.id)
        assert "yeah" == m.field
    assert not cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_with_commit_and_exception(cacheMinimize, sheraf_database):
    with sheraf.connection(commit=True):
        m = AModel.create()

    try:
        with sheraf.connection(commit=True):
            m.field = "yeah"
            raise ValueError()
    except ValueError:
        pass

    with sheraf.connection():
        m = AModel.read(m.id)
        assert not m.field
    assert not cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_with_cache_minimize(cacheMinimize, sheraf_database):
    with sheraf.connection(cache_minimize=True):
        pass

    assert cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_with_cache_minimize_and_exception(cacheMinimize, sheraf_database):
    try:
        with sheraf.connection(cache_minimize=True):
            raise ValueError()
    except ValueError:
        pass

    assert cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_with_database_name(cacheMinimize, sheraf_database, other_database):
    assert sheraf.Database.get("other_database") != sheraf.Database.get()
    with sheraf.connection(commit=True) as c:
        c.root()["data"] = True
    with sheraf.connection(database_name="other_database") as c:
        assert "data" not in c.root()


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_nested_connections_raise_exception(cacheMinimize, sheraf_database):
    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.ConnectionAlreadyOpened):
            with sheraf.connection():
                pass  # pragma: no cover


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_nested_connections_raise_exception_message(cacheMinimize, sheraf_database):
    with sheraf.connection():
        with pytest.raises(
            sheraf.exceptions.ConnectionAlreadyOpened,
            match="First connection was .* on .*{} at line".format(__file__),
        ):
            with sheraf.connection():
                pass  # pragma: no cover


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_nested_connections_on_two_databases_raise_exception(
    cacheMinimize, sheraf_database
):
    other = sheraf.Database("memory://?database_name=other_database")
    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.ConnectionAlreadyOpened):
            with sheraf.connection(database_name="other_database"):
                pass  # pragma: no cover
    other.close()


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_connection_closed_in_connection_context(cacheMinimize, sheraf_database):
    with sheraf.connection() as connection:
        connection.close()

    class CustomException(Exception):
        pass

    with pytest.raises(CustomException):
        with sheraf.connection(commit=True) as connection:
            connection.close()
            raise CustomException()


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_database_context_manager(cacheMinimize):
    db = sheraf.Database()
    with db.connection() as connection:
        assert sheraf.Database.current_connection() is connection
    db.close()


def test_multithreading_database_connection(sheraf_zeo_database):
    with sheraf.connection(commit=True) as c:
        c.root.list = sheraf.types.LargeList()
        c.root.list.append("main")

    class MyThread(threading.Thread):
        def run(self):
            with sheraf.connection(commit=True) as c:
                c.root.list.append("thread")

    my_thread = MyThread()
    my_thread.start()
    my_thread.join(timeout=10)

    with sheraf.connection() as c:
        assert ["main", "thread"] == list(c.root.list)


def test_multiprocessing_database_connection(sheraf_zeo_database):
    with sheraf.connection(commit=True) as c:
        c.root.list = sheraf.types.LargeList()
        c.root.list.append("main")

    class MyProcess(multiprocessing.Process):
        def __init__(self, uri):
            super().__init__()
            self.uri = uri

        def run(self):
            with pytest.raises(KeyError):
                sheraf.Database.get()

            db = sheraf.Database(self.uri)
            with sheraf.connection(commit=True) as conn:
                conn.root.list.append("process")
            db.close()

    my_process = MyProcess(sheraf_zeo_database.uri)
    my_process.start()
    my_process.join(timeout=10)
    assert 0 == my_process.exitcode

    with sheraf.connection() as c:
        assert ["main", "process"] == list(c.root.list)


class TestMultipleConnections:
    sheraf_database_extra_kwargs = {"nestable": True}

    def test_data_reading(self, sheraf_database):
        with sheraf.connection(commit=True) as c:
            c.root()["data"] = True

        with sheraf.connection() as c1:
            assert c1.root()["data"]

            with sheraf.connection(commit=True) as c2:
                c2.root()["data"] = False

            assert c1.root()["data"]

        with sheraf.connection() as c3:
            assert not c3.root()["data"]

    def test_transaction_managers(self, sheraf_database):
        with sheraf.connection() as c1:
            with sheraf.connection() as c2:
                assert c1.transaction_manager != c2.transaction_manager

    def test_conflict(self, sheraf_database):
        with sheraf.connection(commit=True) as c:
            c.root()["data"] = sheraf.types.SmallList()

        with pytest.raises(ConflictError):
            with sheraf.connection(commit=True) as c1:
                c1.root()["data"].append("connection1")

                with sheraf.connection(commit=True) as c2:
                    c2.root()["data"].append("connection2")

    def test_get_current_connection_nested(
        self, sheraf_database, other_nested_database
    ):
        with sheraf.connection(sheraf.Database.DEFAULT_DATABASE_NAME) as conn_default:
            assert (
                sheraf.Database.DEFAULT_DATABASE_NAME == sheraf.Database.current_name()
            )
            assert conn_default == sheraf.Database.current_connection()

            with sheraf.connection("other_nested_database") as conn_other:
                assert "other_nested_database" == sheraf.Database.current_name()
                assert conn_other == sheraf.Database.current_connection()

            assert (
                sheraf.Database.DEFAULT_DATABASE_NAME == sheraf.Database.current_name()
            )
            assert conn_default == sheraf.Database.current_connection()


def test_last_connection(sheraf_database):
    with sheraf.connection() as conn:
        assert conn == sheraf.Database.last_connection(sheraf_database)

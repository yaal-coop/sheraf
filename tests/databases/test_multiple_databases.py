import mock
import pytest

import sheraf
from sheraf.exceptions import ObjectNotFoundException
import tests


def test_connection_returned_by_context_manager_connection(
    sheraf_database, other_nested_database
):
    with sheraf.connection() as connection:
        assert sheraf.Database.current_connection() is connection
        assert connection.db() is sheraf.Database.get().db
        assert (
            sheraf.Database.current_connection(sheraf.Database.DEFAULT_DATABASE_NAME)
            is connection
        )

        other_connection = connection.get_connection("other_nested_database")
        assert connection != other_connection
        assert (
            sheraf.Database.current_connection("other_nested_database")
            is other_connection
        )
        assert other_connection.db() is other_nested_database.db

    assert not connection.opened
    assert not other_connection.opened


def test_get_current_connection_successive(sheraf_database, other_nested_database):
    with sheraf.connection() as conn:
        assert sheraf.Database.DEFAULT_DATABASE_NAME == sheraf.Database.current_name()
        assert conn == sheraf.Database.current_connection()

    with sheraf.connection(sheraf.Database.DEFAULT_DATABASE_NAME) as conn_default:
        assert sheraf.Database.DEFAULT_DATABASE_NAME == sheraf.Database.current_name()
        assert conn_default == sheraf.Database.current_connection()

    with sheraf.connection("other_nested_database") as conn_other:
        assert "other_nested_database" == sheraf.Database.current_name()
        assert conn_other == sheraf.Database.current_connection()


def test_commit(sheraf_database, other_nested_database):
    with sheraf.connection(commit=True) as connection:
        connection.root.data = True
        connection.get_connection("other_nested_database").root.data = False

    with sheraf.connection() as connection:
        assert connection.root.data is True
        assert connection.get_connection("other_nested_database").root.data is False


def test_abort(sheraf_database, other_nested_database):
    with sheraf.connection() as connection:
        connection.root.data = True
        connection.get_connection("other_nested_database").root.data = False

    with sheraf.connection() as connection:
        assert "data" not in connection.root()
        assert "data" not in connection.get_connection("other_nested_database").root()


def test_default_database(sheraf_database, other_nested_database):
    class Model(tests.UUIDAutoModel):
        anything = sheraf.SimpleAttribute(lazy=False)

    with sheraf.connection(sheraf.Database.DEFAULT_DATABASE_NAME, commit=True):
        m1 = Model.create()

    with sheraf.connection("other_nested_database", commit=True):
        m2 = Model.create()

    with sheraf.connection(sheraf.Database.DEFAULT_DATABASE_NAME):
        assert Model.read(m1.id)
        with pytest.raises(ObjectNotFoundException):
            Model.read(m2.id)

    with sheraf.connection("other_nested_database"):
        assert Model.read(m2.id)
        with pytest.raises(ObjectNotFoundException):
            Model.read(m1.id)


def test_successive_connections(sheraf_database, other_nested_database):
    class Model(tests.UUIDAutoModel):
        anything = sheraf.SimpleAttribute(lazy=False)

    with sheraf.connection(commit=True):
        campaign = Model.create()

    with sheraf.connection("other_nested_database"):
        Model.create()

    with sheraf.connection():
        campaign.anything = "foobar"


def test_commit_aborted_on_exception(sheraf_database, other_nested_database):
    class CustomException(Exception):
        pass

    try:
        with sheraf.connection(commit=True) as connection:
            connection.root.data = True
            connection.get_connection("other_nested_database").root.data = False
            raise CustomException()

    except CustomException:
        pass

    with sheraf.connection() as connection:
        assert "data" not in connection.root()
        assert "data" not in connection.get_connection("other_nested_database").root()


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_cache_minimize_default_value_false(cacheMinimize, sheraf_database):
    with sheraf.connection():
        pass

    assert not cacheMinimize.called


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_cache_minimize_true_with_one_connection(cacheMinimize, sheraf_database):
    with sheraf.connection(cache_minimize=True):
        pass

    assert cacheMinimize.call_count == 1


@mock.patch("ZODB.Connection.Connection.cacheMinimize")
def test_cache_minimize_true_with_two_connections(
    cacheMinimize, sheraf_database, other_nested_database
):
    with sheraf.connection(cache_minimize=True) as connection:
        connection.get_connection("other_nested_database")

    assert cacheMinimize.call_count == 2

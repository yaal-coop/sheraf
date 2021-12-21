import pytest
import sheraf.exceptions
import tests
from ZODB.POSException import ConflictError


def test_custom_exceptions(sheraf_database):
    with pytest.raises(ZeroDivisionError):
        with sheraf.connection():
            sheraf.attempt(lambda: 1 / 0)

    def my_function(attempts):
        if attempts == []:
            attempts.append(True)
            raise ZeroDivisionError()
        raise IndexError

    with sheraf.connection():
        attempts = []
        with pytest.raises(IndexError):
            sheraf.attempt(
                my_function, args=(attempts,), also_except=(ZeroDivisionError,)
            )


def test_exception_during_callback(sheraf_database):
    def my_function_with_exception():
        raise AttributeError

    with pytest.raises(AttributeError) as conflict:
        with sheraf.connection():
            sheraf.attempt(
                my_function_with_exception, also_except=AttributeError, on_failure=None
            )

    assert "Execution n°1 took" in conflict.value.extra_info
    assert "Execution n°5 took" in conflict.value.extra_info


def test_exception_conflict(sheraf_database):
    sheraf_database.nestable = True

    def my_function_with_exception():
        with sheraf.connection(commit=True) as c2:
            c2.root()["foo"] = "bar"

        # No need to commit this since attempt will do it
        sheraf.Database.current_connection().root()["foo"] = "baz"

    with pytest.raises(ConflictError) as conflict:
        with sheraf.connection():
            sheraf.attempt(my_function_with_exception, on_failure=None)

    assert "Execution n°1 took" in conflict.value.extra_info
    assert "Execution n°5 took" in conflict.value.extra_info


def test_on_failure(sheraf_database):
    def my_function():
        raise ConflictError()

    results = iter(range(2))

    def on_failure(nb_attempt):
        assert nb_attempt == next(results)

    with pytest.raises(ConflictError):
        with sheraf.connection():
            sheraf.attempt(my_function, attempts=3, on_failure=on_failure)

    with pytest.raises(StopIteration):
        next(results)


def test_no_commit(sheraf_database):
    def my_function():
        sheraf.Database.current_connection().root()["foo"] = "bar"

    with sheraf.connection() as conn:
        sheraf.attempt(my_function, commit=lambda: False)
        assert "foo" not in conn.root()


def test_empty_commit(sheraf_database):
    class Model(tests.IntAutoModel):
        pass

    with sheraf.connection():
        m = Model.create()
        sheraf.commit()

    with sheraf.connection():
        assert Model.read(m.id)


def test_commit_no_db():
    with pytest.raises(sheraf.exceptions.NotConnectedException):
        sheraf.commit()

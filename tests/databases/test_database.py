import pytest
import sheraf


def test_repr(sheraf_database):
    assert "<Database database_name='unnamed'>" == str(sheraf_database)

    sheraf_database.nestable = True
    sheraf_database.db_args["read_only"] = True

    assert "<Database database_name='unnamed' ro nestable>" == str(sheraf_database)


def test_already_opened_exception(sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root()["data"] = True

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.ConnectionAlreadyOpened):
            with sheraf.connection():
                pass  # pragma: no cover


def test_reset_database(sheraf_database):
    with sheraf.connection(commit=True) as conn:
        first_dt = conn.root()._p_mtime
        conn.root()["foo"] = "bar"

    sheraf_database.reset()

    with sheraf.connection(commit=True) as conn:
        second_dt = conn.root()._p_mtime

        assert second_dt > first_dt
        assert "foo" not in conn.root()


def test_close_database_in_context_manager(sheraf_database):
    with sheraf.connection():
        sheraf_database.close()


def test_get_or_create():
    with pytest.raises(KeyError):
        sheraf.Database.get()

    db = sheraf.Database.get_or_create()
    assert db == sheraf.Database.get()
    assert db == sheraf.Database.get_or_create()
    db.close()

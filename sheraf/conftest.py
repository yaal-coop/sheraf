import contextlib

import pytest

import sheraf


class Cowboy(sheraf.IntOrderedNamedAttributesModel):
    table = "conftest_people"
    name = sheraf.SimpleAttribute()
    age = sheraf.SimpleAttribute()


@pytest.fixture(autouse=True)
def add_doctest_namespace(doctest_namespace):
    previous_connection = sheraf.connection

    @contextlib.contextmanager
    def magic_connection(*args, **kwargs):
        try:
            sheraf.Database()
        except KeyError:
            pass

        with previous_connection(*args, **kwargs) as connection:
            yield connection

    sheraf.connection = magic_connection
    doctest_namespace["sheraf"] = sheraf
    doctest_namespace["do_amazing_stuff"] = lambda *args, **kwargs: None
    doctest_namespace["Cowboy"] = Cowboy

    yield

    try:
        sheraf.Database.get().close()
    except KeyError:
        pass
    sheraf.connection = previous_connection

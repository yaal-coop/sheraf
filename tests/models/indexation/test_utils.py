import warnings

import sheraf
import tests


def test_reset_index_table(sheraf_database):
    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(foo="bar")
        Model.create(foo="baz")

    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar")
            assert warns[0].category is sheraf.exceptions.IndexationWarning

    with sheraf.connection(commit=True):
        Model.index_table_rebuild("foo")

    with sheraf.connection(commit=True):
        assert 3 == Model.count()

        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar")
            assert not warns


def test_index_table_rebuild(sheraf_database):
    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(foo="bar", bar="bar")
        Model.create(foo="baz", bar="bor")

    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index()
        bar = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar", bar="bur")
            assert warns[0].category is sheraf.exceptions.IndexationWarning
            assert warns[1].category is sheraf.exceptions.IndexationWarning

    with sheraf.connection(commit=True):
        Model.index_table_rebuild()

    with sheraf.connection(commit=True):
        assert 3 == Model.count()

        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar", bar="boo")
            assert not warns

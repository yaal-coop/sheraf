import pytest
import sheraf
import tests


def test_unique_indexation_and_filter_on_wrong_attribute(sheraf_database):
    class Model(tests.UUIDAutoModel):
        an_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        m = Model.create(an_attribute="foo")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["an_attribute"]
        assert {"foo"} == set(index_table)
        assert m.mapping == index_table["foo"]

        with pytest.raises(sheraf.exceptions.InvalidFilterException):
            list(Model.filter(foobar="foo"))


def test_wrong_index_attribute(sheraf_connection):
    with pytest.raises(sheraf.SherafException):

        class ModelA(tests.UUIDAutoModel):
            i = sheraf.Index()

    with pytest.raises(sheraf.SherafException):

        class ModelB(tests.UUIDAutoModel):
            i = sheraf.Index("invalid")

    with pytest.raises(sheraf.SherafException):

        class ModelC(tests.UUIDAutoModel):
            i = sheraf.Index("invalid")

    with pytest.raises(sheraf.SherafException):

        class ModelE(tests.UUIDAutoModel):
            foo = sheraf.SimpleAttribute()
            ok = sheraf.Index(foo)
            i = sheraf.Index(ok)

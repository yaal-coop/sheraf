import itertools

import pytest
import sheraf.models
from BTrees.OOBTree import OOTreeSet
from sheraf.exceptions import InvalidFilterException
from sheraf.exceptions import NotConnectedException
from sheraf.queryset import QuerySet

from .conftest import Cowboy


def test_list(sheraf_connection, m0, m1, m2, m3):
    assert [m0, m1, m2, m3] == Cowboy.all()
    assert [m0, m1, m2, m3] == list(Cowboy.all())


def test_iteration(sheraf_connection, m0, m1, m2, m3):
    qall = Cowboy.all()
    assert m0 == next(qall)
    assert m1 == next(qall)
    assert m2 == next(qall)
    assert m3 == next(qall)

    with pytest.raises(StopIteration):
        next(qall)

    assert [] == qall


def test_comparison(sheraf_connection, m0, m1, m2):
    assert QuerySet() is not None
    assert QuerySet([m0]) == QuerySet([m0])
    assert QuerySet([m0]) == QuerySet(m for m in [m0])
    assert QuerySet([m0]) == QuerySet(OOTreeSet([m0]))
    # assert QuerySet([m0, m1, m2]) == QuerySet(OOTreeSet([m0, m1, m2]))


def test_bool(sheraf_connection, m0):
    assert bool(QuerySet([m0])) is True
    assert bool(QuerySet()) is False
    assert bool(Cowboy.all()) is True
    assert bool(Cowboy.search(size=99)) is False


def test_create(sheraf_connection, m0):
    assert [m0] == Cowboy.filter(age=30)
    assert [] != Cowboy.filter(age=30)

    assert QuerySet([m0]) == Cowboy.filter(age=30)
    assert m0 in Cowboy.filter(age=30)

    res = [m0]
    assert QuerySet(iter(res)) == Cowboy.filter(age=30)
    assert m0 in Cowboy.filter(age=30)


def test_count_all(sheraf_connection, m0, m1, m2, m3):
    qs = Cowboy.all()
    assert qs.count() == 4
    assert qs.count() == 4


def test_len(sheraf_connection, m0, m1, m2, m3):
    qs = Cowboy.all()
    assert len(qs) == 4
    assert len(qs) == 4


def test_count_unindexed_attributes(sheraf_connection, m0, m1, m2, m3):
    qs = Cowboy.filter(age=30)
    assert qs.count() == 3
    assert qs.count() == 3
    assert Cowboy.filter(age=80).count() == 0


def test_count_multiple_indexed_attributes(sheraf_connection, m0, m1, m2, m3):
    qs = Cowboy.search(size=170)
    assert qs.count() == 2
    assert Cowboy.search(size=150).count() == 0


def test_count_unique_indexed_attributes(sheraf_connection, m0, m1, m2, m3):
    qs = Cowboy.search(email="peter@peter.com")
    assert qs.count() == 1
    assert Cowboy.search(email="nobody@nobody.com").count() == 0


def test_repr(sheraf_connection, m0):
    assert str(Cowboy.all()).startswith("<QuerySet model=")
    assert str(QuerySet()) == "<QuerySet>"
    assert str(QuerySet(Cowboy.all())).startswith("<QuerySet iterable=")


def test_creation_order(sheraf_connection, m0, m1, m2):
    assert [m0, m1, m2] == Cowboy.all()
    assert [m0, m1, m2] == Cowboy.filter(genre="M")
    assert [m0, m1] != Cowboy.filter(genre="M")


def test_filter_named_argument(sheraf_connection, m0, m1, m2):
    assert [m0, m2] == Cowboy.filter(age=30)
    assert QuerySet([m0, m2]) == Cowboy.filter(age=30)
    assert [m0] == Cowboy.filter(age=30, name="Peter")


def test_filter_invalid_named_argument(sheraf_connection):
    with pytest.raises(InvalidFilterException):
        Cowboy.filter(foobar=3)


def test_filter_invalid_index(sheraf_connection):
    assert [] == Cowboy.filter(["invalid"])


def test_filter_predicate(sheraf_connection, m0, m1, m2):
    assert [m0, m2] == Cowboy.filter(lambda m: m.age % 3 == 0)


def test_delete(sheraf_database):
    with sheraf.connection(commit=True):
        Cowboy.create(age=30, name="Peter", size=180)
        m1 = Cowboy.create(age=50, name="George Abitbol", size=170)
        Cowboy.create(age=30, name="Steven", size=160)

    with sheraf.connection(commit=True):
        Cowboy.filter(age=30).delete()

    with sheraf.connection():
        assert [m1] == Cowboy.all()


def test_delete_all(sheraf_database):
    with sheraf.connection(commit=True):
        Cowboy.create(age=30, name="Peter", size=180)
        Cowboy.create(age=50, name="George Abitbol", size=170)
        Cowboy.create(age=30, name="Steven", size=160)

    with sheraf.connection(commit=True):
        Cowboy.all().delete()

    with sheraf.connection():
        assert [] == Cowboy.all()


def test_chained_filters(sheraf_connection, m0, m1, m2):
    assert [m0] == Cowboy.filter(age=30, name="Peter")
    assert [m0] == Cowboy.filter(age=30).filter(name="Peter")
    assert [m0] == Cowboy.filter(age=30).filter(lambda m: "eter" in m.name)
    assert [m0] == Cowboy.filter(lambda m: m.age == 30).filter(
        lambda m: "eter" in m.name
    ).filter(lambda m: m.name.startswith("P"))


def test_invalid_double_filter(sheraf_connection, m0):
    assert [m0] == Cowboy.filter(age=30).filter(age=30)

    with pytest.raises(InvalidFilterException):
        Cowboy.filter(age=30).filter(age=40)


def test_invalid_filter_parameter(sheraf_connection, m0):
    with pytest.raises(InvalidFilterException):
        list(Cowboy.filter(age=30).filter(foobar=40))


def test_itertools_tee(sheraf_connection, m0, m1, m2):
    qall = Cowboy.all()
    qall, qall_tee = itertools.tee(qall)

    assert [m0, m1, m2] == list(qall)
    assert [] == list(qall)
    assert [m0, m1, m2] == list(qall_tee)
    assert [] == list(qall_tee)


def test_copy_model(sheraf_connection, m0, m1, m2):
    qall = Cowboy.all()
    qall_copy = qall.copy()

    assert [m0, m1, m2] == qall_copy
    assert [] == qall_copy
    assert [m0, m1, m2] == qall
    assert [] == qall


def test_copy_iterable(sheraf_connection, m0, m1, m2):
    qall = QuerySet([m0, m2, m1])
    qall_copy = qall.copy()

    assert [m0, m2, m1] == qall_copy
    assert [] == qall_copy
    assert [m0, m2, m1] == qall
    assert [] == qall


def test_copy_iterable_iterator(sheraf_connection, m0, m1, m2):
    res = [m0, m2, m1]
    qall = QuerySet(iter(res))
    qall_copy = qall.copy()

    assert [m0, m2, m1] == qall_copy
    assert [] == qall_copy
    assert [m0, m2, m1] == qall
    assert [] == qall


def test_disconnected(sheraf_database):
    with sheraf.connection(commit=True):
        m0 = Cowboy.create(age=30, name="Peter", size=180)

    with pytest.raises(NotConnectedException):
        list(Cowboy.all())

    q = Cowboy.all()
    with sheraf.connection():
        assert [m0] == q


def test_successive_filters_copy(sheraf_connection, m0, m1, m2, m3):
    a = Cowboy.filter(age=30)
    b = a.filter(lambda p: p.size > 160)

    assert b is not a
    assert b._predicate != a._predicate
    assert [m0, m2, m3] == a
    assert [m0, m3] == b


def test_get(sheraf_connection, m0, m1):
    assert m0 == Cowboy.filter(name="Peter").get()
    assert m0 == Cowboy.get(name="Peter")

    with pytest.raises(sheraf.exceptions.QuerySetUnpackException):
        Cowboy.get()

    with pytest.raises(sheraf.exceptions.QuerySetUnpackException):
        Cowboy.all().get()

    with pytest.raises(sheraf.exceptions.QuerySetUnpackException):
        Cowboy.filter(name="NONAME").get()

    with pytest.raises(sheraf.exceptions.QuerySetUnpackException):
        Cowboy.get(name="NONAME")


def test_concat(sheraf_connection, m0, m1, m2):
    assert Cowboy.filter(age=30) == [m0, m2]
    assert Cowboy.filter(genre="M") == [m0, m1, m2]

    qs = Cowboy.filter(age=30) + Cowboy.filter(genre="M")
    assert Cowboy == qs.model
    assert qs == [m0, m2, m1]

    qs = Cowboy.filter(age=30) + Cowboy.filter(genre="M")
    assert qs.model == Cowboy
    assert next(qs) == m0
    assert next(qs) == m2
    assert next(qs) == m1

    qs = Cowboy.filter(age=30) + Cowboy.filter(genre="M")
    qs = qs[:100]
    assert qs == [m0, m2, m1]


def test_concat_empty(sheraf_connection, m0, m1, m2):
    assert Cowboy.filter(age=30) == [m0, m2]
    assert Cowboy.filter(genre="Z") == []

    qs = Cowboy.filter(genre="Z") + Cowboy.filter(age=30)
    assert qs == [m0, m2]

    qs = Cowboy.filter(age=30) + Cowboy.filter(genre="Z")
    assert qs == [m0, m2]

    qs = Cowboy.filter(genre="Z") + Cowboy.filter(age=30)
    qs = qs[:100]
    assert qs == [m0, m2]

    qs = Cowboy.filter(age=30) + Cowboy.filter(genre="Z")
    qs = qs[:100]
    assert qs == [m0, m2]

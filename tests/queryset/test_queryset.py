import itertools

import orderedset
import pytest

import sheraf
import sheraf.models
from sheraf.exceptions import InvalidFilterException, NotConnectedException
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
    assert QuerySet() != None
    assert QuerySet([m0]) == QuerySet([m0])
    assert QuerySet([m0]) == QuerySet(m for m in [m0])
    assert QuerySet([m0]) == QuerySet(orderedset.OrderedSet([m0]))
    assert QuerySet([m0, m1, m2]) == QuerySet(orderedset.OrderedSet([m0, m1, m2]))


def test_create(sheraf_connection, m0):
    assert [m0] == Cowboy.filter(age=30)
    assert [] != Cowboy.filter(age=30)
    assert QuerySet([m0]) == Cowboy.filter(age=30)
    assert m0 in Cowboy.filter(age=30)


def test_count(sheraf_connection, m0):
    qs = Cowboy.all()
    assert qs.count() == 1
    assert qs.count() == 0


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


def test_copy(sheraf_connection, m0, m1, m2):
    qall = Cowboy.all()
    qall_copy = qall.copy()

    assert [m0, m1, m2] == qall_copy
    assert [] == qall_copy
    assert [m0, m1, m2] == qall
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

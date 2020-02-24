import sys

import pytest

import sheraf
from sheraf.exceptions import InvalidOrderException
from sheraf.queryset import QuerySet

from .conftest import Cowboy


def test_id_order(sheraf_connection, m0, m1, m2):
    assert [m0, m1, m2] == Cowboy.all()
    assert [m0, m1, m2] == Cowboy.order(sheraf.ASC)
    assert [m2, m1, m0] == Cowboy.order(sheraf.DESC)
    assert [m0, m1, m2] == Cowboy.all().order(sheraf.ASC)
    assert [m2, m1, m0] == Cowboy.all().order(sheraf.DESC)

    assert [m0, m1, m2] == QuerySet([m0, m1, m2]).order(id=sheraf.ASC)
    assert [m2, m1, m0] == QuerySet([m0, m1, m2]).order(id=sheraf.DESC)


def test_attribute_order(sheraf_connection, m0, m1, m2):
    assert [m0, m1, m2] == Cowboy.all()
    assert [m0, m1, m2] == Cowboy.order(size=sheraf.DESC)
    assert [m2, m1, m0] == Cowboy.order(size=sheraf.ASC)
    assert [m0, m1, m2] == Cowboy.all().order(size=sheraf.DESC)
    assert [m2, m1, m0] == Cowboy.all().order(size=sheraf.ASC)


def test_multiple_attribute_orders(sheraf_connection, m0, m1, m2, m3):
    assert [m0, m1, m2, m3] == Cowboy.all()
    assert [m0, m3, m2, m1] == Cowboy.all().order(age=sheraf.ASC).order(
        size=sheraf.DESC
    )
    assert [m1, m2, m3, m0] == Cowboy.all().order(age=sheraf.DESC).order(
        size=sheraf.ASC
    )


def test_successive_orders_copy(sheraf_connection, m0, m1, m2, m3):
    a = Cowboy.order(age=sheraf.ASC)
    b = a.order(size=sheraf.DESC)

    assert b is not a
    assert b.orders != a.orders
    assert [m0, m2, m3, m1] == a
    assert [m0, m3, m2, m1] == b


@pytest.mark.skipif(
    sys.version_info < (3, 6), reason="Arguments order is only kept from python 3.6"
)
def test_multiple_order_parameters(sheraf_connection, m0, m1, m2, m3):
    assert [m0, m1, m2, m3] == Cowboy.all()
    assert [m0, m3, m2, m1] == Cowboy.all().order(age=sheraf.ASC, size=sheraf.DESC)
    assert [m1, m2, m3, m0] == Cowboy.all().order(age=sheraf.DESC, size=sheraf.ASC)


@pytest.mark.skipif(
    sys.version_info >= (3, 6), reason="Arguments order is only kept from python 3.6"
)
def test_multiple_order_parameters_compatibility(sheraf_connection, m0, m1, m2, m3):
    with pytest.raises(InvalidOrderException):
        assert [m0, m2, m1] == Cowboy.all().order(name=sheraf.ASC, age=sheraf.DESC)

    with pytest.raises(InvalidOrderException):
        assert [m2, m0, m1] == Cowboy.all().order(age=sheraf.DESC, name=sheraf.ASC)


def test_invalid_order_call(sheraf_connection, m0, m1, m2, m3):
    with pytest.raises(InvalidOrderException):
        Cowboy.order("foobar")

    with pytest.raises(InvalidOrderException):
        Cowboy.all().order("foobar")

    with pytest.raises(InvalidOrderException):
        Cowboy.all().order(sheraf.ASC).order(sheraf.DESC)

    with pytest.raises(InvalidOrderException):
        Cowboy.all().order(age=sheraf.ASC).order(age=sheraf.DESC)

    with pytest.raises(InvalidOrderException):
        Cowboy.all().order(age=sheraf.ASC).order(name=sheraf.DESC).order(
            age=sheraf.DESC
        )

    with pytest.raises(InvalidOrderException):
        Cowboy.order(age="foobar")

    with pytest.raises(InvalidOrderException):
        Cowboy.all().order(age="foobar")

    with pytest.raises(InvalidOrderException):
        Cowboy.order(foobar=sheraf.ASC)

    with pytest.raises(InvalidOrderException):
        list(Cowboy.all().order(foobar=sheraf.ASC))

    with pytest.raises(InvalidOrderException):
        QuerySet([Cowboy.create()]).order()

    with pytest.raises(InvalidOrderException):
        QuerySet([Cowboy.create()]).order(sheraf.ASC)

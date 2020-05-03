import pytest

import tests
from sheraf.queryset import QuerySet

from .conftest import Cowboy


def test_slicing_models(sheraf_connection, m0, m1, m2):
    assert [m0] == Cowboy.all()[0]
    assert [m2] == Cowboy.all()[2]
    assert [m2] == Cowboy.all()[-1]

    assert [m0, m1] == Cowboy.all()[0:2]
    assert [m0] == Cowboy.all()[0:1]

    assert [] == Cowboy.all()[0:0]
    assert [] == Cowboy.all()[2:2]
    assert [] == Cowboy.all()[-1:-1]

    assert [m0, m1, m2] == Cowboy.all()[:]
    assert [m0, m2] == Cowboy.all()[::2]
    assert [m0, m1, m2] == Cowboy.all()[0:]
    assert [m0, m1] == Cowboy.all()[:-1]
    assert [m0, m1] == Cowboy.all()[0:-1]
    assert [m2] == Cowboy.all()[2:]
    assert [m1, m2] == Cowboy.all()[-2:]
    assert [m1] == Cowboy.all()[1:-1]

    assert [m0, m1, m2] == Cowboy.all()[0:10]


def test_slicing_regular_models(sheraf_connection):
    class Cowboy(tests.UUIDAutoModel):
        pass

    m0 = Cowboy.create(id="ac61941e-170f-492a-b049-0d9565985e6a")
    m1 = Cowboy.create(id="bd45dd2c-a222-4342-9110-92994a2739ee")
    m2 = Cowboy.create(id="c8b15752-6605-48b2-be0b-d052fcac799f")

    assert [m0] == Cowboy.all()[0]
    assert [m2] == Cowboy.all()[2]
    assert [m2] == Cowboy.all()[-1]

    assert [m0, m1] == Cowboy.all()[0:2]
    assert [m0] == Cowboy.all()[0:1]

    assert [] == Cowboy.all()[0:0]
    assert [] == Cowboy.all()[2:2]
    assert [] == Cowboy.all()[-1:-1]

    assert [m0, m1, m2] == Cowboy.all()[:]
    assert [m0, m2] == Cowboy.all()[::2]
    assert [m0, m1, m2] == Cowboy.all()[0:]
    assert [m0, m1] == Cowboy.all()[:-1]
    assert [m0, m1] == Cowboy.all()[0:-1]
    assert [m2] == Cowboy.all()[2:]
    assert [m1, m2] == Cowboy.all()[-2:]
    assert [m1] == Cowboy.all()[1:-1]

    assert [m0, m1, m2] == Cowboy.all()[0:10]


def test_slicing_list(sheraf_connection, m0, m1, m2):
    assert [m0] == QuerySet([m0, m1, m2])[0]
    assert [m2] == QuerySet([m0, m1, m2])[2]
    assert [m2] == QuerySet([m0, m1, m2])[-1]

    assert [m0, m1] == QuerySet([m0, m1, m2])[0:2]
    assert [m0] == QuerySet([m0, m1, m2])[0:1]

    assert [] == QuerySet([m0, m1, m2])[0:0]
    assert [] == QuerySet([m0, m1, m2])[2:2]
    assert [] == QuerySet([m0, m1, m2])[-1:-1]

    assert [m0, m1, m2] == QuerySet([m0, m1, m2])[:]
    assert [m0, m2] == QuerySet([m0, m1, m2])[::2]
    assert [m0, m1, m2] == QuerySet([m0, m1, m2])[0:]
    assert [m0, m1] == QuerySet([m0, m1, m2])[:-1]
    assert [m0, m1] == QuerySet([m0, m1, m2])[0:-1]
    assert [m2] == QuerySet([m0, m1, m2])[2:]
    assert [m1, m2] == QuerySet([m0, m1, m2])[-2:]
    assert [m1] == QuerySet([m0, m1, m2])[1:-1]


def test_slicing_iterator(sheraf_connection, m0, m1, m2):
    assert [m0] == QuerySet(iter([m0, m1, m2]))[0]
    assert [m2] == QuerySet(iter([m0, m1, m2]))[2]

    assert [m0, m1] == QuerySet(iter([m0, m1, m2]))[0:2]
    assert [m0] == QuerySet(iter([m0, m1, m2]))[0:1]

    assert [] == QuerySet(iter([m0, m1, m2]))[0:0]
    assert [] == QuerySet(iter([m0, m1, m2]))[2:2]
    assert [m0, m1, m2] == QuerySet(iter([m0, m1, m2]))[:]
    assert [m0, m2] == QuerySet(iter([m0, m1, m2]))[::2]
    assert [m0, m1, m2] == QuerySet(iter([m0, m1, m2]))[0:]
    assert [m2] == QuerySet(iter([m0, m1, m2]))[2:]

    with pytest.raises(ValueError):
        assert [m2] == QuerySet(iter([m0, m1, m2]))[-1]

    with pytest.raises(ValueError):
        assert [m1] == QuerySet(iter([m0, m1, m2]))[1:-1]

    with pytest.raises(ValueError):
        assert [] == QuerySet(iter([m0, m1, m2]))[-1:-1]

    with pytest.raises(ValueError):
        assert [m0, m1] == QuerySet(iter([m0, m1, m2]))[:-1]

    with pytest.raises(ValueError):
        assert [m0, m1] == QuerySet(iter([m0, m1, m2]))[0:-1]

    with pytest.raises(ValueError):
        assert [m1, m2] == QuerySet(iter([m0, m1, m2]))[-2:]

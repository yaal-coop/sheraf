import pytest
from sheraf.queryset import QuerySet


@pytest.mark.skip
def test_and(sheraf_connection, m0, m1, m2):
    assert QuerySet([m1]) == QuerySet([m0, m1]) & QuerySet([m1, m2])
    assert QuerySet([m0, m1, m2]) == QuerySet([m0, m1, m2]) & QuerySet([m2, m1, m0])
    assert QuerySet([m2, m1, m0]) == QuerySet([m2, m1, m0]) & QuerySet([m0, m1, m2])


@pytest.mark.skip
def test_or(sheraf_connection, m0, m1, m2):
    assert QuerySet() == QuerySet() | QuerySet()
    assert QuerySet([m0]) == QuerySet() | QuerySet([m0])
    assert QuerySet([m0]) == QuerySet([m0]) | QuerySet()
    assert QuerySet([m0, m1]) == QuerySet([m0]) | QuerySet([m1])
    assert QuerySet([m1, m0]) == QuerySet([m1]) | QuerySet([m0])

    assert QuerySet([m0, m1, m2]) == QuerySet([m0, m1]) | QuerySet([m1, m2])
    assert QuerySet([m0, m1, m2]) == QuerySet([m0, m1, m2]) | QuerySet([m2, m1, m0])
    assert QuerySet([m2, m1, m0]) == QuerySet([m2, m1, m0]) | QuerySet([m0, m1, m2])


@pytest.mark.skip
def test_xor(sheraf_connection, m0, m1, m2):
    assert QuerySet([m0, m2]) == QuerySet([m0, m1]) ^ QuerySet([m1, m2])
    assert QuerySet([m2, m0]) == QuerySet([m1, m2]) ^ QuerySet([m0, m1])
    assert QuerySet() == QuerySet([m0, m1, m2]) ^ QuerySet([m2, m1, m0])
    assert QuerySet() == QuerySet([m2, m1, m0]) ^ QuerySet([m0, m1, m2])

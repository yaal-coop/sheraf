import pytest
import sheraf


def test_large_list(sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root.list = sheraf.types.LargeList()
        for i in range(100):
            c.root.list.append(str(i))

    with sheraf.connection() as c:
        assert c.root.list[50] == "50"
        assert c.root.list[-1] == "99"
        assert "25" in c.root.list
        assert len(c.root.list) == 100

    with sheraf.connection() as c:
        assert list(c.root.list[98:]) == ["98", "99"]
        assert list(c.root.list[12:14]) == ["12", "13"]
        assert list(c.root.list[98:]) == ["98", "99"]
        assert list(c.root.list[:4]) == ["0", "1", "2", "3"]
        assert list(c.root.list[:]) == [str(i) for i in range(100)]
        assert list(c.root.list[-10:-1:2]) == ["90", "92", "94", "96", "98"]

    with sheraf.connection() as c:
        assert list(c.root.list[99:97:-1]) == ["99", "98"]
        assert list(c.root.list[-1:-3:-1]) == ["99", "98"]
        assert list(c.root.list[::-1]) == [str(i) for i in range(99, -1, -1)]


def test_simple_comparisons():
    assert [1] == sheraf.types.LargeList([1])
    assert [] == sheraf.types.LargeList()

    assert [1] != sheraf.types.LargeList()
    assert [] != sheraf.types.LargeList([1])


def test_insertion():
    a = sheraf.types.LargeList([1, 3])
    a.insert(1, 2)
    assert [1, 2, 3] == list(a)
    assert [1, 2, 3] == a

    b = sheraf.types.LargeList([])
    b.insert(0, "a")
    assert ["a"] == list(b)
    assert ["a"] == b


def test_same(sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root.list = sheraf.types.LargeList()
        for i in range(100):
            c.root.list.append(1)

    with sheraf.connection() as c:
        for i in range(100):
            assert c.root.list[i] == 1


def test_deletion():
    a = sheraf.types.LargeList([1, 2, 3, 2])
    a.remove(2)
    assert [1, 3, 2] == a
    a.remove(2)
    assert [1, 3] == a
    with pytest.raises(ValueError):
        a.remove(2)


def test_deletion_all():
    a = sheraf.types.LargeList([1, 2, 3, 2])
    a.remove(2, True)
    assert [1, 3] == a
    with pytest.raises(ValueError):
        a.remove(2)


def test_append():
    a = sheraf.types.LargeList()
    a.append(1)
    assert [1] == a
    a.append(2)
    assert [1, 2] == a
    a.append(2)
    assert [1, 2, 2] == a
    a.append(2, unique=True)
    assert [1, 2, 2] == a


def test_add():
    a = sheraf.types.LargeList([1])
    assert list(a + [2]) == [1, 2]

    a += [2]
    assert list(a) == [1, 2]

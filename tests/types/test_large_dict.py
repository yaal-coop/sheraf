import string

import pytest

import sheraf


def test_large_dict(sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root.dict = sheraf.types.LargeDict()
        for i in range(100):
            c.root.dict[i] = str(i)

    with sheraf.connection() as c:
        assert c.root.dict[50] == "50"
        with pytest.raises(KeyError):
            c.root.dict[-1]
        assert 25 in c.root.dict
        assert 100 == len(c.root.dict)

    with sheraf.connection() as c:
        assert list(c.root.dict[98:]) == ["98", "99"]
        assert list(c.root.dict[12:14]) == ["12", "13", "14"]
        assert list(c.root.dict[:4]) == ["0", "1", "2", "3", "4"]
        assert list(c.root.dict[:]) == [str(i) for i in range(100)]

    with sheraf.connection() as c:
        assert list(c.root.dict[98::-1]) == ["99", "98"]
        assert list(c.root.dict[:3:-1]) == ["3", "2", "1", "0"]
        assert list(c.root.dict[10:12:-1]) == ["12", "11", "10"]

        assert list(c.root.dict[90:94:2]) == ["90", "92", "94"]

        assert [0, 1, 2] == list(c.root.dict.iterkeys(0, 2, False))
        assert [2, 1, 0] == list(c.root.dict.iterkeys(0, 2, True))


def test_alphabetic_keys(sheraf_database):
    alphabet = sorted(string.ascii_letters)
    with sheraf.connection(commit=True) as c:
        c.root.dict = sheraf.types.LargeDict()
        for i in alphabet:
            c.root.dict[i] = i

    with sheraf.connection() as c:
        assert c.root.dict["t"] == "t"
        with pytest.raises(KeyError):
            c.root.dict["WUT"]
        assert "b" in c.root.dict
        assert len(alphabet) == len(c.root.dict)

    with sheraf.connection() as c:
        assert list(c.root.dict["a":"c"]) == ["a", "b", "c"]
        assert list(c.root.dict["y":]) == ["y", "z"]
        assert list(c.root.dict[:"C"]) == ["A", "B", "C"]
        assert list(c.root.dict[:]) == alphabet

    with sheraf.connection() as c:
        assert list(c.root.dict["a":"c":-1]) == ["c", "b", "a"]
        assert list(c.root.dict["y"::-1]) == ["z", "y"]
        assert list(c.root.dict[:"C":-1]) == ["C", "B", "A"]
        assert list(c.root.dict[::-1]) == list(reversed(alphabet))


def test_integer_tuple(sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root.dict = sheraf.types.LargeDict()
        for x in range(10):
            for y in range(10):
                c.root.dict[(x, y)] = str(x) + "-" + str(y)

    with sheraf.connection() as c:
        assert c.root.dict[(5, 0)] == "5-0"
        with pytest.raises(KeyError):
            c.root.dict[(100, 100)]
        assert (2, 5) in c.root.dict
        assert 100 == len(c.root.dict)

    with sheraf.connection() as c:
        assert list(c.root.dict[(9, 8):]) == ["9-8", "9-9"]
        assert list(c.root.dict[(1, 2):(1, 4)]) == ["1-2", "1-3", "1-4"]
        assert list(c.root.dict[:(0, 4)]) == ["0-0", "0-1", "0-2", "0-3", "0-4"]
        assert list(c.root.dict[:]) == [
            str(x) + "-" + str(y) for x in range(10) for y in range(10)
        ]

    with sheraf.connection() as c:
        assert list(c.root.dict[(9, 8)::-1]) == ["9-9", "9-8"]
        assert list(c.root.dict[:(0, 3):-1]) == ["0-3", "0-2", "0-1", "0-0"]
        assert list(c.root.dict[(1, 0):(1, 2):-1]) == ["1-2", "1-1", "1-0"]
        assert list(c.root.dict[(9, 0):(9, 4):2]) == ["9-0", "9-2", "9-4"]


def test_same(sheraf_database):
    with sheraf.connection(commit=True) as c:
        c.root.dict = sheraf.types.LargeDict()
        for i in range(100):
            c.root.dict[i] = 1

    with sheraf.connection() as c:
        for i in range(100):
            assert c.root.dict[i] == 1

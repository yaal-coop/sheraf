import enum
import pytest
import sheraf
import tests


def test_enum_attribute(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    m = Model.create(status=Enum.FOO)
    n = Model.create(status=1)

    assert m.mapping["status"] == 1
    assert n.mapping["status"] == 1

    assert m.status == 1
    assert m.status == Enum.FOO
    assert m.status == n.status
    assert m.status.is_foo
    assert not m.status.is_bar

    m.status = Enum.BAR
    n.status = 2

    assert m.status == 2
    assert m.status == Enum.BAR
    assert m.status == n.status
    assert m.status.is_bar
    assert not m.status.is_foo

    m.status = 1
    assert m.status < n.status
    assert m.status <= n.status
    assert n.status > m.status
    assert n.status >= m.status


def test_bad_values(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    with pytest.raises(ValueError):
        Model.create(status=3)


def test_default_value(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute(), default=Enum.BAR)

    m = Model.create()
    assert m.status == 2
    assert m.status == Enum.BAR


def test_indexation(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(
            Enum, sheraf.IntegerAttribute(), default=Enum.BAR
        ).index()

    m = Model.create()
    assert m in Model.search(status=Enum.BAR)


def test_cast(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    m = Model.create()
    m.status = "1"

    assert m.status == 1
    assert m.status == Enum.FOO


def test_hash(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    m = Model.create(status=Enum.FOO)
    {m.status}


def test_none(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    m = Model.create(status=None)
    assert m.status is None


def test_str(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    m = Model.create(status=Enum.FOO)
    assert str(m.status) == "1"

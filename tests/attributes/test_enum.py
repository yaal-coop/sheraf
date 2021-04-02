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


def test_bad_values(sheraf_connection):
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2

    class Model(tests.UUIDAutoModel):
        status = sheraf.EnumAttribute(Enum, sheraf.IntegerAttribute())

    with pytest.raises(ValueError):
        Model.create(status=3)

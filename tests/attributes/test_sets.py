import pytest

import sheraf
import tests


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_set_attribute(sheraf_connection, persistent_type, subattribute):
    class ModelForTest(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    a = ModelForTest.create()
    assert len(a.set) == 0
    assert not a.set
    a.set.add(12)
    a.set.add(15)
    assert len(a.set) == 2
    assert a.set
    assert 12 in a.set
    assert 17 not in a.set

    if subattribute:
        assert {12, 15, 18} == set(a.set | {18})
        assert {12} == set(a.set & {18, 12})
        assert {12, 18} == set(a.set ^ {18, 15})

        assert {12, 15, 18} == set({18} | a.set)
        assert {12} == set({18, 12} & a.set)
        assert {12, 18} == set({18, 15} ^ a.set)

        a.set |= {18}
        assert {12, 15, 18} == set(a.set)
        a.set ^= {18}
        assert {12, 15} == set(a.set)
        a.set &= {12, 15}
        assert {12, 15} == set(a.set)

    a = ModelForTest.read(a.id)
    assert {12, 15} == set(a.set)

    a.set.remove(12)
    assert len(a.set) == 1

    a.set.clear()
    assert not a.set

    a.set.add(1)
    assert 1 in a.set
    a.set = None
    assert 1 not in a.set


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_primitive_type(sheraf_connection, persistent_type, subattribute):
    class ModelTest(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    m = ModelTest.create()
    m.set = {1, 2}
    assert isinstance(m.mapping["set"], persistent_type)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_sheraf_typeset(sheraf_connection, persistent_type, subattribute):
    class ModelTest(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    m = ModelTest.create()
    m.set = sheraf.types.Set([1, 2])
    assert isinstance(m.mapping["set"], persistent_type)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_enum_type(sheraf_connection, persistent_type, subattribute):
    import enum

    class ModelTest(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    class E(enum.IntEnum):
        CONST = 1

    m = ModelTest.create()
    m.set = sheraf.types.Set([E.CONST])

    assert isinstance(m.mapping["set"], persistent_type)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_set_attribute_update(sheraf_connection, persistent_type):
    class ModelTest(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(
            attribute=sheraf.IntegerAttribute(), persistent_type=persistent_type
        )

    m = ModelTest.create()
    m.set = {1, 2, 3}

    m.edit({"set": {1, 2}}, deletion=True)
    assert {1, 2} == set(m.set)

    m.edit({"set": {1, 2}}, edition=True)
    assert {1, 2} == set(m.set)

    m.edit({"set": {1, 2, 3}}, addition=True)
    assert {1, 2, 3} == set(m.set)

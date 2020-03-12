import pytest

import sheraf


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList, list]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_list_attribute(sheraf_connection, persistent_type, subattribute):
    class ModelTest(sheraf.AutoModel):
        list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = ModelTest.create()
    assert len(m.list) == 0
    assert not m.list
    m.list.append(1)
    assert len(m.list) == 1
    assert m.list

    for elt in m.list:
        assert elt == 1

    with pytest.raises(IndexError):
        m.list[14] = 4

    with pytest.raises(IndexError):
        m.list[14]

    assert 1 == m.list[0]
    m.list[0] = 2
    assert 2 == m.list[0]
    m.list.extend([3, 4])
    assert [2, 3, 4] == list(m.list)

    assert list(m.list[1:2]) == [3]

    assert 4 == m.list.pop()
    assert [2, 3] == list(m.list)

    m.list.remove(3)
    assert [2] == list(m.list)

    # TODO: clear is not implemented on PersistentList on py2
    if subattribute or persistent_type == sheraf.types.LargeList:
        m.list.clear()
        assert len(m.list) == 0

    m.list = [1, 2]
    assert list(m.list) == [1, 2]
    m.list = None
    assert len(m.list) == 0


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList, list]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.SimpleAttribute()])
def test_primitive_type(sheraf_connection, persistent_type, subattribute):
    class ModelTest(sheraf.AutoModel):
        _list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = ModelTest.create()
    m._list = list()
    assert isinstance(m.mapping["_list"], persistent_type)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList, list]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.SimpleAttribute()])
def test_sherafmapping_type(sheraf_connection, persistent_type, subattribute):
    class ModelTest(sheraf.AutoModel):
        _list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = ModelTest.create()
    m._list = persistent_type([1, 2])
    assert isinstance(m.mapping["_list"], persistent_type)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_list_attribute_update(sheraf_connection, persistent_type, subattribute):
    class ModelTest(sheraf.AutoModel):
        list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = ModelTest.create()
    m.list = [1, 2, 3]

    m.edit({"list": [1, 2]}, deletion=True)
    assert [1, 2] == list(m.list)

    m.edit({"list": [2, 1]}, edition=True)
    assert [2, 1] == list(m.list)

    m.edit({"list": [2, 1, 3]}, addition=True)
    assert [2, 1, 3] == list(m.list)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_nested(sheraf_database, persistent_type, subattribute):
    class ModelTest(sheraf.AutoModel):
        list = sheraf.ListAttribute(
            attribute=sheraf.ListAttribute(
                attribute=subattribute, persistent_type=persistent_type
            ),
            persistent_type=persistent_type,
        )

    with sheraf.connection(commit=True):
        m = ModelTest.create(list=[[0, 1], [2, 3]])

        assert 0 == m.list[0][0]
        assert 1 == m.list[0][1]
        assert 2 == m.list[1][0]
        assert 3 == m.list[1][1]
        assert isinstance(m.mapping["list"], persistent_type)
        assert isinstance(m.mapping["list"][0], persistent_type)
        assert [0, 1] == list(m.list[0])

    with sheraf.connection(commit=True):
        m = ModelTest.read(m.id)

        assert 0 == m.list[0][0]
        assert 1 == m.list[0][1]
        assert 2 == m.list[1][0]
        assert 3 == m.list[1][1]
        assert isinstance(m.mapping["list"], persistent_type)
        assert isinstance(m.mapping["list"][0], persistent_type)
        assert [0, 1] == list(m.list[0])

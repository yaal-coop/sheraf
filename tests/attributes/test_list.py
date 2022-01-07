import pytest
import sheraf
import tests


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList, list]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_list_attribute(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
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

    m.list = [0, 1, 2]
    assert m.list[0] == 0
    assert m.list[1] == 1
    assert m.list[2] == 2
    del m.list[1]
    assert list(m.list) == [0, 2]
    assert m.list[0] == 0
    assert m.list[1] == 2

    m.list = [1, 2]
    assert list(m.list) == [1, 2]
    assert m.list == [1, 2]

    assert list(m.list + [3]) == [1, 2, 3]
    m.list += [3]
    assert list(m.list) == [1, 2, 3]

    if subattribute:
        assert repr(m.list) == "[1, 2, 3]"

    m.list = None
    assert len(m.list) == 0


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList, list]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.SimpleAttribute()])
def test_primitive_type(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        _list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
    m._list = list()
    assert isinstance(m.mapping["_list"], persistent_type)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList, list]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.SimpleAttribute()])
def test_sherafmapping_type(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        _list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
    m._list = persistent_type([1, 2])
    assert isinstance(m.mapping["_list"], persistent_type)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_list_attribute_update(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        list = sheraf.ListAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
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
    class Model(tests.UUIDAutoModel):
        list = sheraf.ListAttribute(
            attribute=sheraf.ListAttribute(
                attribute=subattribute, persistent_type=persistent_type
            ),
            persistent_type=persistent_type,
        )

    with sheraf.connection(commit=True):
        m = Model.create(list=[[0, 1], [2, 3]])

        assert 0 == m.list[0][0]
        assert 1 == m.list[0][1]
        assert 2 == m.list[1][0]
        assert 3 == m.list[1][1]
        assert isinstance(m.mapping["list"], persistent_type)
        assert isinstance(m.mapping["list"][0], persistent_type)
        assert [0, 1] == list(m.list[0])

    with sheraf.connection(commit=True):
        m = Model.read(m.id)

        assert 0 == m.list[0][0]
        assert 1 == m.list[0][1]
        assert 2 == m.list[1][0]
        assert 3 == m.list[1][1]
        assert isinstance(m.mapping["list"], persistent_type)
        assert isinstance(m.mapping["list"][0], persistent_type)
        assert [0, 1] == list(m.list[0])


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.StringAttribute()])
def test_indexation(sheraf_database, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        list = sheraf.ListAttribute(
            subattribute,
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True) as conn:
        m = Model.create(list=["foo", "bar"])
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["foo"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["bar"]
        )
        assert [m] == list(Model.search(list="foo"))

        m.list = ["bar", "baz"]
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["bar"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["baz"]
        )
        assert "foo" not in conn.root()[Model.table]["list"]


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.StringAttribute()])
def test_indexation_limitation(sheraf_database, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        list = sheraf.ListAttribute(
            subattribute,
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True) as conn:
        m = Model.create(list=["foo", "bar"])
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["foo"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["bar"]
        )
        assert [m] == list(Model.search(list="foo"))
        assert [m] == list(Model.search(list="bar"))
        assert [] == list(Model.search(list="baz"))

        # TODO: This behavior should be fixed one day.
        # https://gitlab.com/yaal/sheraf/-/issues/14

        m.list.remove("foo")
        m.list.append("baz")
        assert ["bar", "baz"] == list(m.list)

        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["foo"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["bar"]
        )
        assert "baz" not in conn.root()[Model.table]["list"]

        assert [] == list(Model.search(list="foo"))
        assert [m] == list(Model.search(list="bar"))
        assert [] == list(Model.search(list="baz"))


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
def test_nested_indexation(sheraf_database, persistent_type):
    class Model(tests.UUIDAutoModel):
        list = sheraf.ListAttribute(
            sheraf.ListAttribute(
                sheraf.StringAttribute(),
                persistent_type=persistent_type,
            ),
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True) as conn:
        m = Model.create(list=[["foo", "bar"], ["baz"]])
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["foo"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["bar"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["list"]["baz"]
        )
        assert [m] == list(Model.search(list="foo"))


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallList, sheraf.types.LargeList]
)
def test_nested_model_indexation(sheraf_database, persistent_type):
    class Submodel(tests.UUIDAutoModel):
        pass

    class Model(tests.UUIDAutoModel):
        submodels = sheraf.ListAttribute(
            sheraf.ModelAttribute(Submodel),
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True):
        sub = Submodel.create()
        m = Model.create(submodels=[sub])
        assert [m] == Model.search(submodels=sub)


class AssignAnything(tests.IntAutoModel):
    model = sheraf.ReverseModelAttribute("AssignModel", "list")


class AssignModel(tests.UUIDAutoModel):
    list = sheraf.LargeListAttribute(sheraf.ModelAttribute(AssignAnything)).index()


@pytest.mark.skip
def test_assign_indexed(sheraf_connection):
    m0 = AssignAnything.create()
    m1 = AssignAnything.create()
    m2 = AssignAnything.create()

    m = AssignModel.create(list={m0})
    m0 = AssignAnything.read(m0.id)
    assert [m0] == list(m.list)
    assert m in m0.model

    m.assign(list=[m0, m1])
    m0 = AssignAnything.read(m0.id)
    m1 = AssignAnything.read(m1.id)
    assert [m0, m1] == m.list
    assert m in m0.model
    assert m in m1.model

    m.assign(list=[m0.id, m1.id, m2.id])
    m0 = AssignAnything.read(m0.id)
    m1 = AssignAnything.read(m1.id)
    m2 = AssignAnything.read(m2.id)
    assert [m0, m1, m2] == m.list
    assert m in m0.model
    assert m in m1.model
    assert m in m2.model

import pytest
import sheraf
import tests


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallDict, sheraf.types.LargeDict, dict]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_dict_attribute(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        dict = sheraf.DictAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
    assert not m.dict
    assert 0 == len(m.dict)

    m.dict.update({"a": 0, "b": 1})
    assert 0 == m.dict["a"]
    assert 1 == m.dict["b"]
    assert 2 == len(m.dict)
    assert m.dict

    assert "a" in m.dict.keys()
    assert 1 in m.dict.values()
    for k, v in m.dict.items():
        assert (k, v) in [("a", 0), ("b", 1)]

    for k in m.dict:
        assert k in ("a", "b")

    if subattribute or persistent_type == sheraf.types.LargeDict:
        assert "a" == m.dict.minKey()
        assert "b" == m.dict.maxKey()

    m = Model.read(m.id)
    assert 0 == m.dict["a"]
    assert 1 == m.dict["b"]

    assert 0 == m.dict.get("a")
    assert m.dict.get("YOLO") is None
    assert "DUMMY" == m.dict.get("YOLO", "DUMMY")

    assert "a" in m.dict
    del m.dict["a"]
    assert "a" not in m.dict

    assert m.dict
    m.dict.clear()
    assert not m.dict

    m.dict["a"] = 5
    assert "a" in m.dict
    m.dict = None
    assert "a" not in m.dict


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallDict, sheraf.types.LargeDict, dict]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_primitive_type(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        _dict = sheraf.DictAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
    m._dict = dict()
    assert isinstance(m.mapping["_dict"], persistent_type)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallDict, sheraf.types.LargeDict, dict]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_sheraf_type_dict(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        _dict = sheraf.DictAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
    m._dict = sheraf.types.LargeDict({})
    assert isinstance(m.mapping["_dict"], persistent_type)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallDict, sheraf.types.LargeDict]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_dict_attribute_update(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        dict = sheraf.DictAttribute(
            attribute=subattribute, persistent_type=persistent_type
        )

    m = Model.create()
    m.dict = {"a": 0, "b": 1, "c": 2}

    m.edit({"dict": {"a": 0, "b": 1}}, deletion=True)
    assert {"a": 0, "b": 1} == dict(m.dict)

    m.edit({"dict": {"a": 1, "b": 0}}, edition=True)
    assert {"a": 1, "b": 0} == dict(m.dict)

    m.edit({"dict": {"a": 1, "b": 0, "c": 2}}, addition=True)
    assert {"a": 1, "b": 0, "c": 2} == dict(m.dict)


@pytest.mark.parametrize(
    "persistent_type", [sheraf.types.SmallDict, sheraf.types.LargeDict]
)
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_nested(sheraf_database, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        dict = sheraf.DictAttribute(
            attribute=sheraf.DictAttribute(
                attribute=subattribute, persistent_type=persistent_type
            ),
            persistent_type=persistent_type,
        )

    with sheraf.connection(commit=True):
        m = Model.create(dict={"foo": {"bar": 0, "baz": 1}})

        assert 0 == m.dict["foo"]["bar"]
        assert 1 == m.dict["foo"]["baz"]
        assert isinstance(m.mapping["dict"], persistent_type)
        assert isinstance(m.mapping["dict"]["foo"], persistent_type)
        assert {"bar", "baz"} == set(m.dict["foo"].keys())
        assert {0, 1} == set(m.dict["foo"].values())

    with sheraf.connection(commit=True):
        m = Model.read(m.id)

        assert 0 == m.dict["foo"]["bar"]
        assert 1 == m.dict["foo"]["baz"]
        assert isinstance(m.mapping["dict"], persistent_type)
        assert isinstance(m.mapping["dict"]["foo"], persistent_type)
        assert {"bar", "baz"} == set(m.dict["foo"].keys())
        assert {0, 1} == set(m.dict["foo"].values())

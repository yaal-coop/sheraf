import pytest
import sheraf
import tests


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_set_attribute(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    a = Model.create()
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
        assert {12} == set(a.set - {15})

        assert {12, 15, 18} == set({18} | a.set)
        assert {12} == set({18, 12} & a.set)
        assert {12, 18} == set({18, 15} ^ a.set)
        assert {4} == set({12, 15, 4} - a.set)

        a.set |= {18}
        assert {12, 15, 18} == set(a.set)
        a.set ^= {18}
        assert {12, 15} == set(a.set)
        a.set &= {12, 15}
        assert {12, 15} == set(a.set)
        a.set -= {15}
        assert {12} == set(a.set)
        a.set = {12, 15}

    a = Model.read(a.id)
    assert {12, 15} == set(a.set)

    a.set.remove(12)
    assert len(a.set) == 1

    a.set.clear()
    assert not a.set

    a.set.add(1)
    assert 1 in a.set

    if subattribute:
        assert repr(a.set) == "{1}"

    a.set = None
    assert 1 not in a.set


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_primitive_type(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    m = Model.create()
    m.set = {1, 2}
    assert isinstance(m.mapping["set"], persistent_type)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_sheraf_typeset(sheraf_connection, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    m = Model.create()
    m.set = sheraf.types.Set([1, 2])
    assert isinstance(m.mapping["set"], persistent_type)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.IntegerAttribute()])
def test_enum_type(sheraf_connection, persistent_type, subattribute):
    import enum

    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(subattribute, persistent_type=persistent_type)

    class E(enum.IntEnum):
        CONST = 1

    m = Model.create()
    m.set = sheraf.types.Set([E.CONST])

    assert isinstance(m.mapping["set"], persistent_type)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_set_attribute_update(sheraf_connection, persistent_type):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(
            attribute=sheraf.IntegerAttribute(), persistent_type=persistent_type
        )

    m = Model.create()
    m.set = {1, 2, 3}

    m.edit({"set": {1, 2}}, deletion=True)
    assert {1, 2} == set(m.set)

    m.edit({"set": {1, 2}}, edition=True)
    assert {1, 2} == set(m.set)

    m.edit({"set": {1, 2, 3}}, addition=True)
    assert {1, 2, 3} == set(m.set)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_set_attribute_update_list_value(sheraf_connection, persistent_type):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(
            attribute=sheraf.IntegerAttribute(), persistent_type=persistent_type
        )

    m = Model.create()
    m.set = {1, 2, 3}

    m.edit({"set": [1, 2]}, deletion=True)
    assert {1, 2} == set(m.set)

    m.edit({"set": [1, 2]}, edition=True)
    assert {1, 2} == set(m.set)

    m.edit({"set": [1, 2, 3]}, addition=True)
    assert {1, 2, 3} == set(m.set)


def test_set_assign_list_value(sheraf_connection):
    class Anything(tests.IntAutoModel):
        pass

    m0 = Anything.create()
    m1 = Anything.create()
    m2 = Anything.create()

    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(sheraf.ModelAttribute(Anything))

    m = Model.create(set={m0})
    assert {m0} == set(m.set)

    m.assign(set=[m0, m1])
    assert {m0, m1} == set(m.set)

    m.assign(set=[m0.id, m1.id, m2.id])
    assert {m0, m1, m2} == set(m.set)

    m.assign(set=[m0, m1])
    assert {m0, m1} == set(m.set)


class AssignAnything(tests.IntAutoModel):
    model = sheraf.ReverseModelAttribute("AssignModel", "set")


class AssignModel(tests.UUIDAutoModel):
    set = sheraf.SetAttribute(sheraf.ModelAttribute(AssignAnything)).index()


def test_set_assign_list_value_indexed(sheraf_connection):
    m0 = AssignAnything.create()
    m1 = AssignAnything.create()
    m2 = AssignAnything.create()

    m = AssignModel.create(set={m0})
    m0 = AssignAnything.read(m0.id)
    assert {m0} == set(m.set)
    assert m in m0.model
    assert m not in m1.model
    assert m not in m2.model

    m.assign(set=[m0, m1])
    m0 = AssignAnything.read(m0.id)
    m1 = AssignAnything.read(m1.id)
    assert {m0, m1} == set(m.set)
    assert m in m0.model
    assert m in m1.model
    assert m not in m2.model

    m.assign(set=[m0.id, m1.id, m2.id])
    m0 = AssignAnything.read(m0.id)
    m1 = AssignAnything.read(m1.id)
    m2 = AssignAnything.read(m2.id)
    assert {m0, m1, m2} == set(m.set)
    assert m in m0.model
    assert m in m1.model
    assert m in m2.model

    m.assign(set=[m0, m1])
    m0 = AssignAnything.read(m0.id)
    m1 = AssignAnything.read(m1.id)
    assert {m0, m1} == set(m.set)
    assert m in m0.model
    assert m in m1.model
    assert m not in m2.model


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
@pytest.mark.parametrize("subattribute", [None, sheraf.StringAttribute()])
def test_indexation(sheraf_database, persistent_type, subattribute):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(
            subattribute,
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True) as conn:
        m = Model.create(set=["foo", "bar"])
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["set"]["foo"]
        )
        assert {m.raw_identifier: m.mapping} == dict(
            conn.root()[Model.table]["set"]["bar"]
        )
        assert [m] == list(Model.search(set="foo"))


@pytest.mark.skip
@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_nested_indexation(sheraf_database, persistent_type):
    class Model(tests.UUIDAutoModel):
        set = sheraf.SetAttribute(
            sheraf.SetAttribute(
                sheraf.StringAttribute(),
                persistent_type=persistent_type,
            ),
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True) as conn:
        m = Model.create(set=[["foo", "bar"], ["baz"]])
        assert m.mapping in conn.root()[Model.table]["set"]["foo"]
        assert m.mapping in conn.root()[Model.table]["set"]["bar"]
        assert m.mapping in conn.root()[Model.table]["set"]["baz"]
        assert [m] == list(Model.search(set="foo"))


@pytest.mark.skip
@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_nested_model_indexation(sheraf_database, persistent_type):
    class Submodel(tests.UUIDAutoModel):
        pass

    class Model(tests.UUIDAutoModel):
        submodels = sheraf.SetAttribute(
            sheraf.ModelAttribute(Submodel),
            persistent_type=persistent_type,
        ).index()

    with sheraf.connection(commit=True):
        sub = Submodel.create()
        m = Model.create(submodels={sub})
        assert [m] == Model.search(submodels=sub)


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_int_to_collection(sheraf_connection, persistent_type):
    class Model(tests.UUIDAutoModel):
        foobar = sheraf.IntegerAttribute()

    m = Model.create(foobar=10)
    assert m.foobar == 10

    class Model(tests.UUIDAutoModel):
        foobar = sheraf.SetAttribute(
            attribute=sheraf.IntegerAttribute(), persistent_type=persistent_type
        )

    m = Model.read(m.id)
    assert m.foobar == {10}

    m.foobar = {10, 11}
    assert m.foobar == {10, 11}

    m = Model.read(m.id)
    assert m.foobar == {10, 11}


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_string_to_collection(sheraf_connection, persistent_type):
    class Model(tests.UUIDAutoModel):
        foobar = sheraf.StringAttribute()

    m = Model.create(foobar="baz")
    assert m.foobar == "baz"

    class Model(tests.UUIDAutoModel):
        foobar = sheraf.SetAttribute(
            attribute=sheraf.StringAttribute(), persistent_type=persistent_type
        )

    m = Model.read(m.id)
    assert m.foobar == {"baz"}

    m.foobar = {"baz", "lorem"}
    assert m.foobar == {"baz", "lorem"}

    m = Model.read(m.id)
    assert m.foobar == {"baz", "lorem"}


@pytest.mark.parametrize("persistent_type", [sheraf.types.Set, set])
def test_model_to_collection(sheraf_connection, persistent_type):
    class SubModel(tests.UUIDAutoModel):
        pass

    class Model(tests.UUIDAutoModel):
        foobar = sheraf.ModelAttribute(SubModel)

    s = SubModel.create()
    m = Model.create(foobar=s)
    assert m.foobar == s

    class Model(tests.UUIDAutoModel):
        foobar = sheraf.SetAttribute(
            attribute=sheraf.ModelAttribute(SubModel), persistent_type=persistent_type
        )

    m = Model.read(m.id)
    assert m.foobar == {s}

    t = SubModel.create()
    m.foobar = {s, t}
    assert m.foobar == {s, t}

    m = Model.read(m.id)
    assert m.foobar == {s, t}

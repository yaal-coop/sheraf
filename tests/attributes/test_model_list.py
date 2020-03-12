import pytest

import sheraf


class AModelForTest(sheraf.AutoModel):
    name = sheraf.SimpleAttribute()


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
@pytest.mark.parametrize(
    "model",
    [
        AModelForTest,
        "{}.{}".format(AModelForTest.__module__, AModelForTest.__name__),
        "{}.{}".format(AModelForTest.__module__, AModelForTest.__name__).encode(
            "utf-8"
        ),
    ],
)
def test_model_dict(sheraf_connection, attribute, list_type, model):
    class AnotherModelForTest(sheraf.AutoModel):
        a_list_for_test = attribute(sheraf.ModelAttribute(AModelForTest))

    a = AModelForTest.create()
    b = AModelForTest.create()

    another = AnotherModelForTest.create()
    assert [] == list(another.a_list_for_test)
    assert 0 == len(another.a_list_for_test)
    assert not another.a_list_for_test
    with pytest.raises(IndexError):
        another.a_list_for_test[5]

    another.a_list_for_test.append(a)
    another.a_list_for_test.append(b)

    _another = AnotherModelForTest.read(another.id)
    assert [a, b] == list(_another.a_list_for_test)
    assert 2 == len(_another.a_list_for_test)
    assert b == _another.a_list_for_test[1]
    assert [b] == list(_another.a_list_for_test[1:])
    assert a in _another.a_list_for_test
    assert b in _another.a_list_for_test
    assert not (AModelForTest.create() in _another.a_list_for_test)
    assert another.a_list_for_test

    c = AModelForTest.create()
    d = AModelForTest.create()
    _another.a_list_for_test.extend([c, d])
    assert [a, b, c, d] == list(_another.a_list_for_test)

    other = AnotherModelForTest.create()
    other.a_list_for_test.extend([b, c])
    assert [b, c] == list(other.a_list_for_test)

    other.a_list_for_test.remove(b)
    assert [c] == list(other.a_list_for_test)

    another.a_list_for_test = [a, b]
    _another = AnotherModelForTest.read(another.id)
    assert [a, b] == list(_another.a_list_for_test)

    assert b == another.a_list_for_test.pop()
    assert [a] == list(another.a_list_for_test)

    _another.a_list_for_test.clear()
    assert [] == list(_another.a_list_for_test)


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_indices(sheraf_connection, attribute, list_type):
    class MyModel(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    model = MyModel.create()
    with pytest.raises(IndexError):
        model.models[0]

    with pytest.raises(IndexError):
        model.models[0] = AModelForTest.create()

    with pytest.raises(IndexError):
        model.models[-1]

    with pytest.raises(IndexError):
        model.models[-1] = AModelForTest.create()

    submodel = AModelForTest.create()
    model.models.append(submodel)
    assert model.models[0] == submodel
    model.models[0] = AModelForTest.create()

    with pytest.raises(IndexError):
        model.models[1]

    with pytest.raises(IndexError):
        model.models[1] = AModelForTest.create()

    with pytest.raises((TypeError, IndexError)):
        model.models["foo"]

    with pytest.raises((TypeError, IndexError)):
        model.models["foo"] = AModelForTest.create()


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_create(sheraf_database, attribute, list_type):
    class ModelForTest(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = ModelForTest.create(models=[{"name": "A"}, {"name": "B"}])
        assert isinstance(model.mapping["models"], list_type)
        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[0].mapping, sheraf.types.SmallDict)
        assert "A" == model.models[0].name

    with sheraf.connection():
        model = ModelForTest.read(model.id)
        assert isinstance(model.mapping["models"], list_type)
        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[0].mapping, sheraf.types.SmallDict)
        assert "A" == model.models[0].name


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_edition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "c"}, {"name": "c"}])
        last_sub_id = model.models[0].id

    with sheraf.connection(commit=True):
        model.edit(value={"models": [{"name": "a"}, {"name": "b"}]}, edition=True)

        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[1], AModelForTest)
        x, y = list(model.models)
        assert "a" == x.name
        assert "b" == y.name
        assert model.models[0].id == last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[1], AModelForTest)
        x, y = list(model.models)
        assert "a" == x.name
        assert "b" == y.name
        assert model.models[0].id == last_sub_id


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_no_edition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "c"}, {"name": "c"}])
        last_sub_id = model.models[0].id

    with sheraf.connection(commit=True):
        model.edit(value={"models": [{"name": "a"}, {"name": "b"}]}, edition=False)

        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[1], AModelForTest)
        x, y = list(model.models)
        assert "c" == x.name
        assert "c" == y.name
        assert model.models[0].id == last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[1], AModelForTest)
        x, y = list(model.models)
        assert "c" == x.name
        assert "c" == y.name
        assert model.models[0].id == last_sub_id


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_replacement(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "c"}, {"name": "c"}])
        last_sub_id = model.models[0].id

    with sheraf.connection(commit=True):
        model.edit(value={"models": [{"name": "a"}, {"name": "b"}]}, replacement=True)

        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[1], AModelForTest)
        x, y = list(model.models)
        assert "a" == x.name
        assert "b" == y.name
        assert model.models[0].id != last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.models[0], AModelForTest)
        assert isinstance(model.models[1], AModelForTest)
        x, y = list(model.models)
        assert "a" == x.name
        assert "b" == y.name
        assert model.models[0].id != last_sub_id


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_addition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"models": [{"name": "a"}, {"name": "b"}]}, addition=True)

        assert isinstance(model.mapping["models"], list_type)
        assert isinstance(model.models[1], AModelForTest)
        assert isinstance(model.models[1].mapping, sheraf.types.SmallDict)
        assert "a" == model.models[0].name
        assert "b" == model.models[1].name

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], list_type)
        assert isinstance(model.models[1], AModelForTest)
        assert isinstance(model.models[1].mapping, sheraf.types.SmallDict)
        assert "a" == model.models[0].name
        assert "b" == model.models[1].name


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_no_addition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"models": [{"name": "a"}, {"name": "b"}]}, addition=False)

        assert isinstance(model.mapping["models"], list_type)
        assert "a" == model.models[0].name
        assert len(model.models) == 1

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], list_type)
        assert "a" == model.models[0].name
        assert len(model.models) == 1


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_deletion(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"models": []}, deletion=True)

        assert isinstance(model.mapping["models"], list_type)
        assert 0 == len(model.models)

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], list_type)
        assert 0 == len(model.models)


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_no_deletion(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        models = attribute(sheraf.ModelAttribute(AModelForTest))

    with sheraf.connection(commit=True):
        model = Model.create(models=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"models": []}, deletion=False)

        assert isinstance(model.mapping["models"], list_type)
        assert 1 == len(model.models)

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], list_type)
        assert 1 == len(model.models)

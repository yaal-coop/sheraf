import pytest

import sheraf


class ListInlineModel(sheraf.InlineModel):
    name = sheraf.SimpleAttribute()


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_inline_model_list(sheraf_connection, attribute, list_type):
    class ModelForTest(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    _model = ModelForTest.create()
    assert not _model.inlines
    assert list() == list(_model.inlines)
    assert 0 == len(_model.inlines)

    _a = ListInlineModel.create(name="a")
    _model.inlines.append(_a)
    _b = ListInlineModel.create(name="b")
    _model.inlines.append(_b)
    assert _model.inlines

    [__a, __b] = _model.inlines
    assert "a" == __a.name
    assert "b" == __b.name
    assert 2 == len(_model.inlines)
    assert _a in _model.inlines
    assert not (ListInlineModel.create() in _model.inlines)

    assert __a == _model.inlines[0]

    _other = ListInlineModel.create()
    assert _other not in _model.inlines

    assert [__a, __b] == list(_model.inlines[:])

    assert _b == _model.inlines.pop()
    assert 1 == len(_model.inlines)

    _model.inlines.clear()
    assert not _model.inlines


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_model_absolute_string(sheraf_connection, attribute, list_type):
    class ModelForTest(sheraf.AutoModel):
        inline = attribute(
            sheraf.InlineModelAttribute(
                "{}.{}".format(ListInlineModel.__module__, ListInlineModel.__name__)
            )
        )

    _model = ModelForTest.create()
    _model.inline.append(ListInlineModel.create())
    _model = ModelForTest.read(_model.id)
    assert isinstance(_model.inline[0], ListInlineModel)


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_model_invalid_string(sheraf_connection, attribute, list_type):
    class ModelForTest(sheraf.AutoModel):
        inline = attribute(sheraf.InlineModelAttribute("anticonstitutionnellement"))

    model = ModelForTest.create()
    with pytest.raises(ImportError):
        model.inline.append({"name": "YEAH"})


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_extend(sheraf_connection, attribute, list_type):
    class MyModel(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    model = MyModel.create()
    inline = ListInlineModel.create()
    model.inlines.append(inline)
    extend_inlines = [ListInlineModel.create(), ListInlineModel.create()]
    model.inlines.extend(extend_inlines)
    assert len(model.inlines) == 3
    assert model.inlines[0] == inline
    assert model.inlines[1] == extend_inlines[0]
    assert model.inlines[2] == extend_inlines[1]


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_indices(sheraf_connection, attribute, list_type):
    class MyModel(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    model = MyModel.create()
    with pytest.raises(IndexError):
        model.inlines[0]

    with pytest.raises(IndexError):
        model.inlines[0] = ListInlineModel.create()

    inline = ListInlineModel.create()
    model.inlines.append(inline)
    assert model.inlines[0] == inline
    model.inlines[0] = ListInlineModel.create()

    with pytest.raises(IndexError):
        model.inlines[1]

    with pytest.raises(IndexError):
        model.inlines[1] = ListInlineModel.create()

    with pytest.raises((TypeError, IndexError)):
        model.inlines["foo"]

    with pytest.raises((TypeError, IndexError)):
        model.inlines["foo"] = ListInlineModel.create()


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_create(sheraf_database, attribute, list_type):
    class ModelForTest(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = ModelForTest.create(inlines=[{"name": "A"}, {"name": "B"}])

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model._persistent["inlines"][0], sheraf.types.SmallDict)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert "A" == model.inlines[0].name

    with sheraf.connection():
        model = ModelForTest.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model._persistent["inlines"][0], sheraf.types.SmallDict)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert "A" == model.inlines[0].name


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_edition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "c"}, {"name": "c"}])

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": [{"name": "a"}, {"name": "b"}]}, edition=True)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert isinstance(model.inlines[1], ListInlineModel)
        x, y = list(model.inlines)
        assert "a" == x.name
        assert "b" == y.name

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert isinstance(model.inlines[1], ListInlineModel)
        x, y = list(model.inlines)
        assert "a" == x.name
        assert "b" == y.name


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_no_edition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "c"}, {"name": "c"}])

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": [{"name": "a"}, {"name": "b"}]}, edition=False)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert isinstance(model.inlines[1], ListInlineModel)
        x, y = list(model.inlines)
        assert "c" == x.name
        assert "c" == y.name

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert isinstance(model.inlines[1], ListInlineModel)
        x, y = list(model.inlines)
        assert "c" == x.name
        assert "c" == y.name


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_replacement(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "c"}, {"name": "c"}])

    with sheraf.connection(commit=True):
        old_sub_persistent = model.inlines[0]._persistent
        model.edit(
            value={"inlines": [{"name": "a"}, {"name": "b"}]},
            edition=True,
            replacement=True,
        )
        new_sub_persistent = model.inlines[0]._persistent

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert isinstance(new_sub_persistent, sheraf.types.SmallDict)
        assert "a" == model.inlines[0].name
        assert "b" == model.inlines[1].name
        assert old_sub_persistent is not new_sub_persistent

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[0], ListInlineModel)
        assert isinstance(new_sub_persistent, sheraf.types.SmallDict)
        assert "a" == model.inlines[0].name
        assert "b" == model.inlines[1].name
        assert old_sub_persistent is not new_sub_persistent


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_addition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": [{"name": "a"}, {"name": "b"}]}, addition=True)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[1], ListInlineModel)
        assert isinstance(model.inlines[1]._persistent, sheraf.types.SmallDict)
        assert "a" == model.inlines[0].name
        assert "b" == model.inlines[1].name

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert isinstance(model.inlines[1], ListInlineModel)
        assert isinstance(model.inlines[1]._persistent, sheraf.types.SmallDict)
        assert "a" == model.inlines[0].name
        assert "b" == model.inlines[1].name


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_no_addition(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": [{"name": "a"}, {"name": "b"}]}, addition=False)

        assert isinstance(model._persistent["inlines"], list_type)
        assert "a" == model.inlines[0].name
        assert len(model.inlines) == 1

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert "a" == model.inlines[0].name
        assert len(model.inlines) == 1


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_deletion(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": []}, deletion=True)

        assert isinstance(model._persistent["inlines"], list_type)
        assert 0 == len(model.inlines)

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert 0 == len(model.inlines)


@pytest.mark.parametrize(
    "attribute,list_type",
    [
        (sheraf.SmallListAttribute, sheraf.types.SmallList),
        (sheraf.LargeListAttribute, sheraf.types.LargeList),
    ],
)
def test_update_no_deletion(sheraf_database, attribute, list_type):
    class Model(sheraf.AutoModel):
        inlines = attribute(sheraf.InlineModelAttribute(ListInlineModel))

    with sheraf.connection(commit=True):
        model = Model.create(inlines=[{"name": "a"}])

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": []}, deletion=False)

        assert isinstance(model._persistent["inlines"], list_type)
        assert 1 == len(model.inlines)

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model._persistent["inlines"], list_type)
        assert 1 == len(model.inlines)

import pytest
import sheraf
import tests
from BTrees.IOBTree import IOBTree


class DictInlineModel(sheraf.InlineModel):
    name = sheraf.SimpleAttribute()


def test_inline_model_dict(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    _model = Model.create()
    assert not _model.inlines
    assert 0 == len(_model.inlines)
    assert [] == [_inline for _inline in _model.inlines.values()]

    _inline = DictInlineModel.create()
    _inline.name = "Coucou"
    _model.inlines["a"] = _inline
    assert _model.inlines
    assert 1 == len(_model.inlines)
    assert "a" in _model.inlines
    _count = 0
    for _key in _model.inlines:
        _count += 1
    assert 1 == _count
    assert isinstance(_model.mapping["inlines"], sheraf.types.LargeDict)

    assert _inline == _model.inlines.get("a")
    assert _model.inlines.get("b") is None
    assert "DUMMY" == _model.inlines.get("b", "DUMMY")

    _another = Model.read(_model.id)
    assert _inline == _another.inlines["a"]
    assert "Coucou" == _another.inlines["a"].name

    del _another.inlines["a"]
    with pytest.raises(KeyError):
        _another.inlines["a"]

    with pytest.raises(AttributeError):
        _inline.creation_datetime()
    with pytest.raises(AttributeError):
        _inline.last_update_datetime()


def test_create(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "A"}, "b": {"name": "B"}})
        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.mapping["inlines"]["a"], sheraf.types.SmallDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert "A" == model.inlines["a"].name

    with sheraf.connection():
        model = Model.read(model.id)
        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.mapping["inlines"]["a"], sheraf.types.SmallDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert "A" == model.inlines["a"].name


def test_default_parameter(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.DictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel), persistent_type=IOBTree
        )

    model = Model.create()
    model.inlines[0] = DictInlineModel.create()
    assert isinstance(model.mapping["inlines"], IOBTree)


def test_clear(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    _model = Model.create()
    _inline = DictInlineModel.create()
    _inline.name = "Coucou"
    _model.inlines["a"] = _inline

    _model.inlines.clear()

    assert not _model.inlines
    assert set() == set(_model.inlines)


def test_keys_and_items(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    _model = Model.create()
    _inlineA = DictInlineModel.create()
    _inlineA.name = "Coucou"
    _model.inlines["a"] = _inlineA
    _inlineB = DictInlineModel.create()
    _inlineB.name = "Au revoir"
    _model.inlines["b"] = _inlineB

    assert "a" in _model.inlines
    assert "b" in _model.inlines
    assert not ("c" in _model.inlines)
    assert ["a", "b"] == list(_model.inlines.keys())
    assert [("a", _inlineA), ("b", _inlineB)] == list(_model.inlines.items())
    assert [_inlineA, _inlineB] == list(_model.inlines.values())


def test_model_absolute_string(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute("DictInlineModel")
        )

    _model = Model.create()
    _model.inline["key"] = DictInlineModel.create()
    _model = Model.read(_model.id)
    assert isinstance(_model.inline["key"], DictInlineModel)


def test_model_invalid_string(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute("anticonstitutionnellement")
        )

    model = Model.create()
    model.inline[0] = DictInlineModel.create()
    with pytest.raises(ImportError):
        dict(model.inline)


def test_minKey_and_maxKey(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    _model = Model.create()
    _inlineA = DictInlineModel.create()
    _model.inlines["a"] = _inlineA
    _inlineB = DictInlineModel.create()
    _model.inlines["b"] = _inlineB

    assert _model.inlines.maxKey() == "b"
    assert _model.inlines.minKey() == "a"


def test_update_edition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "c"}, "b": {"name": "c"}})

    with sheraf.connection(commit=True):
        old_submapping = model.inlines["a"].mapping
        model.edit(
            value={"inlines": {"a": {"name": "a"}, "b": {"name": "b"}}}, edition=True
        )
        new_submapping = model.inlines["a"].mapping

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "a" == model.inlines["a"].name
        assert "b" == model.inlines["b"].name
        assert old_submapping is new_submapping

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "a" == model.inlines["a"].name
        assert "b" == model.inlines["b"].name
        assert old_submapping is new_submapping


def test_update_no_edition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "c"}, "b": {"name": "c"}})

    with sheraf.connection(commit=True):
        old_submapping = model.inlines["a"].mapping
        model.edit(
            value={"inlines": {"a": {"name": "a"}, "b": {"name": "b"}}}, edition=False
        )
        new_submapping = model.inlines["a"].mapping

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "c" == model.inlines["a"].name
        assert "c" == model.inlines["b"].name
        assert old_submapping is new_submapping

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "c" == model.inlines["a"].name
        assert "c" == model.inlines["b"].name
        assert old_submapping is new_submapping


def test_update_replacement(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "c"}, "b": {"name": "c"}})

    with sheraf.connection(commit=True):
        old_submapping = model.inlines["a"].mapping
        model.edit(
            value={"inlines": {"a": {"name": "a"}, "b": {"name": "b"}}},
            edition=True,
            replacement=True,
        )
        new_submapping = model.inlines["a"].mapping

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "a" == model.inlines["a"].name
        assert "b" == model.inlines["b"].name
        assert old_submapping is not new_submapping

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["a"], DictInlineModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "a" == model.inlines["a"].name
        assert "b" == model.inlines["b"].name
        assert old_submapping is not new_submapping


def test_update_addition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": {"b": {"name": "b"}}}, addition=False)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert "b" not in model.inlines

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert "b" not in model.inlines


def test_update_no_addition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": {"b": {"name": "b"}}}, addition=True)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["b"], DictInlineModel)
        assert isinstance(model.inlines["b"].mapping, sheraf.types.SmallDict)
        assert "a" == model.inlines["a"].name
        assert "b" == model.inlines["b"].name

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert isinstance(model.inlines["b"], DictInlineModel)
        assert isinstance(model.inlines["b"].mapping, sheraf.types.SmallDict)
        assert "a" == model.inlines["a"].name
        assert "b" == model.inlines["b"].name


def test_update_deletion(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": {}}, deletion=True)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert "a" not in model.inlines

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert "a" not in model.inlines


def test_update_no_deletion(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.LargeDictAttribute(
            sheraf.InlineModelAttribute(DictInlineModel)
        )

    with sheraf.connection(commit=True):
        model = Model.create(inlines={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"inlines": {}}, deletion=False)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert "a" in model.inlines

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["inlines"], sheraf.types.LargeDict)
        assert "a" in model.inlines

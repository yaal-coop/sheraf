import pytest

import sheraf
import tests


class AModel(tests.UUIDAutoModel):
    name = sheraf.SimpleAttribute()


@pytest.mark.parametrize(
    "model",
    [
        AModel,
        "{}.{}".format(AModel.__module__, AModel.__name__),
        "{}.{}".format(AModel.__module__, AModel.__name__).encode("utf-8"),
    ],
)
def test_model_dict(sheraf_connection, model):
    class AnotherModel(tests.UUIDAutoModel):
        a_dict_for_test = sheraf.LargeDictAttribute(sheraf.ModelAttribute(model))

    a = AModel.create()
    b = AModel.create()

    another = AnotherModel.create()
    assert {} == dict(another.a_dict_for_test)
    another.a_dict_for_test.clear()
    assert {} == dict(another.a_dict_for_test)
    assert 0 == len(another.a_dict_for_test)
    with pytest.raises(KeyError):
        another.a_dict_for_test["a"]

    another.a_dict_for_test["a"] = a
    another.a_dict_for_test["b"] = b

    _another = AnotherModel.read(another.id)
    assert _another.a_dict_for_test["a"] == a
    assert _another.a_dict_for_test["b"] == b
    assert {"a": a, "b": b} == dict(_another.a_dict_for_test)
    assert 2 == len(_another.a_dict_for_test)
    assert "a" in _another.a_dict_for_test
    assert "b" in _another.a_dict_for_test
    assert not ("c" in _another.a_dict_for_test)
    assert ["a", "b"] == list(another.a_dict_for_test.keys())
    assert [("a", a), ("b", b)] == list(another.a_dict_for_test.items())
    assert [a, b] == list(another.a_dict_for_test.values())

    c = iter(another.a_dict_for_test)
    assert {"a", "b"} == {next(c), next(c)}

    del _another.a_dict_for_test["a"]
    assert {"b": b} == dict(_another.a_dict_for_test)
    assert 1 == len(another.a_dict_for_test)

    _another.a_dict_for_test.clear()
    assert {} == dict(_another.a_dict_for_test)

    another.a_dict_for_test = {"a": a, "b": b}
    _another = AnotherModel.read(another.id)
    assert {"a": a, "b": b} == dict(_another.a_dict_for_test)


def test_error_if_delete_a_nonexisting_key(sheraf_connection):
    class _AnotherModel(tests.UUIDAutoModel):
        a_dict_for_test = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    another = _AnotherModel.create()
    with pytest.raises(KeyError):
        del another.a_dict_for_test["a"]


def test_create(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "A"}, "b": {"name": "B"}})
        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["a"], AModel)
        assert isinstance(model.models["a"].mapping, sheraf.types.SmallDict)
        assert "A" == model.models["a"].name

    with sheraf.connection():
        model = Model.read(model.id)
        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["a"], AModel)
        assert isinstance(model.models["a"].mapping, sheraf.types.SmallDict)
        assert "A" == model.models["a"].name


def test_update_edition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "c"}, "b": {"name": "c"}})
        last_sub_id = model.models["a"].id

    with sheraf.connection(commit=True):
        model.edit(value={"models": {"a": {"name": "a"}, "b": {"name": "b"}}})

        assert isinstance(model.models["a"], AModel)
        assert isinstance(model.models["b"], AModel)
        assert "a" == model.models["a"].name
        assert "b" == model.models["b"].name
        assert last_sub_id == model.models["a"].id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.models["a"], AModel)
        assert isinstance(model.models["b"], AModel)
        assert "a" == model.models["a"].name
        assert "b" == model.models["b"].name
        assert last_sub_id == model.models["a"].id


def test_update_no_edition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "c"}, "b": {"name": "c"}})
        last_sub_id = model.models["a"].id

    with sheraf.connection(commit=True):
        old_submapping = model.models["a"].mapping
        model.edit(
            value={"models": {"a": {"name": "a"}, "b": {"name": "b"}}}, edition=False
        )
        new_submapping = model.models["a"].mapping

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["a"], AModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "c" == model.models["a"].name
        assert "c" == model.models["b"].name
        assert old_submapping is new_submapping
        assert last_sub_id == model.models["a"].id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["a"], AModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "c" == model.models["a"].name
        assert "c" == model.models["b"].name
        assert old_submapping is new_submapping
        assert last_sub_id == model.models["a"].id


def test_update_replacement(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "c"}, "b": {"name": "c"}})
        last_sub_id = model.models["a"].id

    with sheraf.connection(commit=True):
        old_submapping = model.models["a"].mapping
        model.edit(
            value={"models": {"a": {"name": "a"}, "b": {"name": "b"}}},
            edition=True,
            replacement=True,
        )
        new_submapping = model.models["a"].mapping

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["a"], AModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "a" == model.models["a"].name
        assert "b" == model.models["b"].name
        assert old_submapping is not new_submapping
        assert last_sub_id != model.models["a"].id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["a"], AModel)
        assert isinstance(new_submapping, sheraf.types.SmallDict)
        assert "a" == model.models["a"].name
        assert "b" == model.models["b"].name
        assert old_submapping is not new_submapping
        assert last_sub_id != model.models["a"].id


def test_update_addition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"models": {"b": {"name": "b"}}}, addition=False)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert "b" not in model.models

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert "b" not in model.models


def test_update_no_addition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"models": {"b": {"name": "b"}}}, addition=True)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["b"], AModel)
        assert isinstance(model.models["b"].mapping, sheraf.types.SmallDict)
        assert "a" == model.models["a"].name
        assert "b" == model.models["b"].name

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert isinstance(model.models["b"], AModel)
        assert isinstance(model.models["b"].mapping, sheraf.types.SmallDict)
        assert "a" == model.models["a"].name
        assert "b" == model.models["b"].name


def test_update_deletion(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"models": {}}, deletion=True)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert "a" not in model.models

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert "a" not in model.models


def test_update_no_deletion(sheraf_database):
    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.ModelAttribute(AModel))

    with sheraf.connection(commit=True):
        model = Model.create(models={"a": {"name": "a"}})

    with sheraf.connection(commit=True):
        model.edit(value={"models": {}}, deletion=False)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert "a" in model.models

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(model.mapping["models"], sheraf.types.LargeDict)
        assert "a" in model.models

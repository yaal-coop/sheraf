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
def test_set_attribute(sheraf_connection, model):
    class AnotherModel(tests.UUIDAutoModel):
        a_set_for_test = sheraf.SetAttribute(sheraf.ModelAttribute(model))

    a = AModel.create()
    b = AModel.create()

    another = AnotherModel.create()
    assert set() == set(another.a_set_for_test)
    another.a_set_for_test.clear()
    assert set() == set(another.a_set_for_test)
    assert 0 == len(another.a_set_for_test)

    another.a_set_for_test.add(a)
    another.a_set_for_test.add(b)

    _another = AnotherModel.read(another.id)
    assert 2 == len(_another.a_set_for_test)
    assert a in _another.a_set_for_test
    assert b in _another.a_set_for_test
    assert not (AModel.create() in _another.a_set_for_test)

    _another = AnotherModel.read(another.id)
    _another.a_set_for_test.remove(b)
    assert 1 == len(another.a_set_for_test)
    assert a in _another.a_set_for_test
    assert b not in _another.a_set_for_test

    _another.a_set_for_test.clear()
    assert set() == set(_another.a_set_for_test)

    another.a_set_for_test = {a, b}
    _another = AnotherModel.read(another.id)
    assert {a, b} == set(_another.a_set_for_test)


@pytest.mark.skip
def test_update_edition(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        models = sheraf.SetAttribute(sheraf.ModelAttribute(AModel))

    model = Model.create(models={{"name": "c"}, {"name": "c"}})
    model.edit(value={"models": [{"name": "a"}, {"name": "b"}]})

    x, y = model.models
    assert isinstance(x, AModel)
    assert isinstance(y, AModel)
    assert {"a", "b"} == {x.name, y.name}

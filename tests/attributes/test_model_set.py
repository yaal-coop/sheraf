import pytest

import sheraf


class AModelForTest(sheraf.AutoModel):
    name = sheraf.SimpleAttribute()


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
def test_set_attribute(sheraf_connection, model):
    class AnotherModelForTest(sheraf.AutoModel):
        a_set_for_test = sheraf.SetAttribute(sheraf.ModelAttribute(model))

    a = AModelForTest.create()
    b = AModelForTest.create()

    another = AnotherModelForTest.create()
    assert set() == set(another.a_set_for_test)
    another.a_set_for_test.clear()
    assert set() == set(another.a_set_for_test)
    assert 0 == len(another.a_set_for_test)

    another.a_set_for_test.add(a)
    another.a_set_for_test.add(b)

    _another = AnotherModelForTest.read(another.id)
    assert 2 == len(_another.a_set_for_test)
    assert a in _another.a_set_for_test
    assert b in _another.a_set_for_test
    assert not (AModelForTest.create() in _another.a_set_for_test)

    _another = AnotherModelForTest.read(another.id)
    _another.a_set_for_test.remove(b)
    assert 1 == len(another.a_set_for_test)
    assert a in _another.a_set_for_test
    assert b not in _another.a_set_for_test

    _another.a_set_for_test.clear()
    assert set() == set(_another.a_set_for_test)

    another.a_set_for_test = {a, b}
    _another = AnotherModelForTest.read(another.id)
    assert {a, b} == set(_another.a_set_for_test)


@pytest.mark.skip
def test_update_edition(sheraf_connection):
    class Model(sheraf.AutoModel):
        models = sheraf.SetAttribute(sheraf.ModelAttribute(AModelForTest))

    model = Model.create(models={{"name": "c"}, {"name": "c"}})
    model.edit(value={"models": [{"name": "a"}, {"name": "b"}]})

    x, y = model.models
    assert isinstance(x, AModelForTest)
    assert isinstance(y, AModelForTest)
    assert {"a", "b"} == {x.name, y.name}

import pytest
import sheraf
import tests


class SetInlineModel(sheraf.InlineModel):
    name = sheraf.SimpleAttribute()


def test_inline_model_set(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.SetAttribute(sheraf.InlineModelAttribute(SetInlineModel))

    _model = Model.create()
    assert not _model.inlines
    assert set() == set(_model.inlines)

    _inline = SetInlineModel.create()
    _inline.name = "Coucou"
    _model.inlines.add(_inline)
    assert _model.inlines

    _inline = list(_model.inlines)[0]
    assert "Coucou" == _inline.name
    assert 1 == len(_model.inlines)
    assert _inline in _model.inlines
    assert not (SetInlineModel.create() in _model.inlines)

    _other = SetInlineModel.create()
    assert _other not in _model.inlines

    _model.inlines.clear()
    assert not _model.inlines
    assert set() == set(_model.inlines)


def test_model_absolute_string(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.SetAttribute(sheraf.InlineModelAttribute("SetInlineModel"))

    _model = Model.create()
    _model.inline.add(SetInlineModel.create())
    _model = Model.read(_model.id)
    assert isinstance(list(_model.inline)[0], SetInlineModel)


def test_model_invalid_string(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.SetAttribute(
            sheraf.InlineModelAttribute("anticonstitutionnellement")
        )

    model = Model.create()

    with pytest.raises(ImportError):
        model.inline.add({"name": "YOLO"})


@pytest.mark.skip
def test_update_edition(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inlines = sheraf.SetAttribute(sheraf.InlineModelAttribute(SetInlineModel))

    model = Model.create()
    model.edit({"inlines": [{"name": "a"}, {"name": "b"}]})

    x, y = model.inlines
    assert isinstance(x, SetInlineModel)
    assert isinstance(y, SetInlineModel)
    assert {"a", "b"} == {x.name, y.name}

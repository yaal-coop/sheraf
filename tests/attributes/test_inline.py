import pytest
import sheraf
import tests


class InlineModel(sheraf.InlineModel):
    name = sheraf.SimpleAttribute()


def test_simple_inline_model(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    class AnotherModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    _model = Model.create()
    assert isinstance(_model.inline, InlineModel)

    _model.inline.name = "test"

    _model_reread = Model.read(_model.id)
    assert "test" == _model_reread.inline.name

    _model.inline.name = "test2"

    _model_reread = Model.read(_model.id)
    assert "test2" == _model_reread.inline.name

    _another_model = AnotherModel.create()
    _another_model.inline.name = "test3"

    _another_model_reread = AnotherModel.read(_another_model.id)
    assert "test3" == _another_model_reread.inline.name
    _model_reread = Model.read(_model.id)
    assert "test2" == _model_reread.inline.name

    _inlined = _model.inline

    _inlined.name = "test4"
    _model_reread = Model.read(_model.id)
    assert "test4" == _model_reread.inline.name


def test_default_none(sheraf_connection):
    class AModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(model=InlineModel, default=None)

    m = AModel.create()
    assert m.inline is None


def test_create_none(sheraf_connection):
    class AModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(model=InlineModel)

    m = AModel.create(inline=None)
    assert m.inline is None


def test_write(sheraf_connection):
    class AModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    model = AModel.create()
    model.inline = inline = InlineModel.create()

    assert inline == model.inline
    assert inline == AModel.read(model.id).inline


def test_model_absolute_string(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute("tests.attributes.test_inline.InlineModel")

    _model = Model.create()
    assert isinstance(_model.inline, InlineModel)


def test_model_invalid_string(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute("anticonstitutionnellement")

    model = Model.create()

    with pytest.raises(ImportError):
        model.inline


def test_create(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = Model.create(inline={"name": "A"})
        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(model.inline, InlineModel)
        assert "A" == model.inline.name

    with sheraf.connection():
        model = Model.read(model.id)
        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(model.inline, InlineModel)
        assert "A" == model.inline.name


def test_update_edition(sheraf_database):
    class AModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = AModel.create()

    with sheraf.connection(commit=True):
        oldmapping = model.inline.mapping
        model.edit(value={"inline": {"name": "YEAH"}}, edition=True)
        newmapping = model.inline.mapping

        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert oldmapping is newmapping

    with sheraf.connection():
        model = AModel.read(model.id)

        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert oldmapping is newmapping


def test_update_no_edition(sheraf_database):
    class AModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = AModel.create(inline={"name": "foobar"})

    with sheraf.connection(commit=True):
        oldmapping = model.inline.mapping
        model.edit(value={"inline": {"name": "YEAH"}}, edition=False)
        newmapping = model.inline.mapping

        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "foobar" == AModel.read(model.id).inline.name
        assert oldmapping is newmapping

    with sheraf.connection():
        model = AModel.read(model.id)

        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "foobar" == AModel.read(model.id).inline.name
        assert oldmapping is newmapping


def test_update_replacement(sheraf_database):
    class AModel(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = AModel.create()

    with sheraf.connection(commit=True):
        oldmapping = model.inline.mapping
        model.edit(value={"inline": {"name": "YEAH"}}, replacement=True)
        newmapping = model.inline.mapping

        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert oldmapping is not newmapping

    with sheraf.connection():
        model = AModel.read(model.id)

        assert isinstance(model.mapping["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert oldmapping is not newmapping


def test_anonymous_inline_model(sheraf_database):
    class Model(tests.UUIDAutoModel):
        inline = sheraf.InlineModelAttribute(
            sheraf.InlineModel(name=sheraf.SimpleAttribute())
        )

    with sheraf.connection(commit=True):
        m = Model.create(inline={"name": "George Abitbol"})
        assert "<Model.inline>" == repr(m.inline)
        assert isinstance(m.inline, sheraf.InlineModel)
        assert {"name": "George Abitbol"} == dict(m.inline.mapping)
        assert "George Abitbol" == m.inline.name

    with sheraf.connection():
        m = Model.read(m.id)
        assert isinstance(m.inline, sheraf.InlineModel)
        assert {"name": "George Abitbol"} == dict(m.inline.mapping)
        assert "George Abitbol" == m.inline.name


def test_inline_model_update(sheraf_database):
    class MyInline(sheraf.InlineModel):
        foo = sheraf.SimpleAttribute()

    class Model(tests.UUIDAutoModel):
        bar = sheraf.InlineModelAttribute(MyInline)

    with sheraf.connection(commit=True):
        m = Model.create()
        m.bar.foo = "foo"

        m.update(bar={"foo": "foobar"})

    with sheraf.connection():
        assert "foobar" == Model.read(m.id).bar.foo

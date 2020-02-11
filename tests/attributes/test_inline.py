import pytest

import sheraf


class InlineModel(sheraf.InlineModel):
    name = sheraf.SimpleAttribute()


def test_simple_inline_model(sheraf_connection):
    class ModelForTest(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    class AnotherModelForTest(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    _model = ModelForTest.create()
    assert isinstance(_model.inline, InlineModel)

    _model.inline.name = "test"

    _model_reread = ModelForTest.read(_model.id)
    assert "test" == _model_reread.inline.name

    _model.inline.name = "test2"

    _model_reread = ModelForTest.read(_model.id)
    assert "test2" == _model_reread.inline.name

    _another_model = AnotherModelForTest.create()
    _another_model.inline.name = "test3"

    _another_model_reread = AnotherModelForTest.read(_another_model.id)
    assert "test3" == _another_model_reread.inline.name
    _model_reread = ModelForTest.read(_model.id)
    assert "test2" == _model_reread.inline.name

    _inlined = _model.inline

    _inlined.name = "test4"
    _model_reread = ModelForTest.read(_model.id)
    assert "test4" == _model_reread.inline.name


def test_default_none(sheraf_connection):
    class AModel(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(model=InlineModel, default=None)

    m = AModel.create()
    assert m.inline is None


def test_create_none(sheraf_connection):
    class AModel(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(model=InlineModel)

    m = AModel.create(inline=None)
    assert m.inline is None


def test_write(sheraf_connection):
    class AModel(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    model = AModel.create()
    model.inline = inline = InlineModel.create()

    assert inline == model.inline
    assert inline == AModel.read(model.id).inline


def test_model_absolute_string(sheraf_connection):
    class ModelForTest(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute("tests.attributes.test_inline.InlineModel")

    _model = ModelForTest.create()
    assert isinstance(_model.inline, InlineModel)


def test_model_invalid_string(sheraf_connection):
    class ModelForTest(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute("anticonstitutionnellement")

    model = ModelForTest.create()

    with pytest.raises(ImportError):
        model.inline


def test_create(sheraf_database):
    class ModelForTest(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = ModelForTest.create(inline={"name": "A"})
        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(model.inline, InlineModel)
        assert "A" == model.inline.name

    with sheraf.connection():
        model = ModelForTest.read(model.id)
        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(model.inline, InlineModel)
        assert "A" == model.inline.name


def test_update_edition(sheraf_database):
    class AModel(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = AModel.create()

    with sheraf.connection(commit=True):
        old_persistent = model.inline._persistent
        model.edit(value={"inline": {"name": "YEAH"}}, edition=True)
        new_persistent = model.inline._persistent

        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert old_persistent is new_persistent

    with sheraf.connection():
        model = AModel.read(model.id)

        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert old_persistent is new_persistent


def test_update_no_edition(sheraf_database):
    class AModel(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = AModel.create(inline={"name": "foobar"})

    with sheraf.connection(commit=True):
        old_persistent = model.inline._persistent
        model.edit(value={"inline": {"name": "YEAH"}}, edition=False)
        new_persistent = model.inline._persistent

        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "foobar" == AModel.read(model.id).inline.name
        assert old_persistent is new_persistent

    with sheraf.connection():
        model = AModel.read(model.id)

        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "foobar" == AModel.read(model.id).inline.name
        assert old_persistent is new_persistent


def test_update_replacement(sheraf_database):
    class AModel(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(InlineModel)

    with sheraf.connection(commit=True):
        model = AModel.create()

    with sheraf.connection(commit=True):
        old_persistent = model.inline._persistent
        model.edit(value={"inline": {"name": "YEAH"}}, replacement=True)
        new_persistent = model.inline._persistent

        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert old_persistent is not new_persistent

    with sheraf.connection():
        model = AModel.read(model.id)

        assert isinstance(model._persistent["inline"], sheraf.types.SmallDict)
        assert isinstance(AModel.read(model.id).inline, InlineModel)
        assert "YEAH" == AModel.read(model.id).inline.name
        assert old_persistent is not new_persistent


def test_anonymous_inline_model(sheraf_database):
    class Model(sheraf.AutoModel):
        inline = sheraf.InlineModelAttribute(
            sheraf.InlineModel(name=sheraf.SimpleAttribute())
        )

    with sheraf.connection(commit=True):
        m = Model.create(inline={"name": "George Abitbol"})
        assert isinstance(m.inline, sheraf.InlineModel)
        assert "George Abitbol" == m.inline.name

    with sheraf.connection():
        m = Model.read(m.id)
        assert isinstance(m.inline, sheraf.InlineModel)
        assert "George Abitbol" == m.inline.name


def test_inline_model_update(sheraf_database):
    class MyInline(sheraf.InlineModel):
        foo = sheraf.SimpleAttribute()

    class MyModel(sheraf.AutoModel):
        bar = sheraf.InlineModelAttribute(MyInline)

    with sheraf.connection(commit=True):
        m = MyModel.create()
        m.bar.foo = "foo"

        m.update(bar={"foo": "foobar"})

    with sheraf.connection():
        assert "foobar" == MyModel.read(m.id).bar.foo

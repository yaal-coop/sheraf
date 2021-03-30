import sheraf
import tests


def test_inline_model_list_update(sheraf_database):
    class MyInline(sheraf.InlineModel):
        foo = sheraf.SimpleAttribute()

    class Model(tests.UUIDAutoModel):
        models = sheraf.SmallListAttribute(sheraf.InlineModelAttribute(MyInline))

    with sheraf.connection(commit=True):
        m_up = Model.create(
            models=[MyInline.create(foo="foo"), MyInline.create(foo="bar")]
        )
        m_del = Model.create(
            models=[MyInline.create(foo="foo"), MyInline.create(foo="bar")]
        )
        m_add = Model.create(
            models=[MyInline.create(foo="foo"), MyInline.create(foo="bar")]
        )

        m_up.update(models=[{"foo": "foobar"}, {"foo": "foobar"}])
        m_del.update(models=[{"foo": "foo"}])
        m_add.update(models=[{"foo": "foo"}, {"foo": "bar"}, {"foo": "foobar"}])

    with sheraf.connection():
        m_up = Model.read(m_up.id)
        assert len(m_up.models) == 2
        assert "foobar" == m_up.models[0].foo
        assert "foobar" == m_up.models[1].foo

        m_del = Model.read(m_del.id)
        assert len(m_del.models) == 2
        assert "foo" == m_del.models[0].foo
        assert "bar" == m_del.models[1].foo

        m_add = Model.read(m_add.id)
        assert len(m_add.models) == 3
        assert "foo" == m_add.models[0].foo
        assert "bar" == m_add.models[1].foo
        assert "foobar" == m_add.models[2].foo


def test_inline_model_dict_update(sheraf_database):
    class MyInline(sheraf.InlineModel):
        foo = sheraf.SimpleAttribute()

    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(MyInline))

    with sheraf.connection(commit=True):
        m_up = Model.create(
            models={"a": MyInline.create(foo="foo"), "b": MyInline.create(foo="bar")}
        )
        m_del = Model.create(
            models={"a": MyInline.create(foo="foo"), "b": MyInline.create(foo="bar")}
        )
        m_add = Model.create(
            models={"a": MyInline.create(foo="foo"), "b": MyInline.create(foo="bar")}
        )

        m_up.update(models={"a": {"foo": "foobar"}, "b": {"foo": "foobar"}})
        m_del.update(models={"a": {"foo": "foo"}})
        m_add.update(
            models={"a": {"foo": "foo"}, "b": {"foo": "bar"}, "c": {"foo": "foobar"}}
        )

    with sheraf.connection():
        m_up = Model.read(m_up.id)
        assert len(m_up.models) == 2
        assert "foobar" == m_up.models["a"].foo
        assert "foobar" == m_up.models["b"].foo

        m_del = Model.read(m_del.id)
        assert len(m_del.models) == 2
        assert "foo" == m_del.models["a"].foo
        assert "bar" == m_del.models["b"].foo

        m_add = Model.read(m_add.id)
        assert len(m_add.models) == 3
        assert "foo" == m_add.models["a"].foo
        assert "bar" == m_add.models["b"].foo
        assert "foobar" == m_add.models["c"].foo


def test_inline_model_list_assign(sheraf_database):
    class MyInline(sheraf.InlineModel):
        foo = sheraf.SimpleAttribute()

    class Model(tests.UUIDAutoModel):
        models = sheraf.SmallListAttribute(sheraf.InlineModelAttribute(MyInline))

    with sheraf.connection(commit=True):
        m_up = Model.create(
            models=[MyInline.create(foo="foo"), MyInline.create(foo="bar")]
        )
        m_del = Model.create(
            models=[MyInline.create(foo="foo"), MyInline.create(foo="bar")]
        )
        m_add = Model.create(
            models=[MyInline.create(foo="foo"), MyInline.create(foo="bar")]
        )

        m_up.assign(models=[{"foo": "foobar"}, {"foo": "foobar"}])
        m_del.assign(models=[{"foo": "foo"}])
        m_add.assign(models=[{"foo": "foo"}, {"foo": "bar"}, {"foo": "foobar"}])

    with sheraf.connection():
        m_up = Model.read(m_up.id)
        assert len(m_up.models) == 2
        assert "foobar" == m_up.models[0].foo
        assert "foobar" == m_up.models[1].foo

        m_del = Model.read(m_del.id)
        assert len(m_del.models) == 1
        assert "foo" == m_del.models[0].foo

        m_add = Model.read(m_add.id)
        assert len(m_add.models) == 3
        assert "foo" == m_add.models[0].foo
        assert "bar" == m_add.models[1].foo
        assert "foobar" == m_add.models[2].foo


def test_inline_model_dict_assign(sheraf_database):
    class MyInline(sheraf.InlineModel):
        foo = sheraf.SimpleAttribute()

    class Model(tests.UUIDAutoModel):
        models = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(MyInline))

    with sheraf.connection(commit=True):
        m_up = Model.create(
            models={"a": MyInline.create(foo="foo"), "b": MyInline.create(foo="bar")}
        )
        m_del = Model.create(
            models={"a": MyInline.create(foo="foo"), "b": MyInline.create(foo="bar")}
        )
        m_add = Model.create(
            models={"a": MyInline.create(foo="foo"), "b": MyInline.create(foo="bar")}
        )

        m_up.assign(models={"a": {"foo": "foobar"}, "b": {"foo": "foobar"}})
        m_del.assign(models={"a": {"foo": "foo"}})
        m_add.assign(
            models={"a": {"foo": "foo"}, "b": {"foo": "bar"}, "c": {"foo": "foobar"}}
        )

    with sheraf.connection():
        m_up = Model.read(m_up.id)
        assert len(m_up.models) == 2
        assert "foobar" == m_up.models["a"].foo
        assert "foobar" == m_up.models["b"].foo

        m_del = Model.read(m_del.id)
        assert len(m_del.models) == 1
        assert "foo" == m_del.models["a"].foo

        m_add = Model.read(m_add.id)
        assert len(m_add.models) == 3
        assert "foo" == m_add.models["a"].foo
        assert "bar" == m_add.models["b"].foo
        assert "foobar" == m_add.models["c"].foo

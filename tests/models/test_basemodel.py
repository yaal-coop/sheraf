import mock
import pytest
import sheraf
import tests


def test_delete_attributes(sheraf_connection):
    class M(tests.UUIDAutoModel):
        foo = sheraf.StringAttribute()

    m = M.create()
    m.foo = "foo"
    m.bar = "bar"

    assert "foo" == m.foo
    assert "bar" == m.bar

    del m.foo
    del m.bar

    assert "" == m.foo

    with pytest.raises(AttributeError):
        m.bar


class MyInlineModel(sheraf.InlineModel):
    pass


class MyModel(tests.UUIDAutoModel):
    inline_model = sheraf.InlineModelAttribute(MyInlineModel)


def test_attribute_error_attribute(sheraf_database):
    class MyBadModel(tests.UUIDAutoModel):
        @property
        def my_bad_attribute(self):
            raise AttributeError("it is too bad")

    with sheraf.connection():
        m = MyBadModel.create()

        with pytest.raises(AttributeError, match=r"it is too bad"):
            m.my_bad_attribute


def test_attribute_error_attribute_with_nasty_message(sheraf_database):
    class MyBadModel(tests.UUIDAutoModel):
        @property
        def my_bad_attribute(self):
            raise AttributeError("object has no attribute NIARK NIARK")

    with sheraf.connection():
        m = MyBadModel.create()

        with pytest.raises(
            AttributeError, match=r"object has no attribute NIARK NIARK"
        ):
            m.my_bad_attribute


@pytest.mark.skip
def test_attribute_error_attribute_with_very_nasty_message(
    sheraf_database,
):  # pragma: no cover
    class MyBadModel(tests.UUIDAutoModel):
        @property
        def my_bad_attribute(self):
            raise AttributeError(
                "NIARK object has no attribute 'my_bad_attribute' NIARK NIARK"
            )

    with sheraf.connection():
        m = MyBadModel.create()

        with pytest.raises(
            AttributeError,
            match=r"NIARK object has no attribute 'my_bad_attribute' NIARK NIARK",
        ):
            m.my_bad_attribute


def test_create_nominal_case(sheraf_database):
    class FooModel(tests.UUIDAutoModel):
        pass

    with sheraf.connection(commit=True):
        FooModel.create()

    with sheraf.connection():
        with pytest.raises(TypeError):
            FooModel.create(toto=True)


def test_create_parameters(sheraf_database):
    class BarModel(tests.UUIDAutoModel):
        my_attribute = sheraf.SimpleAttribute(default="hell yeah")

    with sheraf.connection(commit=True):
        m = BarModel.create()
        assert m.my_attribute == "hell yeah"

    with sheraf.connection(commit=True):
        m = BarModel.create(my_attribute="hell no")
        assert m.my_attribute == "hell no"

    with sheraf.connection():
        with pytest.raises(TypeError):
            BarModel.create(toto=True)


def test_lazy_create_parameters(sheraf_database):
    class FoobarModel(tests.UUIDAutoModel):
        my_attribute = sheraf.SimpleAttribute(default="hell yeah", lazy=False)

    with sheraf.connection(commit=True):
        m = FoobarModel.create()
        assert m.my_attribute == "hell yeah"

    with sheraf.connection(commit=True):
        m = FoobarModel.create(my_attribute="hell no")
        assert m.my_attribute == "hell no"

    with sheraf.connection():
        with pytest.raises(TypeError):
            FoobarModel.create(toto=True)


def test_lazy(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        myattribute = sheraf.attributes.simples.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create()

    with sheraf.connection():
        assert not m.attributes["myattribute"].is_created(m)


def test_not_lazy(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        myattribute = sheraf.attributes.simples.SimpleAttribute(lazy=False)

    with sheraf.connection(commit=True):
        m = MyModel.create()

    with sheraf.connection():
        assert m.attributes["myattribute"].is_created(m)


def test_dict_interface(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    with sheraf.connection():
        m = MyModel.create(foo="bar")

        assert "bar" == m["foo"]
        m["foo"] = "foobar"
        assert "foobar" == m["foo"]
        assert "foobar" == m.foo
        assert "foo" in m

        m.a = "foobar"
        assert "foobar" == m.a
        assert "a" not in m
        with pytest.raises(KeyError):
            m["a"]

        with pytest.raises(KeyError):
            m["a"] = "yolo"


def test_model_as_simple_dict(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()
        mylist = sheraf.LargeListAttribute()

    with sheraf.connection():
        m = MyModel.create(foo="bar", mylist=[0, 1, 2])

        assert {
            "_creation": mock.ANY,
            "foo": "bar",
            "mylist": [0, 1, 2],
            "id": mock.ANY,
        } == dict(m)

        assert all(item in dict(m).items() for item in m.items())


def test_model_as_nested_dicts(sheraf_database):
    class DummyModel(tests.UUIDAutoModel):
        pass

    class MyModel(tests.UUIDAutoModel):
        other = sheraf.ModelAttribute(DummyModel)

    with sheraf.connection():
        dummy = DummyModel.create()
        m = MyModel.create(other=dummy)
        n = MyModel.create()

        assert {"_creation": mock.ANY, "other": dummy, "id": mock.ANY} == dict(m)
        assert {"_creation": mock.ANY, "other": None, "id": mock.ANY} == dict(n)


def test_model_as_nested_inline_dicts(sheraf_database):
    class DummyModel(sheraf.InlineModel):
        pass

    class MyModel(tests.UUIDAutoModel):
        other = sheraf.InlineModelAttribute(DummyModel)

    with sheraf.connection():
        dummy = DummyModel.create()
        m = MyModel.create(other=dummy)

        assert {"_creation": mock.ANY, "other": dummy, "id": mock.ANY} == dict(m)


def test_simple_edit(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(foo="bar")
        m.edit({"foo": "foobar"})

    with sheraf.connection():
        m = MyModel.read(m.id)
        assert "foobar" == m.foo


def test_simple_update(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(foo="bar")
        m.update(foo="foobar")

    with sheraf.connection():
        m = MyModel.read(m.id)
        assert "foobar" == m.foo


def test_simple_update_wrong_attribute(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        pass

    with sheraf.connection(commit=True):
        m = MyModel.create()

        with pytest.raises(TypeError):
            m.update(foo="foobar")


def test_list_update(sheraf_database):
    class MyModel(tests.UUIDAutoModel):
        foo = sheraf.SmallListAttribute()

    with sheraf.connection(commit=True):
        m_up = MyModel.create(foo=[1])
        m_add = MyModel.create(foo=[1])

        m_up.update(foo=[2])
        m_add.update(foo=[1, 2])

    with sheraf.connection():
        assert [2] == MyModel.read(m_up.id).foo
        assert [1, 2] == MyModel.read(m_add.id).foo


def test_attribute_inheritance(sheraf_connection):
    class A(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute(default="foo_A")
        bar = sheraf.SimpleAttribute(default="bar_A")

    class B(A):
        foo = sheraf.IntegerAttribute(default=33)

    b = B.create()
    assert 33 == b.foo
    assert "bar_A" == b.bar


def test_abstract_inheritance(sheraf_connection):
    class A(sheraf.BaseModel):
        foo = sheraf.SimpleAttribute(default="foo")

    class B(A, sheraf.DatedNamedAttributesModel):
        bar = sheraf.SimpleAttribute(default="bar")

    b = B.create()
    assert "foo" == b.foo
    assert "bar" == b.bar


def test_copy(sheraf_connection):
    class A(tests.UUIDAutoModel):
        foo = sheraf.StringAttribute()

    a1 = A.create(foo="YEAH")
    a2 = a1.copy()

    assert a1.foo == a2.foo
    assert a1.id != a2.id
    assert a1 != a2


def test_reset_simple_value(sheraf_database):
    class M(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute(default=None)

    with sheraf.connection(commit=True):
        m = M.create(foo="foo")
        mid = m.id
        assert "foo" == m.foo

    with sheraf.connection():
        m = M.read(mid)
        assert "foo" == m.foo
        m.reset("foo")
        assert m.foo is None


def test_reset_callable(sheraf_database):
    class M(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute(default=lambda: None)

    with sheraf.connection(commit=True):
        m = M.create(foo="foo")
        mid = m.id
        assert "foo" == m.foo

    with sheraf.connection():
        m = M.read(mid)
        assert "foo" == m.foo
        m.reset("foo")
        assert m.foo is None

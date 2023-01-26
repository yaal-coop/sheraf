import pytest
import sheraf
import tests


class CustomIndexationModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True, index_keys_func=lambda string: {string.lower() if string else None}
    )
    bar = sheraf.SimpleAttribute()
    barindex = sheraf.Index("bar", key="bar")


class CustomIndexationModelB(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        index_keys_func=lambda string: {string.lower() if string else None},
    )
    barindex = sheraf.Index("bar", key="bar")


class CustomIndexationModelC(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index("foo", key="foo", unique=True)
    barindex = sheraf.Index("bar", key="bar")

    @fooindex.index_keys_func()
    def fooindex_values(self, value):
        return {value.lower() if value else None}


class CustomIndexationModelD(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index("foo", key="foo", unique=True)
    barindex = sheraf.Index("bar", key="bar")

    @fooindex.index_keys_func
    def fooindex_values(self, value):
        return {value.lower() if value else None}


class CustomIndexationModelE(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(foo, key="foo", unique=True)
    barindex = sheraf.Index(bar, key="bar")

    @fooindex.index_keys_func
    def fooindex_values(self, value):
        return {value.lower() if value else None}


class CustomIndexationModelF(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(foo, key="foo", unique=True)
    barindex = sheraf.Index(bar, key="bar")

    @fooindex.index_keys_func
    def fooindex_values(self, value):
        return value.lower() if value else None


class CustomIndexationModelG(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(unique=True)
    bar = sheraf.SimpleAttribute().index()

    @foo.index_keys_func
    @foo.search_keys_func
    def fooindex_values(self, value):
        return value.lower() if value else None


@pytest.mark.parametrize(
    "Model",
    [
        CustomIndexationModelA,
        CustomIndexationModelB,
        CustomIndexationModelC,
        CustomIndexationModelD,
        CustomIndexationModelE,
        CustomIndexationModelF,
        CustomIndexationModelG,
    ],
)
def test_custom_indexation_method(sheraf_database, Model):
    with sheraf.connection(commit=True):
        m = Model.create(foo="FOO", bar="BAR")
        func = Model.indexes["foo"].details.default_index_keys_func
        assert func is not None
        assert {"foo"} == Model.indexes["foo"].details.get_index_keys(
            m, [Model.attributes["foo"]], func
        )
        assert {"foo"} == m.index_keys("foo")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["foo"]
        assert {"foo"} == set(index_table)
        assert m.mapping == index_table["foo"]

        assert [m] == list(Model.filter(foo="foo"))
        assert [] == list(Model.filter(foo="FOO"))

        assert [m] == list(Model.filter(foo="foo", bar="BAR"))
        assert [] == list(Model.filter(foo="foo", bar="bar"))

        assert [m] == list(Model.search(foo="foo"))
        assert [m] == list(Model.search(foo="FOO"))

        assert [m] == list(Model.search(foo="foo", bar="BAR"))
        assert [m] == list(Model.search(foo="FOO", bar="BAR"))

        assert [] == list(Model.search(foo="foo", bar="bar"))
        assert [] == list(Model.search(foo="FOO", bar="bar"))

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(foo="FOO")


def test_default_indexation_method(sheraf_database):
    class ModelA(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index()

    assert (
        ModelA.indexes["foo"].details.default_index_keys_func
        == ModelA.attributes["foo"].index_keys
    )

    class ModelB(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        fooindex = sheraf.Index("foo")

    assert ModelB.indexes["fooindex"].details.default_index_keys_func is None


class CustomSearchModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True,
        index_keys_func=lambda string: {string.lower()},
        search_keys_func=lambda string: [string.lower()[::-1], string.lower()],
    )
    bar = sheraf.SimpleAttribute().index()


class CustomSearchModelB(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        index_keys_func=lambda string: {string.lower()},
        search_keys_func=lambda string: [string.lower()[::-1], string.lower()],
    )

    barindex = sheraf.Index("bar", key="bar")


class CustomSearchModelC(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        index_keys_func=lambda string: {string.lower()},
    )

    barindex = sheraf.Index("bar", key="bar")

    @fooindex.search_keys_func()
    def search_foo(self, value):
        return [value.lower()[::-1], value.lower()]


class CustomSearchModelD(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        index_keys_func=lambda string: {string.lower()},
    )

    barindex = sheraf.Index("bar", key="bar")

    @fooindex.search_keys_func
    def search_foo(self, value):
        return [value.lower()[::-1], value.lower()]


class CustomSearchModelE(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        foo,
        key="foo",
        unique=True,
        index_keys_func=lambda string: {string.lower()},
    )

    barindex = sheraf.Index(bar, key="bar")

    @fooindex.search_keys_func
    def search_foo(self, value):
        return [value.lower()[::-1], value.lower()]


class CustomSearchModelF(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True,
        index_keys_func=lambda string: {string.lower()},
    )
    bar = sheraf.SimpleAttribute().index()

    @foo.search_keys_func
    def search_foo(self, value):
        return [value.lower()[::-1], value.lower()]


@pytest.mark.parametrize(
    "Model",
    [
        CustomSearchModelA,
        CustomSearchModelB,
        CustomSearchModelC,
        CustomSearchModelD,
        CustomSearchModelE,
        CustomSearchModelF,
    ],
)
def test_custom_query_method(sheraf_database, Model):
    with sheraf.connection(commit=True):
        m = Model.create(foo="FOO", bar="BAR")
        assert ["oof", "foo"] == Model.search_keys(foo="foo")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["foo"]
        assert {"foo"} == set(index_table)
        assert m.mapping == index_table["foo"]

        assert [m] == list(Model.search(foo="oof"))
        assert m.is_indexed_with(foo="oof")
        assert [m] == list(Model.search(foo="foo"))
        assert m.is_indexed_with(foo="foo")
        assert [m] == list(Model.search(foo="OOF"))
        assert m.is_indexed_with(foo="OOF")
        assert [m] == list(Model.search(foo="FOO"))
        assert m.is_indexed_with(foo="FOO")

        assert [m] == list(Model.search(foo="oof", bar="BAR"))
        assert m.is_indexed_with(foo="oof", bar="BAR")
        assert [m] == list(Model.search(foo="OOF", bar="BAR"))
        assert m.is_indexed_with(foo="OOF", bar="BAR")

        assert [] == list(Model.search(foo="oof", bar="bar"))
        assert not m.is_indexed_with(foo="oof", bar="bar")
        assert [] == list(Model.search(foo="OOF", bar="bar"))
        assert not m.is_indexed_with(foo="OOF", bar="bar")

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(foo="FOO")


def test_default_search_method(sheraf_database):
    class ModelA(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index()

    assert (
        ModelA.indexes["foo"].details._search_keys_func
        == ModelA.attributes["foo"].search_keys
    )

    class ModelB(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        fooindex = sheraf.Index("foo")

    assert ModelB.indexes["fooindex"].details._search_keys_func is None

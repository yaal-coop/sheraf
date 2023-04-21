import pytest
import sheraf
import tests


def test_common_index(sheraf_database):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()
        theindex = sheraf.Index(foo, bar)

    with sheraf.connection(commit=True):
        m = Model.create(foo="foo", bar="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["theindex"]
        assert {"foo", "bar"} == Model.indexes["theindex"].details.get_model_index_keys(
            m
        )
        assert {"foo", "bar"} == set(index_table)
        assert {m.raw_identifier: m.mapping} == dict(index_table["foo"])
        assert {m.raw_identifier: m.mapping} == dict(index_table["bar"])

        assert [m] == list(Model.read_these(theindex=["foo"]))
        assert [m] == list(Model.read_these(theindex=["bar"]))

        assert [m] == Model.search(theindex="foo")
        assert [m] == Model.search(theindex="bar")


def test_common_index_unique(sheraf_database):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()
        theindex = sheraf.Index(foo, bar, unique=True)

    with sheraf.connection(commit=True):
        Model.create(foo="foo", bar="bar")

        # This behavior can seem strange
        Model.create(foo="anything", bar="anything")

    with sheraf.connection():
        with pytest.raises(sheraf.UniqueIndexException):
            Model.create(foo="bar")

        with pytest.raises(sheraf.UniqueIndexException):
            Model.create(bar="foo")


class CommonModelDifferentValuesMethodsA(tests.IntAutoModel):
    foo = sheraf.StringAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar)

    @theindex.index_keys_func("foo")
    def lower(self, foo):
        return {foo.lower()}

    @theindex.index_keys_func("bar")
    def upper(self, bar):
        return {bar.upper()}


class CommonModelDifferentValuesMethodsB(tests.IntAutoModel):
    foo = sheraf.StringAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar)

    @theindex.index_keys_func(foo)
    def lower(self, foo):
        return {foo.lower()}

    @theindex.index_keys_func(bar)
    def upper(self, bar):
        return {bar.upper()}


@pytest.mark.parametrize(
    "Model",
    (
        CommonModelDifferentValuesMethodsA,
        CommonModelDifferentValuesMethodsB,
    ),
)
def test_common_index_different_values_methods(sheraf_database, Model):
    assert Model.indexes["theindex"].details.index_keys_funcs[Model.lower] == [
        [Model.attributes["foo"]]
    ]
    assert Model.indexes["theindex"].details.index_keys_funcs[Model.upper] == [
        [Model.attributes["bar"]]
    ]
    assert Model.indexes["theindex"].details.index_keys_funcs[None] == []
    assert Model.indexes["theindex"].details.default_index_keys_func is None
    assert Model.indexes["theindex"].details._search_keys_func is None

    with sheraf.connection(commit=True) as conn:
        m = Model.create(foo="FOo", bar="bAr")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["theindex"]
        assert {"foo", "BAR"} == set(index_table)
        assert {m.raw_identifier: m.mapping} == dict(index_table["foo"])
        assert {m.raw_identifier: m.mapping} == dict(index_table["BAR"])

        assert [m] == list(Model.read_these(theindex=["foo"]))
        assert [m] == list(Model.read_these(theindex=["BAR"]))

        assert [m] == Model.search(theindex="foo")
        assert [m] == Model.search(theindex="BAR")

        assert [] == Model.search(theindex="FOo")
        assert [] == Model.search(theindex="bAr")


class CommonModelDefaultValuesMethodsA(tests.IntAutoModel):
    def lower(self, value):
        return {value.lower()}

    foo = sheraf.StringAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar, index_keys_func=lower)

    @theindex.index_keys_func(bar)
    def upper(self, bar):
        return {bar.upper()}


class CommonModelDefaultValuesMethodsB(tests.IntAutoModel):
    foo = sheraf.StringAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar)

    @theindex.index_keys_func
    def lower(self, value):
        return {value.lower()}

    @theindex.index_keys_func(bar)
    def upper(self, bar):
        return {bar.upper()}


@pytest.mark.parametrize(
    "Model", (CommonModelDefaultValuesMethodsA, CommonModelDefaultValuesMethodsB)
)
def test_common_index_default_values_methods(sheraf_database, Model):
    assert Model.indexes["theindex"].details.index_keys_funcs[Model.upper] == [
        [Model.attributes["bar"]]
    ]
    assert Model.indexes["theindex"].details.default_index_keys_func == Model.lower
    assert Model.indexes["theindex"].details._search_keys_func == Model.lower

    with sheraf.connection(commit=True) as conn:
        m = Model.create(foo="FOo", bar="bAr")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["theindex"]
        assert {"foo", "BAR"} == set(index_table)
        assert {m.raw_identifier: m.mapping} == dict(index_table["foo"])
        assert {m.raw_identifier: m.mapping} == dict(index_table["BAR"])

        assert [m] == list(Model.read_these(theindex=["foo"]))
        assert [m] == list(Model.read_these(theindex=["BAR"]))

        assert [m] == Model.filter(theindex="foo")
        assert [m] == Model.filter(theindex="BAR")

        assert [m] == Model.search(theindex="foo")
        assert [m] == Model.search(theindex="FOo")
        assert [] == Model.search(theindex="BAR")
        assert [] == Model.search(theindex="bAr")


class CommonValuesComputedSeparatelyModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar)

    @theindex.index_keys_func(foo)
    @theindex.index_keys_func(bar)
    def index_keys(self, x):
        return {x.upper()}


@pytest.mark.parametrize(
    "Model",
    (CommonValuesComputedSeparatelyModelA,),
)
def test_common_index_common_values_computed_separately(sheraf_database, Model):
    with sheraf.connection(commit=True):
        m = Model.create(foo="Hello", bar="world!")
        assert m in Model.filter(theindex="HELLO")
        assert m in Model.filter(theindex="WORLD!")


class CommonValuesComputedTogetherModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar)

    @theindex.index_keys_func(foo, bar)
    def theindex_values(self, foo, bar):
        return {f"{foo} {bar}"}


class CommonValuesComputedTogetherModelB(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()
    theindex = sheraf.Index(foo, bar)

    @theindex.index_keys_func(foo, bar)
    def theindex_values(self, foo_, bar_):
        return {f"{foo_} {bar_}"}


@pytest.mark.parametrize(
    "Model",
    (
        CommonValuesComputedTogetherModelA,
        CommonValuesComputedTogetherModelB,
    ),
)
def test_common_index_common_values_computed_together(sheraf_connection, Model):
    m = Model.create(foo="Hello", bar="world!")
    assert {"Hello world!"} == Model.indexes["theindex"].details.get_model_index_keys(m)
    assert m in Model.search(theindex="Hello world!")


def test_common_index_complex(sheraf_database):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()
        theindex = sheraf.Index(foo, bar)

        @theindex.index_keys_func
        def index_keys(self, value):
            return {value.lower(), value.upper()}

    with sheraf.connection(commit=True) as conn:
        m = Model.create(foo="foo", bar="bar")
        assert {"foo", "bar", "FOO", "BAR"} == set(conn.root()[Model.table]["theindex"])

        m.bar = "baz"
        assert {"foo", "baz", "FOO", "BAZ"} == set(conn.root()[Model.table]["theindex"])

    with sheraf.connection(commit=True) as conn:
        m = Model.read(m.id)
        assert {"foo", "baz", "FOO", "BAZ"} == set(conn.root()[Model.table]["theindex"])

        m.foo = "OOF"
        assert {"oof", "baz", "OOF", "BAZ"} == set(conn.root()[Model.table]["theindex"])

        del m.foo
        assert {"baz", "BAZ"} == set(conn.root()[Model.table]["theindex"])

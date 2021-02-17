import BTrees.OOBTree
import pytest
import warnings
import sheraf
import sheraf.exceptions
import tests


# ----------------------------------------------------------------------------
# Types
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "instance, mapping",
    [
        (sheraf.IntegerAttribute().index(unique=True), BTrees.LOBTree.LOBTree),
        # ( sheraf.IntegerAttribute().index(unique=True, key="my_int"), BTrees.IOBTree.IOBTree)
        (
            sheraf.SimpleAttribute(default=int).index(unique=True),
            BTrees.OOBTree.OOBTree,
        ),
    ],
)
def test_integer_unique_index_creation(sheraf_database, instance, mapping):
    class Model(tests.IntAutoModel):
        my_attribute = instance

    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute=22)

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {22} == set(index_table)
        assert mfoo.mapping == index_table[22]

        assert isinstance(index_table, mapping)


# ----------------------------------------------------------------------------
# Unique Index
# ----------------------------------------------------------------------------


class UniqueModelA(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute().index(unique=True)


class UniqueModelB(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    my_attribute_index = sheraf.Index("my_attribute", unique=True, key="my_attribute")


class UniqueModelC(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    my_attribute_index = sheraf.Index(my_attribute, unique=True, key="my_attribute")


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation(sheraf_database, Model):
    assert (
        Model.attributes["my_attribute"]
        == Model.indexes["my_attribute"].details.attribute
    )

    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar = Model.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo.mapping == index_table["foo"]
        assert mbar.mapping == index_table["bar"]

        assert mbar == Model.read(my_attribute="bar")
        assert [mbar] == list(Model.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(Model.read_these(my_attribute=["bar", "foo"]))

        # Model._read_unique_index = mock.MagicMock(
        #    side_effect=Model._read_unique_index
        # )
        assert [mbar] == Model.filter(my_attribute="bar")
        # Model._read_unique_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation_and_edition(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="FOO")
        mbar = Model.create(my_attribute="BAR")

    with sheraf.connection(commit=True):
        Model.read(mfoo.id).my_attribute = "foo"
        Model.read(mbar.id).my_attribute = "bar"

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo.mapping == index_table["foo"]
        assert mbar.mapping == index_table["bar"]

        assert mbar == Model.read(my_attribute="bar")
        assert [mbar] == list(Model.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(Model.read_these(my_attribute=["bar", "foo"]))

        # Model._read_unique_index = mock.MagicMock(
        #    side_effect=Model._read_unique_index
        # )
        assert [mbar] == Model.filter(my_attribute="bar")
        # Model._read_unique_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation_and_deletion(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar = Model.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == Model.filter(my_attribute="foo")
        assert [mbar] == Model.filter(my_attribute="bar")


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_double_value(sheraf_database, Model):
    with sheraf.connection(commit=True):
        Model.create(my_attribute="foo")

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(my_attribute="foo")


def test_unique_indexation_on_model_attribute(sheraf_database):
    class DummyModel(sheraf.Model):
        table = "dummymodel_table"
        v = sheraf.SimpleAttribute(lazy=False, default=str)

    class Model(sheraf.Model):
        table = "model_table"
        dummy_attribute = sheraf.ModelAttribute(DummyModel, lazy=False).index(
            unique=True, values=lambda x: {x.v}
        )

    with sheraf.connection(commit=True):
        foo = DummyModel.create(v="fou")
        Model.create(dummy_attribute=foo)

    with sheraf.connection() as conn:
        index_table = conn.root()["model_table"]["dummy_attribute"]
        assert {"fou"} == set(index_table)


def test_unique_index_set_afterwards(sheraf_database):
    class DummyModel(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index(
            values=lambda foo: {foo.lower()} if foo else {}
        )

    with sheraf.connection(commit=True):
        dummy = DummyModel.create()
        dummy.foo = "bar"

    with sheraf.connection():
        assert [dummy] == list(DummyModel.filter(foo="bar"))


# ---------------------------------------------------------------------------------
# Multiple Indexes
# ---------------------------------------------------------------------------------
class MultipleModelA(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute().index()


class MultipleModelB(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    my_attribute_index = sheraf.Index("my_attribute", key="my_attribute")


class MultipleModelC(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    my_attribute_index = sheraf.Index(my_attribute, key="my_attribute")


@pytest.mark.parametrize(
    "Model",
    [
        MultipleModelA,
        MultipleModelB,
        MultipleModelC,
    ],
)
def test_multiple_index_creation(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar1 = Model.create(my_attribute="bar")
        mbar2 = Model.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert [mfoo.mapping] == list(index_table["foo"])
        assert [mbar1.mapping, mbar2.mapping] == list(index_table["bar"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            Model.read(my_attribute="bar")
        assert [mbar1, mbar2] == list(Model.read_these(my_attribute=["bar"]))

        # Model._read_multiple_index = mock.MagicMock(
        #    side_effect=Model._read_multiple_index
        # )
        assert [mbar1, mbar2] == Model.filter(my_attribute="bar")
        # Model._read_multiple_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


@pytest.mark.parametrize(
    "Model",
    [
        MultipleModelA,
        MultipleModelB,
        MultipleModelC,
    ],
)
def test_multiple_index_creation_and_deletion(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar1 = Model.create(my_attribute="bar")
        mbar2 = Model.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()
        mbar2.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == Model.filter(my_attribute="foo")
        assert [mbar1] == Model.filter(my_attribute="bar")


def test_multiple_index_several_filters(sheraf_database):
    class Model(tests.IntAutoModel):
        my_attribute_1 = sheraf.SimpleAttribute().index()
        my_attribute_2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Model.create(my_attribute_1="foo", my_attribute_2="foo")
        Model.create(my_attribute_1="bar", my_attribute_2="bar")
        m = Model.create(my_attribute_1="foo", my_attribute_2="bar")

    with sheraf.connection():
        assert [m] == Model.filter(my_attribute_1="foo").filter(my_attribute_2="bar")


def test_multiple_index_ordering(sheraf_database):
    class MultipleAllModel(tests.IntAutoModel):
        my_attribute_1 = sheraf.SimpleAttribute().index()
        my_attribute_2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        maa = MultipleAllModel.create(my_attribute_1="a", my_attribute_2="a")
        mab = MultipleAllModel.create(my_attribute_1="a", my_attribute_2="b")
        mba = MultipleAllModel.create(my_attribute_1="b", my_attribute_2="a")
        mbb = MultipleAllModel.create(my_attribute_1="b", my_attribute_2="b")

    with sheraf.connection():
        assert [mab, maa, mbb, mba] == MultipleAllModel.order(
            my_attribute_1=sheraf.ASC
        ).order(my_attribute_2=sheraf.DESC)


def test_index_key(sheraf_database):
    class IndexKeyModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(key="another_index_key")

    with sheraf.connection(commit=True):
        mfoo = IndexKeyModel.create(my_attribute="foo")

    with sheraf.connection() as conn:
        index_table = conn.root()[IndexKeyModel.table]["another_index_key"]
        assert {"foo"} == set(index_table)
        assert [mfoo.mapping] == list(index_table["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            IndexKeyModel.read(another_index_key="foo")
        assert [mfoo] == list(IndexKeyModel.read_these(another_index_key=["foo"]))

        # IndexKeyModel._read_multiple_index = mock.MagicMock(
        #    side_effect=IndexKeyModel._read_multiple_index
        # )
        assert [mfoo] == IndexKeyModel.filter(another_index_key="foo")
        # IndexKeyModel._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "another_index_key")]
        # )


class MultipleKeysIndexModelA(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute().index(key="key_1").index(key="key_2")


class MultipleKeysIndexModelB(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    key_1 = sheraf.Index("my_attribute")
    key_2 = sheraf.Index("my_attribute")


class MultipleKeysIndexModelC(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    key_1 = sheraf.Index(my_attribute)
    key_2 = sheraf.Index(my_attribute)


@pytest.mark.parametrize(
    "Model",
    [
        MultipleKeysIndexModelA,
        MultipleKeysIndexModelB,
        MultipleKeysIndexModelC,
    ],
)
def test_multiple_keys_index_create(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")

    with sheraf.connection() as conn:
        index_table_key_1 = conn.root()[Model.table]["key_1"]
        index_table_key_2 = conn.root()[Model.table]["key_2"]
        assert {"foo"} == set(index_table_key_1)
        assert [mfoo.mapping] == list(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert [mfoo.mapping] == list(index_table_key_2["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            Model.read(key_1="foo")
        assert [mfoo] == list(Model.read_these(key_1=["foo"]))

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            Model.read(key_2="foo")
        assert [mfoo] == list(Model.read_these(key_2=["foo"]))

        # Model._read_multiple_index = mock.MagicMock(
        #    side_effect=Model._read_multiple_index
        # )
        assert [mfoo] == Model.filter(key_1="foo")
        # Model._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )

        assert [mfoo] == Model.filter(key_2="foo")
        # Model._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )


@pytest.mark.parametrize(
    "Model",
    [
        MultipleKeysIndexModelA,
        MultipleKeysIndexModelB,
    ],
)
def test_multiple_keys_index_update(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo = Model.read(mfoo.id)
        mfoo.my_attribute = "foo"

    with sheraf.connection() as conn:
        index_table_key_1 = conn.root()[Model.table]["key_1"]
        index_table_key_2 = conn.root()[Model.table]["key_2"]
        assert {"foo"} == set(index_table_key_1)
        assert [mfoo.mapping] == list(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert [mfoo.mapping] == list(index_table_key_2["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            Model.read(key_1="foo")
        assert [mfoo] == list(Model.read_these(key_1=["foo"]))

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            Model.read(key_2="foo")
        assert [mfoo] == list(Model.read_these(key_2=["foo"]))

        # Model._read_multiple_index = mock.MagicMock(
        #    side_effect=Model._read_multiple_index
        # )
        assert [mfoo] == Model.filter(key_1="foo")
        # Model._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )

        assert [mfoo] == Model.filter(key_2="foo")
        # Model._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )


# ---------------------------------------------------------------------------------
# Custom methods
# ---------------------------------------------------------------------------------


class CustomIndexationModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True, values=lambda string: {string.lower()}
    )
    bar = sheraf.SimpleAttribute()
    barindex = sheraf.Index("bar", key="bar")


class CustomIndexationModelB(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo", key="foo", unique=True, values=lambda string: {string.lower()}
    )
    barindex = sheraf.Index("bar", key="bar")


class CustomIndexationModelC(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index("foo", key="foo", unique=True)
    barindex = sheraf.Index("bar", key="bar")

    @fooindex.values()
    def fooindex_values(self, value):
        return {value.lower()}


class CustomIndexationModelD(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index("foo", key="foo", unique=True)
    barindex = sheraf.Index("bar", key="bar")

    @fooindex.values
    def fooindex_values(self, value):
        return {value.lower()}


class CustomIndexationModelE(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(foo, key="foo", unique=True)
    barindex = sheraf.Index(bar, key="bar")

    @fooindex.values
    def fooindex_values(self, value):
        return {value.lower()}


@pytest.mark.parametrize(
    "Model",
    [
        CustomIndexationModelA,
        CustomIndexationModelB,
        CustomIndexationModelC,
        CustomIndexationModelD,
        CustomIndexationModelE,
    ],
)
def test_custom_indexation_method(sheraf_database, Model):
    with sheraf.connection(commit=True):
        m = Model.create(foo="FOO", bar="BAR")
        assert Model.indexes["foo"].details._values_func is not None
        assert {"foo"} == Model.indexes["foo"].details.get_values(m, "FOO")

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

    assert ModelA.indexes["foo"].details._values_func == ModelA.attributes["foo"].values

    class ModelB(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        fooindex = sheraf.Index("foo")

    assert ModelB.indexes["fooindex"].details._values_func is None


class CustomSearchModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True,
        values=lambda string: {string.lower()},
        search=lambda string: [string.lower()[::-1], string.lower()],
    )
    bar = sheraf.SimpleAttribute().index()


class CustomSearchModelB(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        values=lambda string: {string.lower()},
        search=lambda string: [string.lower()[::-1], string.lower()],
    )

    barindex = sheraf.Index("bar", key="bar")


class CustomSearchModelC(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        values=lambda string: {string.lower()},
    )

    barindex = sheraf.Index("bar", key="bar")

    @fooindex.search()
    def search_foo(self, value):
        return [value.lower()[::-1], value.lower()]


class CustomSearchModelD(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        values=lambda string: {string.lower()},
    )

    barindex = sheraf.Index("bar", key="bar")

    @fooindex.search
    def search_foo(self, value):
        return [value.lower()[::-1], value.lower()]


class CustomSearchModelE(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute()
    bar = sheraf.SimpleAttribute()

    fooindex = sheraf.Index(
        foo,
        key="foo",
        unique=True,
        values=lambda string: {string.lower()},
    )

    barindex = sheraf.Index(bar, key="bar")

    @fooindex.search
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
    ],
)
def test_custom_query_method(sheraf_database, Model):
    with sheraf.connection(commit=True):
        m = Model.create(foo="FOO", bar="BAR")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["foo"]
        assert {"foo"} == set(index_table)
        assert m.mapping == index_table["foo"]

        assert [m] == list(Model.search(foo="oof"))
        assert [m] == list(Model.search(foo="foo"))
        assert [m] == list(Model.search(foo="OOF"))
        assert [m] == list(Model.search(foo="FOO"))

        assert [m] == list(Model.search(foo="oof", bar="BAR"))
        assert [m] == list(Model.search(foo="OOF", bar="BAR"))

        assert [] == list(Model.search(foo="oof", bar="bar"))
        assert [] == list(Model.search(foo="OOF", bar="bar"))

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(foo="FOO")


def test_default_search_method(sheraf_database):
    class ModelA(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index()

    assert ModelA.indexes["foo"].details._search_func == ModelA.attributes["foo"].search

    class ModelB(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        fooindex = sheraf.Index("foo")

    assert ModelB.indexes["fooindex"].details._search_func is None


# ----------------------------------------------------------------------------
# Empty Index
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("unique", (True, False))
def test_noneok_index(sheraf_connection, unique):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(noneok=True, unique=unique)
        bar = sheraf.SimpleAttribute().index(noneok=False, unique=unique)

    m = ModelSimple.create(foo=None, bar=None)
    assert m in ModelSimple.search(foo=None)
    assert m not in ModelSimple.search(bar=None)

    n = ModelSimple.create(foo="", bar="")
    assert n in ModelSimple.search(foo="")
    assert n in ModelSimple.search(bar="")

    class ModelInteger(tests.IntAutoModel):
        foo = sheraf.IntegerAttribute().index(noneok=True, unique=unique)
        bar = sheraf.IntegerAttribute().index(noneok=False, unique=unique)

    o = ModelInteger.create(foo=0, bar=0)
    assert o in ModelInteger.search(foo=0)
    assert o in ModelInteger.search(bar=0)


@pytest.mark.parametrize("unique", (True, False))
def test_noneok_index_with_none_as_default(sheraf_connection, unique):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default=None).index(noneok=True, unique=unique)
        bar = sheraf.SimpleAttribute(default=None).index(noneok=False, unique=unique)

    m = ModelSimple.create()
    assert m in ModelSimple.search(foo=None)
    assert m not in ModelSimple.search(bar=None)

    if not unique:
        ModelSimple.create()

    else:
        ModelSimple.create(foo="anything")

        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            ModelSimple.create(bar="anything")


@pytest.mark.parametrize("unique", (True, False))
def test_nullok_index(sheraf_connection, unique):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(nullok=True, unique=unique)
        bar = sheraf.SimpleAttribute().index(nullok=False, unique=unique)

    m = ModelSimple.create(foo=None, bar=None)
    assert m not in ModelSimple.search(foo=None)
    assert m not in ModelSimple.search(bar=None)
    m.delete()

    n = ModelSimple.create(foo="", bar="")
    assert n in ModelSimple.search(foo="")
    assert n not in ModelSimple.search(bar="")
    n.delete()

    o = ModelSimple.create(foo=0, bar=0)
    assert o in ModelSimple.search(foo=0)
    assert o not in ModelSimple.search(bar=0)
    o.delete()

    p = ModelSimple.create(foo="anything", bar="anything")
    assert p in ModelSimple.search(foo="anything")
    assert p in ModelSimple.search(bar="anything")
    p.delete()


# ------------------------------------------------------------------------------------------------
# Cases that must fail
# ------------------------------------------------------------------------------------------------


def test_unique_indexation_and_filter_on_wrong_attribute(sheraf_database):
    class Model(tests.UUIDAutoModel):
        an_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        m = Model.create(an_attribute="foo")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["an_attribute"]
        assert {"foo"} == set(index_table)
        assert m.mapping == index_table["foo"]

        with pytest.raises(sheraf.exceptions.InvalidFilterException):
            list(Model.filter(foobar="foo"))


# ------------------------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------------------------


def test_reset_index_table(sheraf_database):
    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(foo="bar")
        Model.create(foo="baz")

    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar")
            assert warns[0].category is sheraf.exceptions.IndexationWarning

    with sheraf.connection(commit=True):
        Model.index_table_rebuild(["foo"])

    with sheraf.connection(commit=True):
        assert 3 == Model.count()

        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar")
            assert not warns


def test_index_table_rebuild(sheraf_database):
    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(foo="bar", bar="bar")
        Model.create(foo="baz", bar="bor")

    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index()
        bar = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar", bar="bur")
            assert warns[0].category is sheraf.exceptions.IndexationWarning
            assert warns[1].category is sheraf.exceptions.IndexationWarning

    with sheraf.connection(commit=True):
        Model.index_table_rebuild()

    with sheraf.connection(commit=True):
        assert 3 == Model.count()

        with warnings.catch_warnings(record=True) as warns:
            Model.create(foo="foobar", bar="boo")
            assert not warns

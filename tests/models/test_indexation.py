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
    class UniqueModel(tests.IntAutoModel):
        my_attribute = instance

    with sheraf.connection(commit=True):
        mfoo = UniqueModel.create(my_attribute=22)

    with sheraf.connection() as conn:
        index_table = conn.root()["uniquemodel"]["my_attribute"]
        assert {22} == set(index_table)
        assert mfoo.mapping == index_table[22]

        assert isinstance(index_table, mapping)


# ----------------------------------------------------------------------------
# Unique Index
# ----------------------------------------------------------------------------


def test_unique_index_creation(sheraf_database):
    class UniqueModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        mfoo = UniqueModel.create(my_attribute="foo")
        mbar = UniqueModel.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()["uniquemodel"]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo.mapping == index_table["foo"]
        assert mbar.mapping == index_table["bar"]

        assert mbar == UniqueModel.read(my_attribute="bar")
        assert [mbar] == list(UniqueModel.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(UniqueModel.read_these(my_attribute=["bar", "foo"]))

        # UniqueModel._read_unique_index = mock.MagicMock(
        #    side_effect=UniqueModel._read_unique_index
        # )
        assert [mbar] == UniqueModel.filter(my_attribute="bar")
        # UniqueModel._read_unique_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


def test_unique_index_creation_and_edition(sheraf_database):
    class UniqueModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        mfoo = UniqueModel.create(my_attribute="FOO")
        mbar = UniqueModel.create(my_attribute="BAR")

    with sheraf.connection(commit=True):
        UniqueModel.read(mfoo.id).my_attribute = "foo"
        UniqueModel.read(mbar.id).my_attribute = "bar"

    with sheraf.connection() as conn:
        index_table = conn.root()["uniquemodel"]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo.mapping == index_table["foo"]
        assert mbar.mapping == index_table["bar"]

        assert mbar == UniqueModel.read(my_attribute="bar")
        assert [mbar] == list(UniqueModel.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(UniqueModel.read_these(my_attribute=["bar", "foo"]))

        # UniqueModel._read_unique_index = mock.MagicMock(
        #    side_effect=UniqueModel._read_unique_index
        # )
        assert [mbar] == UniqueModel.filter(my_attribute="bar")
        # UniqueModel._read_unique_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


def test_unique_index_creation_and_deletion(sheraf_database):
    class UniqueModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        mfoo = UniqueModel.create(my_attribute="foo")
        mbar = UniqueModel.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()["uniquemodel"]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == UniqueModel.filter(my_attribute="foo")
        assert [mbar] == UniqueModel.filter(my_attribute="bar")


def test_unique_index_double_value(sheraf_database):
    class UniqueModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        UniqueModel.create(my_attribute="foo")

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            UniqueModel.create(my_attribute="foo")


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


def test_unique_index_alternate_definition(sheraf_database):
    class Model(tests.IntAutoModel):
        fooindex = sheraf.Index("foo", key="foo", unique=True)
        foo = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = Model.create(foo="foo")
        assert [m] == Model.search(foo="foo")

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(foo="foo")


# ---------------------------------------------------------------------------------
# Multiple Indexes
# ---------------------------------------------------------------------------------


def test_multiple_index_creation(sheraf_database):
    class MultipleModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        mfoo = MultipleModel.create(my_attribute="foo")
        mbar1 = MultipleModel.create(my_attribute="bar")
        mbar2 = MultipleModel.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()["multiplemodel"]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert [mfoo.mapping] == list(index_table["foo"])
        assert [mbar1.mapping, mbar2.mapping] == list(index_table["bar"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MultipleModel.read(my_attribute="bar")
        assert [mbar1, mbar2] == list(MultipleModel.read_these(my_attribute=["bar"]))

        # MultipleModel._read_multiple_index = mock.MagicMock(
        #    side_effect=MultipleModel._read_multiple_index
        # )
        assert [mbar1, mbar2] == MultipleModel.filter(my_attribute="bar")
        # MultipleModel._read_multiple_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


def test_multiple_index_creation_and_deletion(sheraf_database):
    class MultipleModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        mfoo = MultipleModel.create(my_attribute="foo")
        mbar1 = MultipleModel.create(my_attribute="bar")
        mbar2 = MultipleModel.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()
        mbar2.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()["multiplemodel"]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == MultipleModel.filter(my_attribute="foo")
        assert [mbar1] == MultipleModel.filter(my_attribute="bar")


def test_multiple_index_several_filters(sheraf_database):
    class MultipleModel(tests.IntAutoModel):
        my_attribute_1 = sheraf.SimpleAttribute().index()
        my_attribute_2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        MultipleModel.create(my_attribute_1="foo", my_attribute_2="foo")
        MultipleModel.create(my_attribute_1="bar", my_attribute_2="bar")
        m = MultipleModel.create(my_attribute_1="foo", my_attribute_2="bar")

    with sheraf.connection():
        assert [m] == MultipleModel.filter(my_attribute_1="foo").filter(
            my_attribute_2="bar"
        )


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
        index_table = conn.root()["indexkeymodel"]["another_index_key"]
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


def test_multiple_keys_index_create(sheraf_database):
    class MultipleKeysIndexModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(key="key_1").index(key="key_2")

    with sheraf.connection(commit=True):
        mfoo = MultipleKeysIndexModel.create(my_attribute="foo")

    with sheraf.connection() as conn:
        index_table_key_1 = conn.root()["multiplekeysindexmodel"]["key_1"]
        index_table_key_2 = conn.root()["multiplekeysindexmodel"]["key_2"]
        assert {"foo"} == set(index_table_key_1)
        assert [mfoo.mapping] == list(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert [mfoo.mapping] == list(index_table_key_2["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MultipleKeysIndexModel.read(key_1="foo")
        assert [mfoo] == list(MultipleKeysIndexModel.read_these(key_1=["foo"]))

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MultipleKeysIndexModel.read(key_2="foo")
        assert [mfoo] == list(MultipleKeysIndexModel.read_these(key_2=["foo"]))

        # MultipleKeysIndexModel._read_multiple_index = mock.MagicMock(
        #    side_effect=MultipleKeysIndexModel._read_multiple_index
        # )
        assert [mfoo] == MultipleKeysIndexModel.filter(key_1="foo")
        # MultipleKeysIndexModel._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )

        assert [mfoo] == MultipleKeysIndexModel.filter(key_2="foo")
        # MultipleKeysIndexModel._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )


def test_multiple_keys_index_update(sheraf_database):
    class MultipleKeysIndexModel(tests.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(key="key_1").index(key="key_2")

    with sheraf.connection(commit=True):
        mfoo = MultipleKeysIndexModel.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo = MultipleKeysIndexModel.read(mfoo.id)
        mfoo.my_attribute = "foo"

    with sheraf.connection() as conn:
        index_table_key_1 = conn.root()["multiplekeysindexmodel"]["key_1"]
        index_table_key_2 = conn.root()["multiplekeysindexmodel"]["key_2"]
        assert {"foo"} == set(index_table_key_1)
        assert [mfoo.mapping] == list(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert [mfoo.mapping] == list(index_table_key_2["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MultipleKeysIndexModel.read(key_1="foo")
        assert [mfoo] == list(MultipleKeysIndexModel.read_these(key_1=["foo"]))

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MultipleKeysIndexModel.read(key_2="foo")
        assert [mfoo] == list(MultipleKeysIndexModel.read_these(key_2=["foo"]))

        # MultipleKeysIndexModel._read_multiple_index = mock.MagicMock(
        #    side_effect=MultipleKeysIndexModel._read_multiple_index
        # )
        assert [mfoo] == MultipleKeysIndexModel.filter(key_1="foo")
        # MultipleKeysIndexModel._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )

        assert [mfoo] == MultipleKeysIndexModel.filter(key_2="foo")
        # MultipleKeysIndexModel._read_multiple_index.assert_has_calls(
        #    [mock.call("foo", "key_1")]
        # )


def test_multiple_index_alternate_definition(sheraf_database):
    class Model(tests.IntAutoModel):
        fooindex = sheraf.Index("foo", key="foo")
        foo = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True) as conn:
        m = Model.create(foo="bar")
        n = Model.create(foo="bar")

        assert m.mapping in conn.root()["model"]["foo"]["bar"]
        assert n.mapping in conn.root()["model"]["foo"]["bar"]
        assert [m, n] == Model.search(foo="bar")


# ---------------------------------------------------------------------------------
# Custom methods
# ---------------------------------------------------------------------------------


class CustomIndexationModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True, values=lambda string: {string.lower()}
    )
    barindex = sheraf.Index("bar", key="bar")
    bar = sheraf.SimpleAttribute()


class CustomIndexationModelB(tests.IntAutoModel):
    fooindex = sheraf.Index(
        "foo", key="foo", unique=True, values=lambda string: {string.lower()}
    )
    foo = sheraf.SimpleAttribute()
    barindex = sheraf.Index("bar", key="bar")
    bar = sheraf.SimpleAttribute()


@pytest.mark.parametrize("Model", [CustomIndexationModelA, CustomIndexationModelB])
def test_custom_indexation_method(sheraf_database, Model):
    with sheraf.connection(commit=True):
        m = Model.create(foo="FOO", bar="BAR")

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


class CustomSearchModelA(tests.IntAutoModel):
    foo = sheraf.SimpleAttribute().index(
        unique=True,
        values=lambda string: {string.lower()},
        search=lambda string: [string.lower()[::-1], string.lower()],
    )
    bar = sheraf.SimpleAttribute().index()


class CustomSearchModelB(tests.IntAutoModel):
    fooindex = sheraf.Index(
        "foo",
        key="foo",
        unique=True,
        values=lambda string: {string.lower()},
        search=lambda string: [string.lower()[::-1], string.lower()],
    )

    foo = sheraf.SimpleAttribute()
    barindex = sheraf.Index("bar", key="bar")
    bar = sheraf.SimpleAttribute()


@pytest.mark.parametrize("Model", [CustomSearchModelA, CustomSearchModelB])
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
        index_table = conn.root()["model"]["an_attribute"]
        assert {"foo"} == set(index_table)
        assert m.mapping == index_table["foo"]

        with pytest.raises(sheraf.exceptions.InvalidFilterException):
            list(Model.filter(foobar="foo"))


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

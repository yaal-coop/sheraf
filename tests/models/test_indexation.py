# coding: utf-8
import BTrees.OOBTree
import mock
import pytest

import sheraf


# ----------------------------------------------------------------------------
# Types
# ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "instance, mapping",
    [
        (sheraf.IntegerAttribute().index(unique=True), BTrees.IOBTree.IOBTree),
        # ( sheraf.IntegerAttribute().index(unique=True, key="my_int"), BTrees.IOBTree.IOBTree)
        (sheraf.SimpleAttribute(default=int).index(unique=True), BTrees.OOBTree.OOBTree),
    ],
)
def test_integer_unique_index_creation(sheraf_database, instance, mapping):
    class MyUniqueModel(sheraf.IntAutoModel):
        my_attribute = instance

    with sheraf.connection(commit=True):
        mfoo = MyUniqueModel.create(my_attribute=22)

    with sheraf.connection() as conn:
        index_table = conn.root()["myuniquemodel"]["my_attribute"]
        assert {22} == set(index_table)
        assert mfoo._persistent == index_table[22]

        assert isinstance(index_table, mapping)


# ----------------------------------------------------------------------------
# Unique Index
# ----------------------------------------------------------------------------


def test_unique_index_creation(sheraf_database):
    class MyUniqueModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        mfoo = MyUniqueModel.create(my_attribute="foo")
        mbar = MyUniqueModel.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()["myuniquemodel"]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo._persistent == index_table["foo"]
        assert mbar._persistent == index_table["bar"]

        assert mbar == MyUniqueModel.read(my_attribute="bar")
        assert [mbar] == list(MyUniqueModel.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(
            MyUniqueModel.read_these(my_attribute=["bar", "foo"])
        )

        MyUniqueModel._read_unique_index = mock.MagicMock(
            side_effect=MyUniqueModel._read_unique_index
        )
        assert [mbar] == MyUniqueModel.filter(my_attribute="bar")
        MyUniqueModel._read_unique_index.assert_has_calls(
            [mock.call("bar", "my_attribute")]
        )


def test_unique_index_creation_and_edition(sheraf_database):
    class MyUniqueModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        mfoo = MyUniqueModel.create(my_attribute="FOO")
        mbar = MyUniqueModel.create(my_attribute="BAR")

    with sheraf.connection(commit=True):
        MyUniqueModel.read(mfoo.id).my_attribute = "foo"
        MyUniqueModel.read(mbar.id).my_attribute = "bar"

    with sheraf.connection() as conn:
        index_table = conn.root()["myuniquemodel"]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo._persistent == index_table["foo"]
        assert mbar._persistent == index_table["bar"]

        assert mbar == MyUniqueModel.read(my_attribute="bar")
        assert [mbar] == list(MyUniqueModel.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(
            MyUniqueModel.read_these(my_attribute=["bar", "foo"])
        )

        MyUniqueModel._read_unique_index = mock.MagicMock(
            side_effect=MyUniqueModel._read_unique_index
        )
        assert [mbar] == MyUniqueModel.filter(my_attribute="bar")
        MyUniqueModel._read_unique_index.assert_has_calls(
            [mock.call("bar", "my_attribute")]
        )


def test_unique_index_creation_and_deletion(sheraf_database):
    class MyUniqueModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        mfoo = MyUniqueModel.create(my_attribute="foo")
        mbar = MyUniqueModel.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()["myuniquemodel"]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == MyUniqueModel.filter(my_attribute="foo")
        assert [mbar] == MyUniqueModel.filter(my_attribute="bar")


def test_unique_index_double_value(sheraf_database):
    class MyUniqueModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        MyUniqueModel.create(my_attribute="foo")

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            MyUniqueModel.create(my_attribute="foo")


def test_unique_indexation_on_model_attribute(sheraf_database):
    class DummyModel(sheraf.Model):
        table = "dummymodel_table"
        v = sheraf.SimpleAttribute(lazy_creation=False, default=str)

    class MyModel(sheraf.Model):
        table = "mymodel_table"
        dummy_attribute = sheraf.ModelAttribute(DummyModel, lazy_creation=False).index(
            unique=True, values=lambda x: {x.v}
        )

    with sheraf.connection(commit=True):
        foo = DummyModel.create(v="fou")
        m = MyModel.create(dummy_attribute=foo)

    with sheraf.connection() as conn:
        index_table = conn.root()["mymodel_table"]["dummy_attribute"]
        assert {"fou"} == set(index_table)


# ---------------------------------------------------------------------------------
# Multiple Indexes
# ---------------------------------------------------------------------------------


def test_multiple_index_creation(sheraf_database):
    class MyMultipleModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        mfoo = MyMultipleModel.create(my_attribute="foo")
        mbar1 = MyMultipleModel.create(my_attribute="bar")
        mbar2 = MyMultipleModel.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()["mymultiplemodel"]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert [mfoo._persistent] == list(index_table["foo"])
        assert [mbar1._persistent, mbar2._persistent] == list(index_table["bar"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MyMultipleModel.read(my_attribute="bar")
        assert [mbar1, mbar2] == list(MyMultipleModel.read_these(my_attribute=["bar"]))

        MyMultipleModel._read_multiple_index = mock.MagicMock(
            side_effect=MyMultipleModel._read_multiple_index
        )
        assert [mbar1, mbar2] == MyMultipleModel.filter(my_attribute="bar")
        MyMultipleModel._read_multiple_index.assert_has_calls(
            [mock.call("bar", "my_attribute")]
        )


def test_multiple_index_creation_and_deletion(sheraf_database):
    class MyMultipleModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        mfoo = MyMultipleModel.create(my_attribute="foo")
        mbar1 = MyMultipleModel.create(my_attribute="bar")
        mbar2 = MyMultipleModel.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()
        mbar2.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()["mymultiplemodel"]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == MyMultipleModel.filter(my_attribute="foo")
        assert [mbar1] == MyMultipleModel.filter(my_attribute="bar")


def test_multiple_index_several_filters(sheraf_database):
    class MyMultipleModel(sheraf.IntAutoModel):
        my_attribute_1 = sheraf.SimpleAttribute().index()
        my_attribute_2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        MyMultipleModel.create(my_attribute_1="foo", my_attribute_2="foo")
        MyMultipleModel.create(my_attribute_1="bar", my_attribute_2="bar")
        m = MyMultipleModel.create(my_attribute_1="foo", my_attribute_2="bar")

    with sheraf.connection():
        assert [m] == MyMultipleModel.filter(my_attribute_1="foo").filter(
            my_attribute_2="bar"
        )


def test_multiple_index_ordering(sheraf_database):
    class MyMultipleAllModel(sheraf.IntAutoModel):
        my_attribute_1 = sheraf.SimpleAttribute().index()
        my_attribute_2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        maa = MyMultipleAllModel.create(my_attribute_1="a", my_attribute_2="a")
        mab = MyMultipleAllModel.create(my_attribute_1="a", my_attribute_2="b")
        mba = MyMultipleAllModel.create(my_attribute_1="b", my_attribute_2="a")
        mbb = MyMultipleAllModel.create(my_attribute_1="b", my_attribute_2="b")

    with sheraf.connection():
        assert [mab, maa, mbb, mba] == MyMultipleAllModel.order(
            my_attribute_1=sheraf.ASC
        ).order(my_attribute_2=sheraf.DESC)


def test_index_key(sheraf_database):
    class MyIndexKeyModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(key="another_index_key")

    with sheraf.connection(commit=True):
        mfoo = MyIndexKeyModel.create(my_attribute="foo")

    with sheraf.connection() as conn:
        index_table = conn.root()["myindexkeymodel"]["another_index_key"]
        assert {"foo"} == set(index_table)
        assert [mfoo._persistent] == list(index_table["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MyIndexKeyModel.read(another_index_key="foo")
        assert [mfoo] == list(MyIndexKeyModel.read_these(another_index_key=["foo"]))

        MyIndexKeyModel._read_multiple_index = mock.MagicMock(
            side_effect=MyIndexKeyModel._read_multiple_index
        )
        assert [mfoo] == MyIndexKeyModel.filter(another_index_key="foo")
        MyIndexKeyModel._read_multiple_index.assert_has_calls(
            [mock.call("foo", "another_index_key")]
        )


def test_multiple_keys_index(sheraf_database):
    class MyMultipleKeysIndexModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(key="key_1").index(key="key_2")

    with sheraf.connection(commit=True):
        mfoo = MyMultipleKeysIndexModel.create(my_attribute="foo")

    with sheraf.connection() as conn:
        index_table_key_1 = conn.root()["mymultiplekeysindexmodel"]["key_1"]
        index_table_key_2 = conn.root()["mymultiplekeysindexmodel"]["key_2"]
        assert {"foo"} == set(index_table_key_1)
        assert [mfoo._persistent] == list(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert [mfoo._persistent] == list(index_table_key_2["foo"])

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MyMultipleKeysIndexModel.read(key_1="foo")
        assert [mfoo] == list(MyMultipleKeysIndexModel.read_these(key_1=["foo"]))

        with pytest.raises(sheraf.exceptions.MultipleIndexException):
            MyMultipleKeysIndexModel.read(key_2="foo")
        assert [mfoo] == list(MyMultipleKeysIndexModel.read_these(key_2=["foo"]))

        MyMultipleKeysIndexModel._read_multiple_index = mock.MagicMock(
            side_effect=MyMultipleKeysIndexModel._read_multiple_index
        )
        assert [mfoo] == MyMultipleKeysIndexModel.filter(key_1="foo")
        MyMultipleKeysIndexModel._read_multiple_index.assert_has_calls(
            [mock.call("foo", "key_1")]
        )

        assert [mfoo] == MyMultipleKeysIndexModel.filter(key_2="foo")
        MyMultipleKeysIndexModel._read_multiple_index.assert_has_calls(
            [mock.call("foo", "key_1")]
        )


def test_custom_indexation_method(sheraf_database):
    class MyCustomModel(sheraf.IntAutoModel):
        my_attribute = sheraf.SimpleAttribute().index(
            unique=True, values=lambda string: {string.lower()}
        )

    with sheraf.connection(commit=True):
        m = MyCustomModel.create(my_attribute="FOO")

    with sheraf.connection() as conn:
        index_table = conn.root()["mycustommodel"]["my_attribute"]
        assert {"foo"} == set(index_table)
        assert m._persistent == index_table["foo"]

        assert [m] == list(MyCustomModel.filter(my_attribute="foo"))
        assert [] == list(MyCustomModel.filter(my_attribute="FOO"))

        assert [m] == list(MyCustomModel.filter_raw(my_attribute="foo"))
        assert [m] == list(MyCustomModel.filter_raw(my_attribute="FOO"))

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            MyCustomModel.create(my_attribute="FOO")


# ------------------------------------------------------------------------------------------------
# Cases that must fail
# ------------------------------------------------------------------------------------------------


def test_unique_indexation_and_filter_on_wrong_attribute(sheraf_database):
    class MyModel(sheraf.AutoModel):
        an_attribute = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        m = MyModel.create(an_attribute="foo")

    with sheraf.connection() as conn:
        index_table = conn.root()["mymodel"]["an_attribute"]
        assert {"foo"} == set(index_table)
        assert m._persistent == index_table["foo"]

        with pytest.raises(sheraf.exceptions.InvalidFilterException):
            list(MyModel.filter(foobar="foo"))


# TODO: les indexes auront besoin d'être initialisés si jamais quelqu'un veut passer d'une base non indexée à une base indexée.
#  Tester qu'un attribut passé « indexé » mais non initialisé adopte toujours un comportement valide.

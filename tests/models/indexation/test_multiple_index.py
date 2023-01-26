import pytest
import sheraf
import tests


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
        assert {mfoo.raw_identifier: mfoo.mapping} == dict(index_table["foo"])
        assert {
            mbar1.raw_identifier: mbar1.mapping,
            mbar2.raw_identifier: mbar2.mapping,
        } == dict(index_table["bar"])

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
        assert [{mfoo.raw_identifier: mfoo.mapping}] == [dict(index_table["foo"])]

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
        assert {mfoo.raw_identifier: mfoo.mapping} == dict(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert {mfoo.raw_identifier: mfoo.mapping} == dict(index_table_key_2["foo"])

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
        assert {mfoo.raw_identifier: mfoo.mapping} == dict(index_table_key_1["foo"])
        assert {"foo"} == set(index_table_key_2)
        assert {mfoo.raw_identifier: mfoo.mapping} == dict(index_table_key_2["foo"])

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

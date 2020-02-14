import warnings
from unittest import mock

import sheraf

warnings.simplefilter("always")


def test_edit_no_index(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create()

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        m.my_simple_attribute = "bar"

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]


def test_edit_single_instance_after_set_index(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(
            my_simple_attribute="attribute_value_that_should_not_be_in_index_table"
        )

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        with warnings.catch_warnings(record=True) as warning_messages:
            m.my_simple_attribute = "bar_indexed"
            assert not warning_messages

    with sheraf.connection() as conn:
        index_table = conn.root()["mymodel"]["my_simple_attribute"]
        assert len(index_table) == 1
        assert {"bar_indexed"} == set(index_table)


def test_edit_a_not_single_instance_after_set_index(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo_not_indexed")
        # Having more than one instance must prevent indexation
        MyModel.create(my_simple_attribute="foo_not_indexed2")

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        with warnings.catch_warnings(record=True) as warning_messages:
            m.my_simple_attribute = "bar_still_not_indexed"
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]


def test_edit_a_not_single_instance_after_set_index_in_one_of_two_attributes(
    sheraf_database,
):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()
        my_other_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(
            my_simple_attribute="foo_not_indexed", my_other_attribute="other1"
        )
        # Having more than one instance must prevent indexation
        MyModel.create(
            my_simple_attribute="foo_not_indexed2", my_other_attribute="other2"
        )

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        with warnings.catch_warnings(record=True) as warning_messages:
            m.my_other_attribute = "new_other1"
            m.my_simple_attribute = "bar_still_not_indexed"
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]
        assert "my_other_attribute" not in conn.root()["mymodel"]


def test_edit_a_not_single_instance_after_set_index_with_key(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo_not_indexed")
        MyModel.create(my_simple_attribute="foo_not_indexed2")

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index(key="new_key")
        my_other_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        with warnings.catch_warnings(record=True) as warning_messages:
            m.my_simple_attribute = "bar_still_not_indexed"
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]


# ---------------------------------------------------------------------------------
# Multiple indexes
# ---------------------------------------------------------------------------------


def test_edit_a_not_single_instance_when_two_indexes_with_key(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = (
            sheraf.SimpleAttribute().index(key="key1").index(key="key2")
        )

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo_indexed")
        MyModel.create(my_simple_attribute="foo_indexed2")

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        with mock.patch("logging.Logger.warning") as warning:
            m.my_simple_attribute = "foo_indexed_changed"
            assert not warning.called

    with sheraf.connection() as conn:
        assert {"foo_indexed_changed", "foo_indexed2"} == set(
            conn.root()["mymodel"]["key1"]
        )


def test_edit_a_not_single_instance_when_two_indexes_with_key_afterwards(
    sheraf_database,
):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo_not_indexed")
        MyModel.create(my_simple_attribute="foo_not_indexed2")

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = (
            sheraf.SimpleAttribute()
            .index(key="key1")
            .index(key="key2", values=lambda x: x)
        )

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        with warnings.catch_warnings(record=True) as warning_messages:
            m.my_simple_attribute = "bar_still_not_indexed"
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "key1" not in conn.root()["mymodel"]
        assert "key2" not in conn.root()["mymodel"]


# ----------------------------------------------------------------------------
# ATTRIBUTES WITH A KEY
# ----------------------------------------------------------------------------


def test_edit_one_with_attribute_key_index(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(key="attr_key").index()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo1")

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        m.my_simple_attribute = "foo2"

    with sheraf.connection() as conn:
        assert {"foo2"} == set(conn.root()["mymodel"]["attr_key"])


def test_edit_one_with_attribute_key_index_with_key(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(key="attr_key").index(
            key="index_key"
        )

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo1")

    with sheraf.connection(commit=True):
        m = MyModel.read(m.id)
        m.my_simple_attribute = "foo2"

    with sheraf.connection() as conn:
        assert {"foo2"} == set(conn.root()["mymodel"]["index_key"])


# TODO :
#  - not tested if attribute is multi-indexed AND with multiple keys (.index(key="k1").index(key="k2")
#  - ... key pour attribut et cle differente pour l'index?

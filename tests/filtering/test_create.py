import warnings

import sheraf
import tests

warnings.simplefilter("always")


def test_create_indexed(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Model.create(my_simple_attribute="foo")

    with sheraf.connection() as conn:
        assert "foo" in conn.root()["model"]["my_simple_attribute"]
        assert len(conn.root()["model"]["my_simple_attribute"]) == 1


def test_create_not_indexed(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(my_simple_attribute="foo")

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["model"]


def test_create_indexed_one_recreated_instance(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = Model.create(my_simple_attribute="foo_indexed")

    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(default="").index()

    with sheraf.connection(commit=True) as conn:
        Model.read(m.id).delete()
        assert Model.table not in conn.root()

    with sheraf.connection(commit=True):
        Model.create(my_simple_attribute="foo_indexed")
        Model.create(my_simple_attribute="foo_indexed2")

    with sheraf.connection() as conn:
        index_table = conn.root()["model"]["my_simple_attribute"]
        assert "foo_indexed" in index_table
        assert "foo_indexed2" in index_table


# ---------------------------------------------------------------
# WITH AFTERWARDS INDEX SETTING
# ---------------------------------------------------------------


def test_create_already_one_instance(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(my_simple_attribute="foo_not_indexed")

    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warning_messages:
            Model.create(my_simple_attribute="foo_still_not_indexed")
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["model"]


def test_create_already_one_instance_with_index_key(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Model.create(my_simple_attribute="foo_not_indexed")

    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index(key="key1")

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warning_messages:
            Model.create(my_simple_attribute="foo_still_not_indexed")
            assert "key1 will not be indexed." in str(warning_messages[0].message)

    with sheraf.connection() as conn:
        assert "key1" not in conn.root()["model"]


def test_create_one_new_indexed(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()
        my_simple_attribute2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Model.create(
            my_simple_attribute="foo_not_indexed", my_simple_attribute2="foo_indexed"
        )

    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()
        my_simple_attribute2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warning_messages:
            Model.create(my_simple_attribute="foo_still_not_indexed")
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["model"]
        assert "foo_indexed" in conn.root()["model"]["my_simple_attribute2"]


# ----------------------------------------------------------------------------
# ATTRIBUTES WITH A KEY
# ----------------------------------------------------------------------------


def test_create_one_with_attribute_key_index(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(key="attr_key").index()

    with sheraf.connection(commit=True):
        Model.create(my_simple_attribute="foo1")

    with sheraf.connection() as conn:
        assert {"foo1"} == set(conn.root()["model"]["attr_key"])


def test_create_one_with_attribute_key_index_with_key(sheraf_database):
    class Model(tests.UUIDAutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(key="attr_key").index(
            key="index_key"
        )

    with sheraf.connection(commit=True):
        m = Model.create(my_simple_attribute="foo1")

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        m.my_simple_attribute = "foo2"

    with sheraf.connection() as conn:
        assert {"foo2"} == set(conn.root()["model"]["index_key"])

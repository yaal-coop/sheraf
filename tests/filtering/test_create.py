import warnings

import sheraf

warnings.simplefilter("always")


def test_create_indexed(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        MyModel.create(my_simple_attribute="foo")

    with sheraf.connection() as conn:
        assert "foo" in conn.root()["mymodel"]["my_simple_attribute"]
        assert len(conn.root()["mymodel"]["my_simple_attribute"]) == 1


def test_create_not_indexed(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo")

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]


def test_create_indexed_one_recreated_instance(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo_indexed")

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(default="").index()

    with sheraf.connection(commit=True):
        MyModel.read(m.id).delete()

    with sheraf.connection(commit=True):
        MyModel.create(my_simple_attribute="foo_indexed")
        MyModel.create(my_simple_attribute="foo_indexed2")

    with sheraf.connection() as conn:
        index_table = conn.root()["mymodel"]["my_simple_attribute"]
        assert "foo_indexed" in index_table
        assert "foo_indexed2" in index_table


# ---------------------------------------------------------------
# WITH AFTERWARDS INDEX SETTING
# ---------------------------------------------------------------


def test_create_already_one_instance(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        MyModel.create(my_simple_attribute="foo_not_indexed")

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warning_messages:
            MyModel.create(my_simple_attribute="foo_still_not_indexed")
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]


def test_create_already_one_instance_with_index_key(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        MyModel.create(my_simple_attribute="foo_not_indexed")

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index(key="key1")

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warning_messages:
            MyModel.create(my_simple_attribute="foo_still_not_indexed")
            assert "key1 will not be indexed." in str(warning_messages[0].message)

    with sheraf.connection() as conn:
        assert "key1" not in conn.root()["mymodel"]


def test_create_one_new_indexed(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute()
        my_simple_attribute2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        MyModel.create(
            my_simple_attribute="foo_not_indexed", my_simple_attribute2="foo_indexed"
        )

    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute().index()
        my_simple_attribute2 = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        with warnings.catch_warnings(record=True) as warning_messages:
            MyModel.create(my_simple_attribute="foo_still_not_indexed")
            assert "my_simple_attribute will not be indexed." in str(
                warning_messages[0].message
            )

    with sheraf.connection() as conn:
        assert "my_simple_attribute" not in conn.root()["mymodel"]
        assert "foo_indexed" in conn.root()["mymodel"]["my_simple_attribute2"]


# ----------------------------------------------------------------------------
# ATTRIBUTES WITH A KEY
# ----------------------------------------------------------------------------


def test_create_one_with_attribute_key_index(sheraf_database):
    class MyModel(sheraf.AutoModel):
        my_simple_attribute = sheraf.SimpleAttribute(key="attr_key").index()

    with sheraf.connection(commit=True):
        m = MyModel.create(my_simple_attribute="foo1")

    with sheraf.connection() as conn:
        assert {"foo1"} == set(conn.root()["mymodel"]["attr_key"])


def test_create_one_with_attribute_key_index_with_key(sheraf_database):
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

import warnings

import sheraf
import tests


def test_initialization_on_creation(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute().index()

    with warnings.catch_warnings(record=True) as warns:
        Model.create(foo="nope")
        assert "bar" in sheraf_connection.root()[Model.table]
        assert len(warns) == 0


def test_initialization_on_creation_when_attribute_is_accessed_in_a_callback(
    sheraf_connection,
):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute().index()

        @foo.on_change
        def change_foo(self, new=None, old=None):
            self.bar

    with warnings.catch_warnings(record=True) as warns:
        Model.create(foo="nope")
        assert "bar" in sheraf_connection.root()[Model.table]
        assert len(warns) == 0


def test_initialization_order_on_creation(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute().index()

        @foo.on_creation
        @bar.on_creation
        def change(self, new=None, old=None):
            assert self.foo is None
            assert self.bar is None
            assert self.index_keys("bar") == set()

            yield

            assert self.foo == "after_foo"
            assert self.bar == "after_bar"
            assert self.index_keys("bar") == {"after_bar"}

    Model.create(foo="after_foo", bar="after_bar")


def test_initialization_order_on_update(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default="before_foo")
        bar = sheraf.SimpleAttribute(default="before_bar").index()

        @foo.on_edition
        @bar.on_edition
        def change(self, new=None, old=None):
            assert self.foo == "before_foo"
            assert self.bar == "before_bar"
            assert self.index_keys("bar") == {"before_bar"}

            yield

            assert self.foo == "after_foo"
            assert self.bar == "after_bar"
            assert self.index_keys("bar") == {"after_bar"}

    m = Model.create()
    m.update(foo="after_foo", bar="after_bar")


def test_initialization_order_on_deletion(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default="before_foo")
        bar = sheraf.SimpleAttribute(default="before_bar").index()

        @foo.on_deletion
        @bar.on_deletion
        def change(self, new=None, old=None):
            assert self.foo == "before_foo"
            assert self.bar == "before_bar"
            assert self.index_keys("bar") == {"before_bar"}

            yield

            assert not self.attributes["foo"].is_created(self)
            assert not self.attributes["bar"].is_created(self)
            assert self.index_keys("bar") == set()

    m = Model.create(foo="before_foo", bar="before_bar")
    m.delete()

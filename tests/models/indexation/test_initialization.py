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

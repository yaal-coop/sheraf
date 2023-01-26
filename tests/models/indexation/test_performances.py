import sheraf
import tests


def test_index_not_recomputed_when_attribute_value_has_not_changed(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index()
        index_recomputed = False

        @foo.index_keys_func
        def index_foo(self, value):
            self.index_recomputed = True

    m = Model.create(foo="foo")
    assert m.index_recomputed

    m.index_recomputed = False
    m.foo = "foo"
    assert not m.index_recomputed

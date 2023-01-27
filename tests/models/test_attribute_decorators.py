import sheraf
import tests


def test_on_creation(sheraf_connection):
    class Model(tests.IntAutoModel):
        created = False
        foo = sheraf.SimpleAttribute()

    class OtherModel(tests.IntAutoModel):
        created = False
        foo = sheraf.SimpleAttribute()

    @Model.on_creation
    def foo_creation(model):
        model.created = True

    m = Model.create()
    assert m.created

    n = OtherModel.create()
    assert not n.created


def test_on_creation_parenthesis(sheraf_connection):
    class Model(tests.IntAutoModel):
        created = False
        foo = sheraf.SimpleAttribute()

    @Model.on_creation()
    def foo_creation(model):
        model.created = True

    m = Model.create()
    assert m.created


def test_on_creation_yield(sheraf_connection):
    class Model(tests.IntAutoModel):
        created = False
        foo = sheraf.SimpleAttribute()

    @Model.on_creation
    def foo_creation(model):
        assert "foo" not in model.mapping
        yield
        model.created = True
        assert model.mapping["foo"] == "anything"

    m = Model.create(foo="anything")
    assert m.created


def test_on_deletion(sheraf_connection):
    class Model(tests.IntAutoModel):
        deleted = False
        foo = sheraf.SimpleAttribute()

    @Model.on_deletion
    def foo_deletion(model):
        Model.deleted = True

    m = Model.create()
    assert not Model.deleted
    m.delete()
    assert Model.deleted


def test_on_deletion_parenthesis(sheraf_connection):
    class Model(tests.IntAutoModel):
        deleted = False
        foo = sheraf.SimpleAttribute()

    @Model.on_deletion()
    def foo_deletion(model):
        Model.deleted = True

    m = Model.create()
    assert not Model.deleted
    m.delete()
    assert Model.deleted


def test_initialization_order_on_creation(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default="before_foo")
        bar = sheraf.SimpleAttribute(default="before_bar")

        @foo.on_creation
        @bar.on_creation
        def change(self, new=None, old=None):
            assert self.foo == "before_foo"
            assert self.bar == "before_bar"
            yield
            assert self.foo == "after_foo"
            assert self.bar == "after_bar"

    Model.create(foo="after_foo", bar="after_bar")


def test_initialization_order_on_update(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default="before_foo")
        bar = sheraf.SimpleAttribute(default="before_bar")

        @foo.on_edition
        @bar.on_edition
        def change(self, new=None, old=None):
            assert self.foo == "before_foo"
            assert self.bar == "before_bar"
            yield
            assert self.foo == "after_foo"
            assert self.bar == "after_bar"

    m = Model.create()
    m.update(foo="after_foo", bar="after_bar")


def test_initialization_order_on_deletion(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default="before")
        bar = sheraf.SimpleAttribute(default="before")

        @foo.on_deletion
        @bar.on_deletion
        def change(self, new=None, old=None):
            assert self.foo == "before"
            assert self.bar == "before"
            yield
            assert not self.attributes["foo"].is_created(self)
            assert not self.attributes["bar"].is_created(self)

    m = Model.create()
    m.delete()

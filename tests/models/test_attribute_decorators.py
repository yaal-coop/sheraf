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

import sheraf
import tests


def test_on_creation(sheraf_connection):
    class Model(tests.IntAutoModel):
        created = False
        foo = sheraf.SimpleAttribute()

        @foo.on_creation
        def foo_creation(self, new):
            if new == "whatever":
                self.created = True

    m = Model.create()
    assert not m.created
    m.foo = "whatever"
    assert m.created


def test_on_edition(sheraf_connection):
    class Model(tests.IntAutoModel):
        edited = False
        foo = sheraf.SimpleAttribute()

        @foo.on_edition
        def foo_update(self, new, old):
            if new == "whatever":
                self.edited = True

    m = Model.create(foo="yolo")
    assert not m.edited
    m.foo = "whatever"
    assert m.edited


def test_on_edition_parenthesis(sheraf_connection):
    class Model(tests.IntAutoModel):
        edited = False
        foo = sheraf.SimpleAttribute()

        @foo.on_edition
        def foo_update(self, new, old):
            if new == "whatever":
                self.edited = True

    m = Model.create(foo="yolo")
    assert not m.edited
    m.foo = "whatever"
    assert m.edited


def test_on_edition_generator(sheraf_connection):
    class Model(tests.IntAutoModel):
        edited = False
        foo = sheraf.SimpleAttribute()

        @foo.on_edition
        def foo_update(self, new, old):
            yield
            if new == "whatever":
                self.edited = True

    m = Model.create(foo="yolo")
    assert not m.edited
    m.foo = "whatever"
    assert m.edited


def test_on_edition_empty_generator(sheraf_connection):
    class Model(tests.IntAutoModel):
        edited = False
        foo = sheraf.SimpleAttribute()

        @foo.on_edition
        def foo_update(self, new, old):
            if False:
                yield
            if new == "whatever":
                self.edited = True

    assert Model.attributes["foo"].cb_edition

    m = Model.create(foo="yolo")
    assert not m.edited
    m.foo = "whatever"
    assert m.edited


def test_on_deletion(sheraf_connection):
    class Model(tests.IntAutoModel):
        deleted = False
        foo = sheraf.SimpleAttribute()

        @foo.on_deletion
        def foo_deletion(self, old):
            self.deleted = True

    m = Model.create()
    assert not m.deleted
    del m.foo
    assert m.deleted


class Farm(tests.IntAutoModel):
    owner = sheraf.ReverseModelAttribute("Cowboy", "farm")
    size = sheraf.IntegerAttribute()

    @size.on_edition
    def update_size(self, new, old):
        attr = self.owner.attributes["farm"]
        old_values = self.owner.before_index_edition(attr)
        yield
        self.owner.after_index_edition(attr, old_values)


class Cowboy(tests.IntAutoModel):
    farm = sheraf.ModelAttribute("Farm").index(unique=True)

    farm_size = sheraf.Index(farm)

    @farm_size.search
    def search_farm_size(self, size):
        return size

    @farm_size.values
    def index_farm_size(self, farm):
        return farm.size


def test_back_indexation(sheraf_connection):
    farm = Farm.create(size=100)
    cowboy = Cowboy.create(farm=farm)

    assert cowboy in Cowboy.search(farm_size=100)

    farm.size = 90

    assert cowboy not in Cowboy.search(farm_size=100)
    assert cowboy in Cowboy.search(farm_size=90)

    farm.size = 80

    assert cowboy not in Cowboy.search(farm_size=100)
    assert cowboy not in Cowboy.search(farm_size=90)
    assert cowboy in Cowboy.search(farm_size=80)

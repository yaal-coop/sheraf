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


class FarmA(tests.IntAutoModel):
    owner = sheraf.ReverseModelAttribute("CowboyA", "farm")
    size = sheraf.IntegerAttribute()

    @size.on_edition
    def update_size(self, new, old):
        attr = self.owner.attributes["farm"]
        old_values = self.owner.before_index_edition(attr)
        yield
        self.owner.after_index_edition(attr, old_values)


class CowboyA(tests.IntAutoModel):
    farm = sheraf.ModelAttribute("FarmA").index(unique=True)

    farm_size = sheraf.Index(farm)

    @farm_size.search
    def search_farm_size(self, size):
        return size

    @farm_size.values
    def index_farm_size(self, farm):
        return farm.size


def test_back_indexation_simple(sheraf_connection):
    farm = FarmA.create(size=100)
    cowboy = CowboyA.create(farm=farm)

    assert cowboy in CowboyA.search(farm_size=100)

    farm.size = 90

    assert cowboy not in CowboyA.search(farm_size=100)
    assert cowboy in CowboyA.search(farm_size=90)

    farm.size = 80

    assert cowboy not in CowboyA.search(farm_size=100)
    assert cowboy not in CowboyA.search(farm_size=90)
    assert cowboy in CowboyA.search(farm_size=80)


class FarmB(tests.IntAutoModel):
    owner = sheraf.ReverseModelAttribute("CowboyB", "farms")
    size = sheraf.IntegerAttribute()

    @size.on_edition
    def update_size(self, new, old):
        attr = self.owner.attributes["farms"]
        old_values = self.owner.before_index_edition(attr)
        yield
        self.owner.after_index_edition(attr, old_values)


class CowboyB(tests.IntAutoModel):
    farms = sheraf.LargeListAttribute(sheraf.ModelAttribute("FarmB")).index(unique=True)

    farm_size = sheraf.Index(farms)

    @farm_size.search
    def search_farm_size(self, size):
        return size

    @farm_size.values
    def index_farm_size(self, farms):
        return {farm.size for farm in farms}


def test_back_indexation_list_of_farms(sheraf_connection):
    farm1 = FarmB.create(size=100)
    farm2 = FarmB.create(size=110)
    cowboy = CowboyB.create(farms=[farm1, farm2])

    assert cowboy in CowboyB.search(farm_size=100)
    assert cowboy in CowboyB.search(farm_size=110)

    farm1.size = 90

    assert cowboy not in CowboyB.search(farm_size=100)
    assert cowboy in CowboyB.search(farm_size=90)
    assert cowboy in CowboyB.search(farm_size=110)

    farm1.size = 80

    assert cowboy not in CowboyB.search(farm_size=100)
    assert cowboy not in CowboyB.search(farm_size=90)
    assert cowboy in CowboyB.search(farm_size=80)
    assert cowboy in CowboyB.search(farm_size=110)


class FarmC(tests.IntAutoModel):
    owners = sheraf.ReverseModelAttribute("CowboyC", "farm")
    size = sheraf.IntegerAttribute()

    @size.on_edition
    def update_size(self, new, old):
        attr = CowboyC.attributes["farm"]
        old_values = {owner: owner.before_index_edition(attr) for owner in self.owners}
        yield
        for owner, old_value in old_values.items():
            owner.after_index_edition(attr, old_value)


class CowboyC(tests.IntAutoModel):
    farm = sheraf.ModelAttribute("FarmC").index()

    farm_size = sheraf.Index(farm)

    @farm_size.search
    def search_farm_size(self, size):
        return size

    @farm_size.values
    def index_farm_size(self, farm):
        return farm.size


def test_back_indexation_list_of_cowboys(sheraf_connection):
    farm = FarmC.create(size=100)
    cowboy1 = CowboyC.create(farm=farm)
    cowboy2 = CowboyC.create(farm=farm)

    assert {cowboy1, cowboy2} == CowboyC.search(farm_size=100)

    farm.size = 90

    assert not CowboyC.search(farm_size=100)
    assert {cowboy1, cowboy2} == CowboyC.search(farm_size=90)

    farm.size = 80

    assert not CowboyC.search(farm_size=100)
    assert not CowboyC.search(farm_size=90)
    assert {cowboy1, cowboy2} == CowboyC.search(farm_size=80)


class FarmD(tests.IntAutoModel):
    owners = sheraf.ReverseModelAttribute("CowboyD", "farms")
    size = sheraf.IntegerAttribute()

    @size.on_edition
    def update_size(self, new, old):
        attr = CowboyD.attributes["farms"]
        old_values = {owner: owner.before_index_edition(attr) for owner in self.owners}
        yield
        for owner, old_value in old_values.items():
            owner.after_index_edition(attr, old_value)


class CowboyD(tests.IntAutoModel):
    farms = sheraf.LargeListAttribute(sheraf.ModelAttribute("FarmD")).index()

    farm_size = sheraf.Index(farms)

    @farm_size.search
    def search_farm_size(self, size):
        return size

    @farm_size.values
    def index_farm_size(self, farms):
        return {farm.size for farm in farms}


def test_back_indexation_list_of_both(sheraf_connection):
    farm1 = FarmD.create(size=100)
    farm2 = FarmD.create(size=200)
    farm3 = FarmD.create(size=300)
    cowboy1 = CowboyD.create(farms=[farm1, farm2])
    cowboy2 = CowboyD.create(farms=[farm1, farm3])

    assert {cowboy1, cowboy2} == set(CowboyD.search(farm_size=100))
    assert {cowboy1} == set(CowboyD.search(farm_size=200))
    assert {cowboy2} == set(CowboyD.search(farm_size=300))

    farm1.size = 90

    assert not CowboyD.search(farm_size=100)
    assert {cowboy1, cowboy2} == set(CowboyD.search(farm_size=90))
    assert {cowboy1} == set(CowboyD.search(farm_size=200))
    assert {cowboy2} == set(CowboyD.search(farm_size=300))

    farm2.size = 80

    assert not CowboyD.search(farm_size=100)
    assert {cowboy1, cowboy2} == set(CowboyD.search(farm_size=90))
    assert not CowboyD.search(farm_size=200)
    assert {cowboy1} == set(CowboyD.search(farm_size=80))
    assert {cowboy2} == set(CowboyD.search(farm_size=300))

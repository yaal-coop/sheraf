import uuid

import pytest
import sheraf
import tests


class Horse(sheraf.AttributeModel):
    name = sheraf.StringAttribute().index(primary=True)
    size = sheraf.IntegerAttribute()


class Cowboy(tests.UUIDAutoModel):
    name = sheraf.StringAttribute()
    horses = sheraf.IndexedModelAttribute(Horse)


def test_create(sheraf_connection):
    george = Cowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper")

    assert "Jolly Jumper" == jolly.name
    assert jolly.mapping == george.mapping["horses"]["name"]["Jolly Jumper"]


def test_read(sheraf_database):
    with sheraf.connection(commit=True):
        george = Cowboy.create(name="George")
        jolly = george.horses.create(name="Jolly Jumper")
        assert jolly == george.horses.read("Jolly Jumper")
        assert jolly == george.horses.read(name="Jolly Jumper")

    with sheraf.connection():
        george = Cowboy.read(george.id)
        assert jolly == george.horses.read("Jolly Jumper")
        assert jolly == george.horses.read(name="Jolly Jumper")

        with pytest.raises(sheraf.ModelObjectNotFoundException):
            george.horses.read("any horse")

        with pytest.raises(sheraf.ModelObjectNotFoundException):
            george.horses.read(name="YO")


def test_read_these(sheraf_database):
    with sheraf.connection(commit=True):
        george = Cowboy.create(name="George")
        jolly = george.horses.create(name="Jolly Jumper")
        polly = george.horses.create(name="Polly Pumper")

    with sheraf.connection():
        george = Cowboy.read(george.id)

        assert [jolly, polly] == list(
            george.horses.read_these(("Jolly Jumper", "Polly Pumper"))
        )


def test_delete(sheraf_connection):
    george = Cowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper")

    assert george.horses.get() == jolly
    assert george.horses.read("Jolly Jumper") == jolly

    jolly.delete()

    with pytest.raises(sheraf.exceptions.EmptyQuerySetUnpackException):
        george.horses.get()

    with pytest.raises(sheraf.ModelObjectNotFoundException):
        assert george.horses.read("Jolly Jumper")


def test_create_dict(sheraf_connection):
    george = Cowboy.create(
        name="George",
        horses=[dict(name="Jolly Jumper"), dict(name="Polly Pumper")],
    )

    jolly = george.horses.read("Jolly Jumper")
    polly = george.horses.read("Polly Pumper")

    assert jolly.mapping == george.mapping["horses"]["name"]["Jolly Jumper"]
    assert polly.mapping == george.mapping["horses"]["name"]["Polly Pumper"]


def test_string_model(sheraf_database):
    class Horseboy(tests.UUIDAutoModel):
        name = sheraf.StringAttribute()
        horses = sheraf.IndexedModelAttribute(Horse)

    with sheraf.connection():
        george = Horseboy.create(name="George")
        jolly = george.horses.create(name="Jolly Jumper")
        assert isinstance(jolly, Horse)
        assert isinstance(george.horses.read("Jolly Jumper"), Horse)


def test_count(sheraf_connection):
    george = Cowboy.create(name="George")
    assert 0 == george.horses.count()
    george.horses.create(name="Jolly Jumper")
    assert 1 == george.horses.count()


def test_all(sheraf_connection):
    george = Cowboy.create(name="George")
    assert [] == list(george.horses.all())

    jolly = george.horses.create(name="Jolly Jumper")
    assert [jolly] == list(george.horses.all())

    polly = george.horses.create(name="Polly pumper")
    assert [jolly, polly] == list(george.horses.all())


def test_primary_attribute_cannot_be_edited(sheraf_connection):
    first_id = str(uuid.uuid4())
    second_id = str(uuid.uuid4())

    george = Cowboy.create(id=first_id)
    assert george.id == first_id

    with pytest.raises(sheraf.SherafException):
        george.id = second_id

    assert george.id == first_id


def test_unchanged_primary_attribute_can_be_assigned(sheraf_connection):
    first_id = str(uuid.uuid4())

    george = Cowboy.create(id=first_id)
    assert george.id == first_id

    george.id = first_id

    assert george.id == first_id


def test_no_primary_key(sheraf_database):
    class HorseWithNoName(sheraf.AttributeModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()

    class HorseKeeper(tests.UUIDAutoModel):
        horses = sheraf.IndexedModelAttribute(HorseWithNoName)

    with sheraf.connection():
        keeper = HorseKeeper.create()

        with pytest.raises(sheraf.PrimaryKeyException):
            keeper.horses.create()


def test_get(sheraf_connection):
    george = Cowboy.create(name="George")

    with pytest.raises(sheraf.QuerySetUnpackException):
        george.horses.get()

    jolly = george.horses.create(name="Jolly Jumper")

    assert jolly == george.horses.get()

    george.horses.create(name="Polly Pumper")

    with pytest.raises(sheraf.QuerySetUnpackException):
        george.horses.get()


def test_filter(sheraf_connection):
    george = Cowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper", size=5)
    polly = george.horses.create(name="Polly Pumper", size=5)
    george.horses.create(name="Loosy Lumper", size=4)

    assert [jolly, polly] == list(george.horses.filter(size=5))
    assert [] == george.horses.filter(size=90000)


def test_order(sheraf_connection):
    george = Cowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper", size=6)
    polly = george.horses.create(name="Polly Pumper", size=5)
    loosy = george.horses.create(name="Loosy Lumper", size=4)

    assert [jolly, polly, loosy] == george.horses.order(size=sheraf.DESC)
    assert [loosy, polly, jolly] == george.horses.order(size=sheraf.ASC)


def test_on_creation(sheraf_connection):
    class SubModelA(sheraf.AttributeModel):
        id = sheraf.StringAttribute().index(primary=True)
        trigger = sheraf.BooleanAttribute(default=False)

    class SubModelB(sheraf.AttributeModel):
        id = sheraf.StringAttribute().index(primary=True)
        trigger = sheraf.BooleanAttribute(default=False)

    class Model(tests.IntAutoModel):
        sub_a = sheraf.IndexedModelAttribute(SubModelA)
        sub_b = sheraf.IndexedModelAttribute(SubModelB)

    @SubModelA.on_creation
    def foo_creation(model):
        model.trigger = True

    m = Model.create(sub_a=[{"id": "A"}], sub_b=[{"id": "B"}])
    assert m.sub_a.read("A").trigger
    assert not m.sub_b.read("B").trigger


def test_on_deletion(sheraf_connection):
    class SubModel(sheraf.AttributeModel):
        id = sheraf.StringAttribute().index(primary=True)
        trigger = False

    class Model(tests.IntAutoModel):
        sub = sheraf.IndexedModelAttribute(SubModel)

    @SubModel.on_deletion
    def foo_deletion(model):
        SubModel.trigger = True

    m = Model.create(sub=[{"id": "A"}])
    assert not SubModel.trigger
    m.sub.read("A").delete()
    assert SubModel.trigger


class IndexedHorse(sheraf.AttributeModel):
    name = sheraf.StringAttribute().index(primary=True)
    size = sheraf.IntegerAttribute()


class IndexedCowboy(tests.UUIDAutoModel):
    name = sheraf.StringAttribute()
    horses = sheraf.IndexedModelAttribute("IndexedHorse").index(unique=True)


def test_indexation(sheraf_connection):
    george = IndexedCowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper")
    polly = george.horses.create(name="Polly Pumper")

    george.index_keys("horses") == {
        jolly.identifier,
        polly.identifier,
    }
    IndexedCowboy.search_keys(horses=jolly) == jolly.name
    IndexedCowboy.search_keys(horses=jolly.name) == jolly.name

    horses_table = sheraf_connection.root()[IndexedCowboy.table]["horses"]
    assert set(horses_table.keys()) == {
        jolly.identifier,
        polly.identifier,
    }
    assert IndexedCowboy.search(horses=jolly.name).get() == george
    assert IndexedCowboy.search(horses=jolly).get() == george

    george = IndexedCowboy.read(george.id)
    assert set(horses_table.keys()) == {
        jolly.identifier,
        polly.identifier,
    }
    assert IndexedCowboy.search(horses=jolly.name).get() == george
    assert IndexedCowboy.search(horses=jolly).get() == george

    dolly = george.horses.create(name="Dolly Dumper")
    assert set(horses_table.keys()) == {
        jolly.identifier,
        polly.identifier,
        dolly.identifier,
    }
    assert IndexedCowboy.search(horses=jolly.name).get() == george
    assert IndexedCowboy.search(horses=jolly).get() == george
    assert IndexedCowboy.search(horses=dolly.name).get() == george
    assert IndexedCowboy.search(horses=dolly).get() == george


class ReverseIndexedHorse(sheraf.AttributeModel):
    name = sheraf.StringAttribute().index(primary=True)
    size = sheraf.IntegerAttribute()
    cowboy = sheraf.ReverseModelAttribute("ReverseIndexedCowboy", "horses")


class ReverseIndexedCowboy(tests.UUIDAutoModel):
    name = sheraf.StringAttribute()
    horses = sheraf.IndexedModelAttribute("ReverseIndexedHorse").index(unique=True)


def test_reverse_indexation(sheraf_connection):
    george = ReverseIndexedCowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper")

    assert jolly.cowboy == george

import pytest
import sheraf


class Horse(sheraf.AttributeModel):
    name = sheraf.StringAttribute().index(primary=True)
    size = sheraf.IntegerAttribute()


class Cowboy(sheraf.AutoModel):
    name = sheraf.StringAttribute()
    horses = sheraf.IndexedModelAttribute(Horse)


def test_create(sheraf_connection):
    george = Cowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper")

    assert "Jolly Jumper" == jolly.name
    assert jolly._persistent == george._persistent["horses"]["name"]["Jolly Jumper"]


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
            george.read("any horse")

        with pytest.raises(sheraf.ModelObjectNotFoundException):
            george.read(id="YO")


def test_read_these(sheraf_database):
    with sheraf.connection(commit=True):
        george = Cowboy.create(name="George")
        jolly = george.horses.create(name="Jolly Jumper")
        polly = george.horses.create(name="Polly Pumper")

    with sheraf.connection():
        george = Cowboy.read(george.id)

        assert {jolly, polly} == set(
            george.horses.read_these(("Jolly Jumper", "Polly Pumper"))
        )


def test_create_dict(sheraf_connection):
    george = Cowboy.create(
        name="George", horses=[dict(name="Jolly Jumper"), dict(name="Polly Pumper")],
    )

    jolly = george.horses.read("Jolly Jumper")
    polly = george.horses.read("Polly Pumper")

    assert jolly._persistent == george._persistent["horses"]["name"]["Jolly Jumper"]
    assert polly._persistent == george._persistent["horses"]["name"]["Polly Pumper"]


def test_string_model(sheraf_database):
    class Horseboy(sheraf.AutoModel):
        name = sheraf.StringAttribute()
        horses = sheraf.IndexedModelAttribute(
            "tests.attributes.test_indexed_models.Horse"
        )

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


def test_no_primary_key(sheraf_database):
    class HorseWithNoName(sheraf.IndexedModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()

    class HorseKeeper(sheraf.AutoModel):
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

    assert {jolly, polly} == set(george.horses.filter(size=5))
    assert [] == george.horses.filter(size=90000)


def test_order(sheraf_connection):
    george = Cowboy.create(name="George")
    jolly = george.horses.create(name="Jolly Jumper", size=6)
    polly = george.horses.create(name="Polly Pumper", size=5)
    loosy = george.horses.create(name="Loosy Lumper", size=4)

    assert [jolly, polly, loosy] == george.horses.order(size=sheraf.DESC)
    assert [loosy, polly, jolly] == george.horses.order(size=sheraf.ASC)

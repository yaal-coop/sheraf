import datetime

import libfaketime
import pytest

import sheraf
import sheraf.exceptions
import tests


class Submodel1(sheraf.Model):
    table = "submodel1"
    name = sheraf.SimpleAttribute()


class Submodel2(sheraf.Model):
    table = "submodel2"
    name = sheraf.SimpleAttribute()


utc_now = datetime.datetime(2016, 12, 31, 23, 59, 59, 5000)


@libfaketime.fake_time(utc_now)
@pytest.mark.parametrize(
    "model",
    [
        Submodel1,
        "{}.{}".format(Submodel1.__module__, Submodel1.__name__),
        "{}.{}".format(Submodel1.__module__, Submodel1.__name__).encode("utf-8"),
    ],
)
def test_simple_model(sheraf_database, model):
    sheraf_database.reset()

    class Other(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection() as conn:
        a = Submodel1.create()

        other = Other.create()
        assert other.submodel is None
        other.submodel = a
        assert a.id == other.mapping["submodel"]

        _other = Other.read(other.id)
        assert a == _other.submodel
        conn.transaction_manager.commit()

        assert utc_now == a.creation_datetime()
        assert utc_now == a.last_update_datetime()


def test_set_to_none(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    model = Model.create()
    model.submodel = Submodel1.create()
    assert model.submodel
    model.submodel = None
    assert model.submodel is None


def test_set_id(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        submodel = Submodel1.create()
        model = Model.create(submodel=submodel.id)
        assert model.submodel == submodel

    with sheraf.connection():
        model = Model.read(model.id)
        assert model.submodel == submodel


def test_set_bad_id(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    model = Model.create(submodel="invalid")
    assert model.submodel is None


def test_create(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    model = Model.create(submodel={"name": "A"})
    assert isinstance(model.submodel, Submodel1)
    assert isinstance(model.submodel.mapping, sheraf.types.SmallDict)
    assert "A" == model.submodel.name


def test_delete(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    sub1 = Submodel1.create(name="foobar")
    m = Model.create(submodel=sub1)
    assert m.submodel.name == "foobar"

    sub1.delete()

    assert m.submodel is None


def test_update_edition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        model = Model.create(submodel={"name": "YOH"})
        last_sub_id = model.submodel.id

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": {"name": "YEAH"}}, edition=True)

        assert isinstance(Model.read(model.id).submodel, Submodel1)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(Model.read(model.id).submodel, Submodel1)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id


def test_update_edition_with_model(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        sub1 = Submodel1.create()
        sub2 = Submodel1.create()

        model = Model.create(submodel=sub1)

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": sub2}, edition=True)
        assert model.submodel == sub2

    with sheraf.connection():
        model = Model.read(model.id)
        assert model.submodel == sub2


def test_update_edition_with_id(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        sub1 = Submodel1.create()
        sub2 = Submodel1.create()

        model = Model.create(submodel=sub1)

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": sub2.id}, edition=True)
        assert model.submodel == sub2

    with sheraf.connection():
        model = Model.read(model.id)
        assert model.submodel == sub2


def test_update_no_edition(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        model = Model.create(submodel={"name": "YOH"})
        last_sub_id = model.submodel.id

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": {"name": "YEAH"}}, edition=False)

        assert isinstance(Model.read(model.id).submodel, Submodel1)
        assert "YOH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(Model.read(model.id).submodel, Submodel1)
        assert "YOH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id


def test_update_replacement_with_dict(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        model = Model.create(submodel={"name": "YOH"})
        last_sub_id = model.submodel.id

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": {"name": "YEAH"}}, replacement=True)

        assert isinstance(Model.read(model.id).submodel, Submodel1)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id != last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(Model.read(model.id).submodel, Submodel1)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id != last_sub_id


def test_delete_before_created(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1)

    with sheraf.connection(commit=True):
        m = Model.create()
        m.submodel = None


def test_indexation(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute(Submodel1).index()

    m = Model.create()
    assert m.submodel is None

    s = Submodel1.create(name="foo")
    m = Model.create(submodel=s)
    assert [m] == Model.search(submodel=s)


def test_generic_nominal_case(sheraf_database):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute((Submodel1, Submodel2))

    with sheraf.connection(commit=True):
        s1 = Submodel1.create(name="foo")
        s2 = Submodel2.create(name="bar")

        m1 = Model.create(submodel=s1)
        m2 = Model.create(submodel=s2)

        assert (Submodel1.table, s1.id) == m1.mapping["submodel"]
        assert (Submodel2.table, s2.id) == m2.mapping["submodel"]

        assert "foo" == m1.submodel.name
        assert "bar" == m2.submodel.name

    with sheraf.connection():
        m1 = Model.read(m1.id)
        m2 = Model.read(m2.id)

        assert isinstance(m1.submodel, Submodel1)
        assert isinstance(m2.submodel, Submodel2)

        assert "foo" == m1.submodel.name
        assert "bar" == m2.submodel.name


def test_generic_indexation(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        submodel = sheraf.ModelAttribute((Submodel1, Submodel2)).index()

    s1 = Submodel1.create(name="foo")
    s2 = Submodel2.create(name="bar")

    m1 = Model.create(submodel=s1)
    m2 = Model.create(submodel=s2)

    assert (Submodel1.table, s1.id) == m1.mapping["submodel"]
    assert (Submodel2.table, s2.id) == m2.mapping["submodel"]

    assert [m1] == Model.search(submodel=s1)
    assert [m2] == Model.search(submodel=s2)

    assert (
        m1.mapping
        in sheraf_connection.root()[Model.table]["submodel"][(Submodel1.table, s1.id)]
    )
    assert (
        m2.mapping
        in sheraf_connection.root()[Model.table]["submodel"][(Submodel2.table, s2.id)]
    )


def test_raise_exception_if_no_model_are_defined(sheraf_database):
    with pytest.raises(sheraf.exceptions.SherafException) as e:

        class Model(tests.UUIDAutoModel):
            submodel = sheraf.ModelAttribute()

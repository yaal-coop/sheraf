import datetime

import libfaketime
import pytest

import sheraf


class Submodel(sheraf.AutoModel):
    name = sheraf.SimpleAttribute()


utc_now = datetime.datetime(2016, 12, 31, 23, 59, 59, 5000)


@libfaketime.fake_time(utc_now)
@pytest.mark.parametrize(
    "model",
    [
        Submodel,
        "{}.{}".format(Submodel.__module__, Submodel.__name__),
        "{}.{}".format(Submodel.__module__, Submodel.__name__).encode("utf-8"),
    ],
)
def test_simple_model(sheraf_database, model):
    sheraf_database.reset()

    class Other(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    with sheraf.connection() as conn:
        a = Submodel.create()

        other = Other.create()
        assert other.submodel is None

        other.submodel = a

        _other = Other.read(other.id)
        assert a == _other.submodel
        conn.transaction_manager.commit()

        assert utc_now == a.creation_datetime()
        assert utc_now == a.last_update_datetime()


def test_set_to_none(sheraf_connection):
    class Model(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    model = Model.create()
    model.submodel = Submodel.create()
    assert model.submodel
    model.submodel = None
    assert model.submodel is None


def test_create(sheraf_connection):
    class ModelForTest(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    model = ModelForTest.create(submodel={"name": "A"})
    assert isinstance(model.submodel, Submodel)
    assert isinstance(model.submodel._persistent, sheraf.types.SmallDict)
    assert "A" == model.submodel.name


def test_update_edition(sheraf_database):
    class Model(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    with sheraf.connection(commit=True):
        model = Model.create(submodel={"name": "YOH"})
        last_sub_id = model.submodel.id

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": {"name": "YEAH"}}, edition=True)

        assert isinstance(Model.read(model.id).submodel, Submodel)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(Model.read(model.id).submodel, Submodel)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id


def test_update_no_edition(sheraf_database):
    class Model(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    with sheraf.connection(commit=True):
        model = Model.create(submodel={"name": "YOH"})
        last_sub_id = model.submodel.id

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": {"name": "YEAH"}}, edition=False)

        assert isinstance(Model.read(model.id).submodel, Submodel)
        assert "YOH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(Model.read(model.id).submodel, Submodel)
        assert "YOH" == Model.read(model.id).submodel.name
        assert model.submodel.id == last_sub_id


def test_update_replacement(sheraf_database):
    class Model(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    with sheraf.connection(commit=True):
        model = Model.create(submodel={"name": "YOH"})
        last_sub_id = model.submodel.id

    with sheraf.connection(commit=True):
        model.edit(value={"submodel": {"name": "YEAH"}}, replacement=True)

        assert isinstance(Model.read(model.id).submodel, Submodel)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id != last_sub_id

    with sheraf.connection():
        model = Model.read(model.id)

        assert isinstance(Model.read(model.id).submodel, Submodel)
        assert "YEAH" == Model.read(model.id).submodel.name
        assert model.submodel.id != last_sub_id


def test_delete_before_created(sheraf_database):
    class Model(sheraf.AutoModel):
        submodel = sheraf.ModelAttribute(Submodel)

    with sheraf.connection(commit=True):
        m = Model.create()
        m.submodel = None

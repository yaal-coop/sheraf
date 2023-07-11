import pytest
import sheraf
import tests


@pytest.fixture
def db2(request):
    database = None
    try:
        database = sheraf.Database("memory://?database_name=db2")
        yield database

    finally:
        if database:
            database.close()


def test_model_create_in_default_connection(sheraf_database, db2):
    class Model(tests.UUIDAutoModel):
        pass

    class MyDefaultModel(tests.UUIDAutoModel):
        database_name = "unnamed"

    class MyDB2Model(tests.UUIDAutoModel):
        database_name = "db2"

    with sheraf.connection(commit=True) as connection:
        rootd = connection.root()
        m = Model.create()
        md = MyDefaultModel.create()
        m2 = MyDB2Model.create()

    with sheraf.connection() as connection:
        rootd = connection.root()
        root2 = connection.get_connection("db2").root()

        assert m.id in rootd[Model.table]["id"]
        assert md.id in rootd[MyDefaultModel.table]["id"]
        assert m2.id in root2[MyDB2Model.table]["id"]

        assert Model.table not in root2
        assert MyDefaultModel.table not in root2
        assert MyDB2Model.table not in rootd


def test_model_with_database_name_specified(sheraf_database, db2):
    class Db2Model(tests.UUIDAutoModel):
        database_name = "db2"

    with sheraf.connection(commit=True):
        m = Db2Model.create()
        n = Db2Model.create()
        m_id = m.id

    with sheraf.connection() as connection:
        assert m.id not in connection.root().get(Db2Model.table, {})

        connection_2 = connection.get_connection("db2")
        assert connection_2.root()[Db2Model.table]["id"][m.id] is m.mapping
        assert Db2Model.read(m.id) == m
        assert Db2Model.count() == 2
        assert m in Db2Model.all()
        assert n in Db2Model.all()

        m.delete()
        assert m_id not in connection_2.root()[Db2Model.table]["id"]
        assert Db2Model.count() == 1

        n.delete()
        assert Db2Model not in connection_2.root()
        assert Db2Model.count() == 0


def test_database_retrocompatibility(sheraf_database, db2):
    """
    When a model is assigned a new database. We should still
    be able to delete instances created in the old database.
    """

    class Model(tests.UUIDAutoModel):
        pass

    with sheraf.connection(commit=True):
        m0 = Model.create()
        m1 = Model.create()
        m1_id = m1.id

    class Model(tests.UUIDAutoModel):
        database_name = "db2"

    with sheraf.connection() as connection:
        root1 = connection.root()
        root2 = connection.get_connection("db2").root()

        m2 = Model.create()
        assert root1[Model.table]["id"][m1.id] is m1.mapping
        assert m1.id not in root2[Model.table]["id"]
        assert m1.mapping == Model.read(m1.id).mapping
        assert Model.count() == 3
        assert m0 in Model.all()
        assert m1 in Model.all()
        assert m2 in Model.all()

        m1.delete()
        assert m1_id not in root1[Model.table]["id"]
        assert Model.count() == 2

        m0.delete()
        assert Model.table not in root1
        assert Model.count() == 1


def test_make_id(sheraf_database, db2):
    class Model(tests.UUIDAutoModel):
        pass

    class ModelWithProposeId(Model):
        table = "modelwithproposeid"
        id = sheraf.IntegerAttribute(default=lambda m: m.count()).index(primary=True)

    with sheraf.connection(commit=True):
        m0 = ModelWithProposeId.create()
        m1 = ModelWithProposeId.create()
        assert m0.id == 0
        assert m1.id == 1

    class Model(tests.UUIDAutoModel):
        database_name = "db2"

    class ModelWithProposeId(Model):
        table = "modelwithproposeid"
        id = sheraf.IntegerAttribute(default=lambda m: m.count()).index(primary=True)

    with sheraf.connection() as conn:
        root1 = conn.root()
        root2 = conn.get_connection("db2").root()

        m2 = ModelWithProposeId.create()
        m3 = ModelWithProposeId.create()
        assert m2.id == 2
        assert m3.id == 3

        assert root1["modelwithproposeid"]["id"][m1.id] is m1.mapping
        assert root2["modelwithproposeid"]["id"][m2.id] is m2.mapping

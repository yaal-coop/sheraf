import mock
import pytest
import sheraf


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
    class MyModel(sheraf.AutoModel):
        pass

    class MyDefaultModel(sheraf.AutoModel):
        database_name = "unnamed"

    class MyDB2Model(sheraf.AutoModel):
        database_name = "db2"

    with sheraf.connection(commit=True) as connection:
        rootd = connection.root()
        m = MyModel.create()
        md = MyDefaultModel.create()
        m2 = MyDB2Model.create()

    with sheraf.connection() as connection:
        rootd = connection.root()
        root2 = connection.get_connection("db2").root()

        assert rootd[MyModel.table] is MyModel.index_root()
        assert rootd[MyDefaultModel.table] is MyDefaultModel.index_root()
        assert root2[MyDB2Model.table] is MyDB2Model.index_root()

        assert m.id in rootd[MyModel.table]["id"]
        assert md.id in rootd[MyDefaultModel.table]["id"]
        assert m2.id in root2[MyDB2Model.table]["id"]

        assert MyModel.table not in root2
        assert MyDefaultModel.table not in root2
        assert MyDB2Model.table not in rootd


def test_model_with_database_name_specified(sheraf_database, db2):
    class Db2Model(sheraf.AutoModel):
        database_name = "db2"

    with sheraf.connection(commit=True):
        m = Db2Model.create()

    with sheraf.connection() as connection:
        assert m.id not in connection.root().get(Db2Model.table, {})

        connection_2 = connection.get_connection("db2")
        assert connection_2.root()[Db2Model.table]["id"][m.id] is m._persistent
        assert Db2Model.read(m.id) == m
        assert Db2Model.count() == 1
        assert Db2Model.all() == [m]

        m.delete()
        assert m.id not in connection_2.root()[Db2Model.table]["id"]
        assert Db2Model.count() == 0


def test_database_retrocompatibility(sheraf_database, db2):
    """
    When a model is assigned a new database. We should still
    be able to delete instances created in the old database.
    """

    class MyModel(sheraf.AutoModel):
        pass

    with sheraf.connection(commit=True):
        m1 = MyModel.create()

    class MyModel(sheraf.AutoModel):
        database_name = "db2"

    with sheraf.connection() as connection:
        root1 = connection.root()
        root2 = connection.get_connection("db2").root()

        m2 = MyModel.create()
        assert root1[MyModel.table]["id"][m1.id] is m1._persistent
        assert m1.id not in root2[MyModel.table]["id"]
        assert m1._persistent == MyModel.read(m1.id)._persistent
        assert MyModel.count() == 2
        assert set(MyModel.all()) == {m1, m2}

        m1.delete()
        assert m1.id not in root1[MyModel.table]["id"]
        assert MyModel.count() == 1


def test_make_id(sheraf_database, db2):
    class MyModel(sheraf.AutoModel):
        pass

    class ModelWithProposeId(MyModel):
        table = "modelwithproposeid"
        id = sheraf.IntegerAttribute(default=lambda m: m.count()).index(primary=True)

    with sheraf.connection(commit=True):
        m0 = ModelWithProposeId.create()
        m1 = ModelWithProposeId.create()
        assert m0.id == 0
        assert m1.id == 1

    class MyModel(sheraf.AutoModel):
        database_name = "db2"

    class ModelWithProposeId(MyModel):
        table = "modelwithproposeid"
        id = sheraf.IntegerAttribute(default=lambda m: m.count()).index(primary=True)

    with sheraf.connection() as conn:
        root1 = conn.root()
        root2 = conn.get_connection("db2").root()

        m2 = ModelWithProposeId.create()
        m3 = ModelWithProposeId.create()
        assert m2.id == 2
        assert m3.id == 3

        assert root1["modelwithproposeid"]["id"][m1.id] is m1._persistent
        assert root2["modelwithproposeid"]["id"][m2.id] is m2._persistent

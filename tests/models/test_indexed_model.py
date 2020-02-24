import mock
import pytest
import uuid

import sheraf


class MyInlineModel(sheraf.InlineModel):
    pass


class MyModel(sheraf.AutoModel):
    inline_model = sheraf.InlineModelAttribute(MyInlineModel)


def test_read_invalid_parameters(sheraf_connection):
    class M(sheraf.AutoModel):
        pass

    with pytest.raises(TypeError):
        M.read(1, 2)

    with pytest.raises(TypeError):
        M.read(1, id=2)

    with pytest.raises(TypeError):
        M.read(foo=1, id=2)


def test_read_these_invalid_index(sheraf_database):
    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.ModelObjectNotFoundException):
            list(MyModel.read_these(["invalid"]))


def test_read_these_valid_index(sheraf_database):
    with sheraf.connection():
        m = MyModel.create()
        assert [m] == list(MyModel.read_these([m.id]))


def test_count(sheraf_database):
    class M(sheraf.AutoModel):
        pass

    with sheraf.connection():
        assert 0 == M.count()
        M.create()
        M.create()
        assert 2 == M.count()


def test_default_id(sheraf_database):
    class M(sheraf.AutoModel):
        id = sheraf.IntegerAttribute(default=lambda m: m.count()).index(primary=True)

    with sheraf.connection():
        assert 0 == M.create().id
        assert 1 == M.create().id
        assert 2 == M.create().id
        assert 3 == M.create().id

    class N(sheraf.IndexedModel):
        table = "n"
        pass

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.SherafException):
            N.create()


def test_model_with_id(sheraf_database):
    with sheraf.connection():
        m = MyModel.create()
        assert "<MyModel id={}>".format(m.id) == repr(m)


def test_model_without_id(sheraf_database):
    assert "<MyModel id=None>" == repr(MyModel())


def test_all(sheraf_database):
    class MyModel(sheraf.IntOrderedNamedAttributesModel):
        table = "my_test_all_model"

    with sheraf.connection(commit=True):
        m0 = MyModel.create()
        m1 = MyModel.create()
        m2 = MyModel.create()

    with sheraf.connection():
        all_queryset = MyModel.all()
        assert sheraf.queryset.QuerySet([m0, m1, m2]) == all_queryset
        assert sheraf.queryset.QuerySet() == all_queryset

        assert sheraf.queryset.QuerySet([m0, m1, m2]) == MyModel.all()


def test_single_database(sheraf_database):
    with sheraf.connection(commit=True):
        m = MyModel.create()
    with sheraf.connection() as connection:
        assert connection.root()[MyModel.table]["id"][m.id] is m._persistent


def test_two_databases_and_model_in_default_database(sheraf_database):
    sheraf.Database("memory://?database_name=db2")
    with sheraf.connection(commit=True):
        m = MyModel.create()

    with sheraf.connection() as connection:
        assert connection.root()[MyModel.table]["id"][m.id] is m._persistent
        assert MyModel.table not in connection.get_connection("db2").root()
    sheraf.Database.get("db2").close()


def test_two_databases_and_model_with_database_name_specified(sheraf_database):
    sheraf.Database("memory://?database_name=db2")

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
    sheraf.Database.get("db2").close()


def test_database_retrocompatibility(sheraf_database):
    with sheraf.connection(commit=True):
        m1 = MyModel.create()
    sheraf.Database("memory://?database_name=db2")
    with mock.patch(__name__ + ".MyModel.database_name", "db2"):
        with sheraf.connection() as connection:
            m2 = MyModel.create()
            assert connection.root()[MyModel.table]["id"][m1.id] is m1._persistent
            assert m1.id not in connection.get_connection("db2").root()[MyModel.table]
            assert m1._persistent == MyModel.read(m1.id)._persistent
            assert MyModel.count() == 2
            assert set(MyModel.all()) == {m1, m2}
            m1.delete()
            assert m1.id not in connection.root()[MyModel.table]["id"]
    sheraf.Database.get("db2").close()


def test_make_id_with_two_databases(sheraf_database):
    class ModelWithProposeId(MyModel):
        table = "modelwithproposeid"
        id = sheraf.IntegerAttribute(default=lambda m: m.count()).index(primary=True)

    with sheraf.connection(commit=True):
        m0 = ModelWithProposeId.create()
        m1 = ModelWithProposeId.create()
        assert m0.id == 0
        assert m1.id == 1

    ModelWithProposeId.current_id = -1
    sheraf.Database("memory://?database_name=db2")

    with mock.patch(__name__ + ".MyModel.database_name", "db2"):
        with sheraf.connection():
            m2 = ModelWithProposeId.create()
            m3 = ModelWithProposeId.create()
            assert m2.id == 2
            assert m3.id == 3

    sheraf.Database.get("db2").close()


def test_id_in_persistent_uuid_model(sheraf_database):
    mid = uuid.uuid4()

    class M(sheraf.Model):
        table = "test_uuid_model"
        id = sheraf.StringUUIDAttribute(default=lambda: "{}".format(str(mid))).index(
            primary=True
        )

    assert isinstance(M.attributes["id"], sheraf.attributes.simples.StringUUIDAttribute)

    with sheraf.connection():
        m = M.create()
        assert mid.int == m._persistent["id"]


def test_id_in_persistent_int_model(sheraf_database):
    mid = 15

    class M(sheraf.IntIndexedNamedAttributesModel):
        table = "test_int_model"
        id = sheraf.IntegerAttribute(default=mid).index(primary=True)

    assert isinstance(M.attributes["id"], sheraf.attributes.simples.IntegerAttribute)

    with sheraf.connection():
        m = M.create()
        assert mid == m._persistent["id"]


def test_id_in_persistent_automodel(sheraf_database):
    mid = str(uuid.uuid4())

    class M(sheraf.AutoModel):
        id = sheraf.StringUUIDAttribute(default=mid).index(primary=True)

    assert isinstance(M.attributes["id"], sheraf.attributes.simples.StringUUIDAttribute)

    with sheraf.connection():
        m = M.create()
        assert mid == str(uuid.UUID(int=m._persistent["id"]))

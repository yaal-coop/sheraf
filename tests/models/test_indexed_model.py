import pytest
import uuid
import sheraf
import tests
from sheraf.models.indexation import model_from_table


class MyInlineModel(sheraf.InlineModel):
    pass


class Model(tests.UUIDAutoModel):
    inline_model = sheraf.InlineModelAttribute(MyInlineModel)


def test_read_invalid_parameters(sheraf_connection):
    class M(tests.UUIDAutoModel):
        pass

    with pytest.raises(TypeError):
        M.read(1, 2)

    with pytest.raises(TypeError):
        M.read(1, id=2)

    with pytest.raises(TypeError):
        M.read(foo=1, id=2)


def test_read_raises_no_database_connection_exception(sheraf_connection):
    class MyModel(sheraf.Model):
        table = "test_read_raises_no_database_connection_exception"
        database_name = "unexisting_db_name"

    with pytest.raises(sheraf.exceptions.NoDatabaseConnectionException) as exc:
        MyModel.read("id")

    assert str(exc.value) == "unexisting_db_name"
    assert isinstance(exc.value, sheraf.exceptions.SherafException)


def test_read_these_invalid_index(sheraf_connection):
    with pytest.raises(sheraf.exceptions.ModelObjectNotFoundException):
        list(Model.read_these(["invalid"]))


def test_read_these_valid_index(sheraf_connection):
    m = Model.create()
    assert [m] == list(Model.read_these([m.id]))


def test_read_these_invalid_calls(sheraf_connection):
    with pytest.raises(TypeError):
        Model.read_these()

    with pytest.raises(TypeError):
        Model.read_these(id=["foo"], inline_model=["bar"])

    with pytest.raises(sheraf.exceptions.InvalidIndexException):
        Model.read_these(yolo=["foo"])


def test_count(sheraf_connection):
    class M(tests.UUIDAutoModel):
        foo = sheraf.IntegerAttribute()
        evens = sheraf.Index(foo, index_keys_func=lambda x: {x} if x % 2 == 0 else {})

    assert 0 == M.count()
    assert 0 == M.count("evens")

    M.create(foo=1)
    M.create(foo=2)

    assert 2 == M.count()
    assert 1 == M.count("evens")


def test_default_id(sheraf_database):
    class M(tests.UUIDAutoModel):
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


def test_repr_model_with_id(sheraf_database):
    with sheraf.connection():
        m = Model.create()
        assert "<Model id={}>".format(m.id) == repr(m)


def test_repr_model_without_id(sheraf_database):
    assert "<Model id=None>" == repr(Model())


def test_all(sheraf_database):
    class Model(sheraf.IntOrderedNamedAttributesModel):
        table = "my_test_all_model"

    with sheraf.connection(commit=True):
        m0 = Model.create()
        m1 = Model.create()
        m2 = Model.create()

    with sheraf.connection():
        all_queryset = Model.all()
        assert sheraf.queryset.QuerySet([m0, m1, m2]) == all_queryset
        assert sheraf.queryset.QuerySet() == all_queryset

        assert sheraf.queryset.QuerySet([m0, m1, m2]) == Model.all()


def test_all_with_parameters_unique(sheraf_database):
    class Model(sheraf.IntOrderedNamedAttributesModel):
        table = "my_test_all_model"
        foo = sheraf.SimpleAttribute().index(unique=True)

    with sheraf.connection(commit=True):
        m0 = Model.create(foo="bar")
        m1 = Model.create(foo="baz")
        m2 = Model.create(foo="bal")
        Model.create()

    with sheraf.connection():
        assert {m0, m1, m2} == set(Model.all("foo"))


def test_all_with_parameters_multiple(sheraf_database):
    class Model(sheraf.IntOrderedNamedAttributesModel):
        table = "my_test_all_model"
        foo = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        m0 = Model.create(foo="bar")
        m1 = Model.create(foo="bar")
        m2 = Model.create(foo="baz")
        Model.create()

    with sheraf.connection():
        assert {m0, m1, m2} == set(Model.all("foo"))


def test_single_database(sheraf_database):
    with sheraf.connection(commit=True):
        m = Model.create()

    with sheraf.connection() as connection:
        assert connection.root()[Model.table]["id"][m.id] is m.mapping


def test_id_inmapping_uuid_model(sheraf_database):
    mid = uuid.uuid4()

    class M(sheraf.Model):
        table = "test_uuid_model"
        id = sheraf.StringUUIDAttribute(default=lambda: "{}".format(str(mid))).index(
            primary=True
        )

    assert isinstance(M.attributes["id"], sheraf.attributes.simples.StringUUIDAttribute)

    with sheraf.connection():
        m = M.create()
        assert mid.int == m.mapping["id"]


def test_id_inmapping_int_model(sheraf_database):
    mid = 15

    class M(sheraf.IntIndexedNamedAttributesModel):
        table = "test_int_model"
        id = sheraf.IntegerAttribute(default=mid).index(primary=True)

    assert isinstance(M.attributes["id"], sheraf.attributes.simples.IntegerAttribute)

    with sheraf.connection():
        m = M.create()
        assert mid == m.mapping["id"]


def test_id_inmapping_automodel(sheraf_database):
    mid = str(uuid.uuid4())

    class M(tests.UUIDAutoModel):
        id = sheraf.StringUUIDAttribute(default=mid).index(primary=True)

    assert isinstance(M.attributes["id"], sheraf.attributes.simples.StringUUIDAttribute)

    with sheraf.connection():
        m = M.create()
        assert mid == str(uuid.UUID(int=m.mapping["id"]))


def test_model_from_table():
    class M(sheraf.Model):
        table = "tablem"
        foo = sheraf.SimpleAttribute()

    assert model_from_table("tablem") is M
    assert model_from_table("invalid") is None


def test_delete_last_model(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        pass

    m = Model.create()
    assert m.id in sheraf_connection.root()[Model.table]["id"]

    m.delete()
    assert Model.table not in sheraf_connection.root()


def test_delete_last_model_with_another_simple_index_without_data(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(noneok=False, nullok=True)

    m = Model.create(foo=None)
    assert m.id in sheraf_connection.root()[Model.table]["id"]
    assert None not in sheraf_connection.root()[Model.table]["foo"]

    m.delete()
    assert Model.table not in sheraf_connection.root()


def test_delete_last_model_with_another_simple_index_with_data(sheraf_connection):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(noneok=False, nullok=True)

    m = Model.create(foo="bar")
    assert m.id in sheraf_connection.root()[Model.table]["id"]
    assert "bar" in sheraf_connection.root()[Model.table]["foo"]

    m.delete()
    assert Model.table not in sheraf_connection.root()


def test_first_instance_no_index_second_instance_index(sheraf_connection):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(noneok=False, nullok=True)

    m = ModelSimple.create(foo=None)

    assert None not in sheraf_connection.root()[ModelSimple.table]["foo"]
    assert m not in ModelSimple.search(foo=None)

    n = ModelSimple.create(foo="bar")
    assert "bar" in sheraf_connection.root()[ModelSimple.table]["foo"]
    assert n in ModelSimple.search(foo="bar")

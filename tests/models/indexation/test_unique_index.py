import pytest
import sheraf
import tests


class UniqueModelA(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute().index(unique=True)
    other = sheraf.SimpleAttribute()


class UniqueModelB(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    my_attribute_index = sheraf.Index("my_attribute", unique=True, key="my_attribute")
    other = sheraf.SimpleAttribute()


class UniqueModelC(tests.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()
    my_attribute_index = sheraf.Index(my_attribute, unique=True, key="my_attribute")
    other = sheraf.SimpleAttribute()


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation(sheraf_database, Model):
    assert (
        Model.attributes["my_attribute"]
        in Model.indexes["my_attribute"].details.attributes
    )

    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar = Model.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo.mapping == index_table["foo"]
        assert mbar.mapping == index_table["bar"]

        assert mbar == Model.read(my_attribute="bar")
        assert [mbar] == list(Model.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(Model.read_these(my_attribute=["bar", "foo"]))

        # Model._read_unique_index = mock.MagicMock(
        #    side_effect=Model._read_unique_index
        # )
        assert [mbar] == Model.filter(my_attribute="bar")
        # Model._read_unique_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation_and_edition(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="FOO")
        mbar = Model.create(my_attribute="BAR")

    with sheraf.connection(commit=True):
        Model.read(mfoo.id).my_attribute = "foo"
        Model.read(mbar.id).my_attribute = "bar"

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert mfoo.mapping == index_table["foo"]
        assert mbar.mapping == index_table["bar"]

        assert mbar == Model.read(my_attribute="bar")
        assert [mbar] == list(Model.read_these(my_attribute=["bar"]))
        assert [mbar, mfoo] == list(Model.read_these(my_attribute=["bar", "foo"]))

        # Model._read_unique_index = mock.MagicMock(
        #    side_effect=Model._read_unique_index
        # )
        assert [mbar] == Model.filter(my_attribute="bar")
        # Model._read_unique_index.assert_has_calls(
        #    [mock.call("bar", "my_attribute")]
        # )


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation_and_deletion(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar = Model.create(my_attribute="bar")

    with sheraf.connection(commit=True):
        mfoo.delete()

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == Model.filter(my_attribute="foo")
        assert [mbar] == Model.filter(my_attribute="bar")


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_creation_and_attribute_deletion(sheraf_database, Model):
    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute="foo")
        mbar = Model.create(my_attribute="bar")

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"foo", "bar"} == set(index_table)
        assert [mfoo] == Model.filter(my_attribute="foo")
        assert [mbar] == Model.filter(my_attribute="bar")

    with sheraf.connection(commit=True):
        del mfoo.my_attribute

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {"bar"} == set(index_table)
        assert [] == Model.filter(my_attribute="foo")
        assert [mbar] == Model.filter(my_attribute="bar")


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_double_value_create(sheraf_database, Model):
    with sheraf.connection(commit=True):
        Model.create(my_attribute="foo")
        assert Model.count() == 1

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(my_attribute="foo")
        assert Model.count() == 1


@pytest.mark.parametrize(
    "Model",
    [
        UniqueModelA,
        UniqueModelB,
        UniqueModelC,
    ],
)
def test_unique_index_double_value_set(sheraf_connection, Model):
    Model.create(my_attribute="foo")
    other = Model.create(my_attribute="anything", other="old")
    assert Model.count() == 2

    with pytest.raises(sheraf.exceptions.UniqueIndexException):
        other.other = "new"
        other.my_attribute = "foo"

    assert other.other == "new"


def test_unique_indexation_on_model_attribute(sheraf_database):
    class DummyModel(sheraf.Model):
        table = "dummymodel_table"
        val = sheraf.SimpleAttribute(lazy=False, default=str)

    class Model(sheraf.Model):
        table = "model_table"
        dummy_attribute = sheraf.ModelAttribute(DummyModel).index(
            unique=True, index_keys_func=lambda x: {x.val}
        )

    with sheraf.connection(commit=True):
        foo = DummyModel.create(val="fou")
        Model.create(dummy_attribute=foo)

    with sheraf.connection() as conn:
        index_table = conn.root()["model_table"]["dummy_attribute"]
        assert {"fou"} == set(index_table)


def test_unique_index_set_afterwards(sheraf_database):
    class DummyModel(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute().index(
            index_keys_func=lambda foo: {foo.lower()} if foo else {}
        )

    with sheraf.connection(commit=True):
        dummy = DummyModel.create()
        dummy.foo = "bar"

    with sheraf.connection():
        assert [dummy] == list(DummyModel.filter(foo="bar"))


def test_unique_index_double_attributes(sheraf_database):
    class Model(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        bar = sheraf.SimpleAttribute()

        unique = sheraf.Index(foo, bar, unique=True)
        multiple = sheraf.Index(foo, bar)

        @unique.index_keys_func(foo, bar)
        def index_unique(self, foo, bar):
            return frozenset({foo, bar})

    with sheraf.connection(commit=True):
        Model.create(foo="foo", bar="bar")
        assert Model.count() == 1

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(foo="foo", bar="bar")

        assert Model.count() == 1

    with sheraf.connection():
        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            Model.create(bar="bar", foo="foo")

        assert Model.count() == 1

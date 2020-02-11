import itertools
import random
import sys
import uuid

import BTrees

import sheraf.exceptions
from sheraf.models.base import BaseModel, BaseModelMetaclass


class IndexedModelMetaclass(BaseModelMetaclass):
    """Internal class.

    Contains the mapping of tables (name of models) to their
    corresponding model definitions
    """

    tables = {}

    def __new__(cls, name, bases, attrs):
        klass = super(IndexedModelMetaclass, cls).__new__(cls, name, bases, attrs)

        if "table" in attrs:
            table_name = attrs["table"]
            qualname = attrs["__module__"] + "." + attrs["__qualname__"]

            unique_table_name = attrs.get("unique_table_name", True)
            if (
                unique_table_name
                and table_name in IndexedModelMetaclass.tables
                and name != IndexedModelMetaclass.tables[table_name][0].split(".")[-1]
            ):
                message = "Table named '{table_name}' used twice: {first_class} and {second_class}".format(
                    table_name=table_name,
                    first_class=IndexedModelMetaclass.tables[table_name][0],
                    second_class=qualname,
                )
                raise sheraf.exceptions.SameNameForTableException(message)
            IndexedModelMetaclass.tables[table_name] = (qualname, klass)
        return klass


class IndexedModel(BaseModel, metaclass=IndexedModelMetaclass):
    """This class handles the whole indexation mechanism."""

    database_name = None
    id = sheraf.attributes.simples.SimpleAttribute()

    @staticmethod
    def _current_database_name():
        current_name = sheraf.Database.current_name()
        if not current_name:
            raise sheraf.exceptions.NotConnectedException()
        return current_name

    @staticmethod
    def _table_iterkeys(table, reverse=False):
        try:
            return table.iterkeys(reverse=reverse)
        # TODO: Remove this guard (or just keep it and remove the first lines of this function)
        # on the next compatibility breaking release.
        except TypeError:
            # Some previous stored data may have been OOBTree instead of LargeDict,
            # so the 'reverse' parameter was not available
            keys = table.iterkeys()
            if reverse:
                keys = reversed(list(keys))
            return keys

    @classmethod
    def _table(cls, database_name=None):
        database_name = (
            database_name or cls.database_name or cls._current_database_name()
        )
        _root = sheraf.Database.current_connection(database_name).root()
        index_root = _root.setdefault(cls.table, sheraf.types.SmallDict())
        return index_root.setdefault("id", cls._table_default())

    @classmethod
    def _table_default(cls):
        return sheraf.types.LargeDict()

    @classmethod
    def _tables(cls):
        return (
            cls._table(db_name)
            for db_name in (cls.database_name, cls._current_database_name())
            if db_name
        )

    @classmethod
    def _tables_contains(cls, key):
        return any(key in table for table in cls._tables())

    @classmethod
    def _tables_getitem(cls, key):
        if cls.database_name:
            try:
                return cls._table(cls.database_name)[key]
            except KeyError:
                pass
        return cls._table(cls._current_database_name())[key]

    @classmethod
    def _tables_iterkeys(cls, reverse=False):
        return itertools.chain.from_iterable(
            cls._table_iterkeys(table, reverse=reverse) for table in cls._tables()
        )

    @classmethod
    def _tables_del(cls, key):
        if cls.database_name:
            try:
                del cls._table(cls.database_name)[key]
                return
            except KeyError:
                pass
        del cls._table(sheraf.Database.current_name())[key]

    def make_id(self):
        """:return: a unique id for this object. Not intended for use"""
        _id = self.attributes["id"].create(self)
        while self._tables_contains(_id):
            _id = self.attributes["id"].create(self)

        return _id

    @classmethod
    def all(cls):
        """
        :return: A :class:`~sheraf.queryset.QuerySet` containing all the
            registered models.
        """
        return sheraf.queryset.QuerySet(model_class=cls)

    @classmethod
    def read_these(cls, ids):
        """Get model instances from their ids. If an instance id does not
        exist, a :class:`~sheraf.exceptions.ModelObjectNotFoundException` is
        raised.

        :param ids: A collection of ids.
        :return: A generator of :class:`~sheraf.models.indexation.IndexedModel`
            matching the ids.

        >>> class MyModel(sheraf.IntIndexedNamedAttributesModel):
        ...     table = "my_model"
        ...
        >>> with sheraf.connection():
        ...     m1 = MyModel.create(id=1)
        ...     m2 = MyModel.create(id=2)
        ...
        ...     assert [m1, m2] == list(MyModel.read_these([m1.id, m2.id]))
        ...     list(MyModel.read_these(["invalid"]))
        Traceback (most recent call last):
            ...
        sheraf.exceptions.ModelObjectNotFoundException: Id 'invalid' not found in MyModel
        """
        return (cls.read(id) for id in ids)

    @classmethod
    def create(cls, id=None, *args, **kwargs):
        """:return: an instance of this model"""

        if "id" not in cls.attributes:
            raise sheraf.exceptions.SherafException(
                "{} inherit from IndexedModel but has no id attribute. Cannot create.".format(
                    cls.__name__
                )
            )

        model = super(IndexedModel, cls).create(*args, **kwargs)
        table = cls._table()
        id = id or model.make_id()
        table[id] = model._persistent
        model.id = id
        return model

    @classmethod
    def read(cls, id):
        """Get a model instance from its id. If the model id does not exist, a
        :class:`~sheraf.exceptions.ModelObjectNotFoundException` is raised.

        :param id: The ``id`` of the model.
        :return: The :class:`~sheraf.models.indexation.IndexedModel` matching the id.

        >>> class MyModel(sheraf.Model):
        ...     table = "my_model"
        ...
        >>> with sheraf.connection():
        ...     m = MyModel.create()
        ...     assert MyModel.read(m.id) == m
        ...     MyModel.read("invalid")
        Traceback (most recent call last):
            ...
        sheraf.exceptions.ModelObjectNotFoundException: Id 'invalid' not found in MyModel
        """
        try:
            mapping = cls._tables_getitem(id)
            model = cls._decorate(mapping)
            return model
        except (KeyError, TypeError):
            raise sheraf.exceptions.ModelObjectNotFoundException(cls, id)

    @classmethod
    def count(cls):
        """
        :return: the number of instances.

        Using this method is faster than using ``len(MyModel.all())``.
        """
        return sum(len(table) for table in cls._tables())

    @classmethod
    def filter(cls, predicate=None, **kwargs):
        """Shortcut for :func:`sheraf.queryset.QuerySet.filter`.

        :return: :class:`sheraf.queryset.QuerySet`
        """
        return sheraf.queryset.QuerySet(model_class=cls).filter(
            predicate=predicate, **kwargs
        )

    @classmethod
    def order(cls, *args, **kwargs):
        """Shortcut for :func:`sheraf.queryset.QuerySet.order`.

        :return: :class:`sheraf.queryset.QuerySet`
        """
        return sheraf.queryset.QuerySet(model_class=cls).order(*args, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        """Shortcut for :func:`sheraf.queryset.QuerySet.filter` and
        :func:`sheraf.queryset.QuerySet.get`. ``Cowboy.get(name="Peter")`` and
        ``Cowboy.filter(name="Peter").get()`` are equivalent.

        :return: The instance of the model if the filter matches exactly one
            instance. Otherwise, it raises a
            :class:`~sheraf.exceptions.QuerySetUnpackException`.

        >>> class Cowboy(sheraf.Model):
        ...     table = "people"
        ...     name = sheraf.SimpleAttribute()
        ...     age = sheraf.SimpleAttribute()
        ...
        >>> with sheraf.connection(commit=True):
        ...     peter = Cowboy.create(name="Peter", age=30)
        ...     steven = Cowboy.create(name="Steven", age=30)
        ...     assert peter == Cowboy.get(name="Peter")
        ...
        >>> with sheraf.connection():
        ...     Cowboy.get()
        Traceback (most recent call last):
            ...
        sheraf.exceptions.QuerySetUnpackException: Trying to unpack more than 1 value from a QuerySet
        >>> with sheraf.connection():
        ...     Cowboy.get(age=30)
        Traceback (most recent call last):
            ...
        sheraf.exceptions.QuerySetUnpackException: Trying to unpack more than 1 value from a QuerySet
        >>> with sheraf.connection():
        ...     Cowboy.get(name="Unknown cowboy")
        Traceback (most recent call last):
            ...
        sheraf.exceptions.EmptyQuerySetUnpackException: Trying to unpack an empty QuerySet
        """
        return cls.filter(*args, **kwargs).get()

    def __repr__(self):
        id = (
            self.id
            if self._persistent is not None and "id" in self._persistent
            else None
        )
        return "<{} id={}>".format(self.__class__.__name__, id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return hasattr(self, "id") and hasattr(other, "id") and self.id == other.id

    def copy(self):
        copy = super(IndexedModel, self).copy()
        copy.id = copy.make_id()
        return copy

    def delete(self):
        """Delete the current model instance.

        >>> class MyModel(sheraf.Model):
        ...     table = "my_model"
        ...
        >>> with sheraf.connection():
        ...    m = MyModel.create()
        ...    assert m == MyModel.read(m.id)
        ...    m.delete()
        ...    m.read(m.id)
        Traceback (most recent call last):
            ...
        sheraf.exceptions.ModelObjectNotFoundException: Id '...' not found in MyModel
        """
        for attr in self.attributes.values():
            attr.delete(self)
        self._tables_del(self.id)


class UUIDIndexedModel:
    """Model using uuid4 as ids. Ids are stored as strings.

    >>> class MyUUIDModel(sheraf.IntIndexedModel):
    ...     table = "my_uuid_model"
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     MyIntModel.create().id
    "e4bb714e-b5a8-40d6-bb69-ab3b932fbfe0"
    """

    id = sheraf.attributes.simples.StringUUIDAttribute(
        default=lambda: "{}".format(uuid.uuid4())
    )


class IntIndexedModel:
    """Model using integers as ids.

    By default ids are 64bits integers.

    >>> class MyIntModel(sheraf.IntIndexedModel):
    ...     table = "my_int_model"
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     MyIntModel.create().id
    383428472384721983
    """

    MAX_INT = sys.maxsize
    id = sheraf.attributes.simples.IntegerAttribute(
        default=lambda m: random.randint(0, m.MAX_INT)
    )

    @classmethod
    def _table_default(cls):
        return BTrees.LOBTree.LOBTree()


class BaseAutoModelMetaclass(IndexedModelMetaclass):
    @property
    def table(self):
        return self.__name__.lower()


class BaseAutoModel(metaclass=BaseAutoModelMetaclass):
    """
    :class:`~sheraf.models.indexation.BaseAutoModel` are regular models which 'table' parameter automatically takes the lowercase class name.
    It should only be used with unit tests.

    >>> class MyWonderfulClass(sheraf.AutoModel):
    ...    pass
    ...
    >>> assert MyWonderfulClass.table == "mywonderfulclass"
    >>> with sheraf.connection():
    ...     m = MyWonderfulClass.create()
    ...     assert m.table == "mywonderfulclass"
    """

    @property
    def table(self):
        return self.__class__.__name__.lower()

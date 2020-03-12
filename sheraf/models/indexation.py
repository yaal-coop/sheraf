import itertools
import warnings

import sheraf.exceptions
from sheraf.models.base import BaseModel, BaseModelMetaclass


class BaseIndexedModel(BaseModel):
    """
    This class handles the whole indexation mechanism. The mechanisms
    for reading or iterating over models in the database are handled
    here.
    """

    index_root_default = sheraf.types.SmallDict

    @classmethod
    def primary_key(cls):
        return "id"

    @classmethod
    def all(cls):
        """
        :return: A :class:`~sheraf.queryset.QuerySet` containing all the
            registered models.
        """
        return sheraf.queryset.QuerySet(model_class=cls)

    @classmethod
    def create(cls, *args, **kwargs):
        if hasattr(cls, "make_id"):
            args = list(args)
            identifier = args.pop() if args else kwargs.get(cls.primary_key())
            model = super().create(*args, **kwargs)

            warnings.warn(
                "BaseIndexedModel.make_id is deprecated and wont be supported with sheraf 0.2. "
                "Please use your id attribute 'default' parameter instead.",
                DeprecationWarning,
                stacklevel=3,
            )
            identifier = identifier or model.make_id()
            cls.index_setitem(identifier, model.mapping)
            model.identifier = identifier
        else:
            model = super().create(*args, **kwargs)
            cls.index_setitem(model.identifier, model.mapping)

        return model

    @classmethod
    def read(cls, *args, **kwargs):
        """
        Get a model instance from its identifier. If the model identifier is not valid, a
        :class:`~sheraf.exceptions.ModelObjectNotFoundException` is raised.

        :param *args*: The ``identifier`` of the model. There can be only one positionnal or
                      keyword argument.
        :param *kwargs*: The ``identifier`` of the model. There can be only one positionnal or
                        keyword argument.
        :return: The :class:`~sheraf.models.indexation.BaseIndexedModel` matching the id.

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

        if len(args) + len(kwargs) != 1:
            raise TypeError(
                "BaseIndexedModel.read takes only one positionnal or named parameter"
            )

        args = list(args)
        identifier = args.pop() if args else kwargs.get(cls.primary_key())

        try:
            mapping = cls.index_getitem(identifier)
            model = cls._decorate(mapping)
            return model
        except (KeyError, TypeError):
            raise sheraf.exceptions.ModelObjectNotFoundException(cls, identifier)

    @classmethod
    def read_these(cls, *args, **kwargs):
        """
        Get model instances from their identifiers. If an instance identifiers does not
        exist, a :class:`~sheraf.exceptions.ModelObjectNotFoundException` is
        raised.

        The function takes only one parameter which key is the index where to
        search, and which values are the index identifier.
        By default the index used is the `id` index.

        :return: A generator over the models matching the keys.

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
        sheraf.exceptions.ModelObjectNotFoundException: Id 'invalid' not found in MyModel, 'id' index
        """

        if len(args) + len(kwargs) != 1:
            raise TypeError(
                "BaseIndexedModel.read_these takes only one positionnal or named parameter"
            )

        identifiers = args[0] if args else kwargs.get(cls.primary_key())

        return (cls.read(identifier) for identifier in identifiers)

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
        identifier = (
            self.identifier
            if self.mapping is not None and self.primary_key() in self.mapping
            else None
        )
        return "<{} {}={}>".format(
            self.__class__.__name__, self.primary_key(), identifier
        )

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return (
            hasattr(self, self.primary_key())
            and hasattr(other, self.primary_key())
            and self.identifier == other.identifier
        )

    @property
    def identifier(self):
        """
        The identifier is the value of the primary_key for the current instance.
        If the primary_key is 'id', then the identifier might be an UUID.
        """
        return getattr(self, self.primary_key())

    def copy(self, **kwargs):
        """
        Copies a model.

        :param \*\*kwargs: Keywords arguments will be passed to
                         :func:`~sheraf.models.BaseModel.create` and thus
                         wont be copied.

        :return: a copy of this instance.
        """

        copy = super().copy(**kwargs)
        if hasattr(self, "make_id"):
            warnings.warn(
                "BaseIndexedModel.make_id is deprecated and wont be supported with sheraf 0.2. "
                "Please use your id attribute 'default' parameter instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            setattr(copy, self.primary_key(), copy.make_id())
        else:
            if self.primary_key():
                self.reset(self.primary_key())

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
        self.index_delete(self.identifier)


class IndexedModelMetaclass(BaseModelMetaclass):
    """
    Contains the mapping of tables (name of models) to their
    corresponding model definitions
    """

    tables = {}

    def __new__(cls, name, bases, attrs):
        klass = super().__new__(cls, name, bases, attrs)

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


class IndexedModel(BaseIndexedModel, metaclass=IndexedModelMetaclass):
    """
    Top-level indexed models.

    Those models are stored at the root of the database. They must
    have a **table** parameter defined and an **id** attribute.

    They can have a **database_name** attribute. If it is set, then in a
    default connection context:

    - :func:`~sheraf.models.indexation.IndexedModel.create` will store the\
    new model instances in this database;
    - :func:`~sheraf.models.indexation.IndexedModel.read` and\
    :func:`~sheraf.models.indexation.IndexedModel.all` (etc.) will read in\
    priority in this database, and then in the default database.
    - :func:`~sheraf.models.indexation.IndexedModel.delete` will try to delete\
    the model from this database, and by default in the default database.

    However, if a **database_name** is explicitly passed to
    :func:`sheraf.databases.connection`, then every action will be
    performed on this database, ignoring the model **database_name** attribute.
    """

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
    def index_table(cls, database_name=None, setdefault=True):
        index_root = cls.index_root(database_name, setdefault)

        try:
            return index_root[cls.primary_key()]
        except KeyError:
            if not setdefault:
                raise

        return index_root.setdefault(cls.primary_key(), cls.index_table_default())

    @classmethod
    def index_table_default(cls):
        return sheraf.types.LargeDict()

    @classmethod
    def _index_tables(cls, database_name=None):
        tables = []
        for db_name in (database_name, cls.database_name, cls._current_database_name()):
            if not db_name:
                continue

            try:
                tables.append(cls.index_table(db_name, False))
            except KeyError:
                continue

        return tables

    @classmethod
    def index_contains(cls, key):
        return any(key in table for table in cls._index_tables())

    @classmethod
    def index_getitem(cls, key):
        if cls.database_name:
            try:
                return cls.index_table(cls.database_name)[key]
            except KeyError:
                pass
        return cls.index_table(cls._current_database_name())[key]

    @classmethod
    def index_setitem(cls, key, value):
        cls.index_table()[key] = value

    @classmethod
    def index_iterkeys(cls, reverse=False):
        return itertools.chain.from_iterable(
            cls._table_iterkeys(table, reverse=reverse) for table in cls._index_tables()
        )

    @classmethod
    def index_delete(cls, key):
        if cls.database_name:
            try:
                del cls.index_table(cls.database_name)[key]
                return
            except KeyError:
                pass
        del cls.index_table(sheraf.Database.current_name())[key]

    @classmethod
    def index_root(cls, database_name=None, setdefault=True):
        database_name = (
            database_name or cls.database_name or cls._current_database_name()
        )
        root = sheraf.Database.current_connection(database_name).root()

        try:
            return root[cls.table]
        except KeyError:
            if not setdefault:
                raise
            return root.setdefault(cls.table, sheraf.types.SmallDict())

    @classmethod
    def create(cls, *args, **kwargs):
        if cls.primary_key() not in cls.attributes:
            raise sheraf.exceptions.SherafException(
                "{} inherit from IndexedModel but has no id attribute. Cannot create.".format(
                    cls.__name__
                )
            )

        return super().create(*args, **kwargs)

    @classmethod
    def count(cls):
        """
        :return: the number of instances.

        Using this method is faster than using ``len(MyModel.all())``.
        """
        return sum(len(table) for table in cls._index_tables())

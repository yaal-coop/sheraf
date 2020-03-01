import itertools
import warnings

import sheraf.exceptions
from sheraf.models.base import BaseModel, BaseModelMetaclass


class BaseIndexedModelMetaclass(BaseModelMetaclass):
    @property
    def primary_key(cls):
        if cls._primary_key is None:
            for index_name, index in cls.indexes().items():
                if not index.primary:
                    continue

                if cls._primary_key is None:
                    cls._primary_key = index_name

                else:
                    raise sheraf.exceptions.PrimaryKeyException(
                        "A model can have only one primary key. {} has {} and {}".format(
                            cls.__class__.name, cls._primary_key, index_name,
                        )
                    )

        return cls._primary_key


class BaseIndexedModel(BaseModel, metaclass=BaseIndexedModelMetaclass):
    """
    This class handles the whole indexation mechanism. The mechanisms
    for reading or iterating over models in the database are handled
    here.
    """

    index_root_default = sheraf.types.SmallDict
    # TODO: Is LargeList the right the right collection here?
    index_multiple_default = sheraf.types.LargeList

    _indexes = None
    _primary_key = None

    @classmethod
    def indexes(cls):
        if cls._indexes is None:
            cls._indexes = {}
            for attribute_name, attribute in cls.attributes.items():
                for index_key, index in attribute.indexes.items():
                    index.key = index_key or attribute.key(cls)
                    cls._indexes[index.key] = index

        return cls._indexes

    @classmethod
    def all(cls):
        """
        :return: A :class:`~sheraf.queryset.QuerySet` containing all the
            registered models.
        """
        return sheraf.queryset.QuerySet(model_class=cls)

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

        if args:
            index_name = cls.primary_key
            keys = args[0]

        else:
            index_name, keys = list(kwargs.items())[0]

        try:
            index = cls.indexes()[index_name]
        except KeyError:
            raise sheraf.exceptions.InvalidIndexException(
                "{} is not a valid index".format(index_name)
            )

        if index.unique:
            return (cls._read_unique_index(key, index_name) for key in keys)

        else:
            return itertools.chain.from_iterable(
                cls._read_multiple_index(key, index_name) for key in keys
            )

    @classmethod
    def create(cls, *args, **kwargs):
        """
        :return: an instance of this model
        """

        model = super().create(*args, **kwargs)
        first_instance = not cls.index_root_initialized()
        for index in model.indexes().values():
            if first_instance or cls.index_table_initialized(index.key):
                model.index_set(index)
            else:
                warnings.warn(
                    "New index in an already populated table. %s.%s will not be indexed. "
                    'Consider calling %s.index_table_rebuild(["%s"]) to initialize the indexation table.'
                    % (cls.__name__, index.key, cls.__name__, index.key,),
                    sheraf.exceptions.IndexationWarning,
                    stacklevel=2,
                )

        return model

    @classmethod
    def read(cls, *args, **kwargs):
        """
        Get a model instance from its identifier. If the model identifier is not valid, a
        :class:`~sheraf.exceptions.ModelObjectNotFoundException` is raised.

        The function takes only one parameter which key is the index where to
        search, and which value is the index identifier. If the index is
        multiple, a :class:`~sheraf.exceptions.MultipleIndexException` is
        raised.
        By default the index used is the `id` index.

        :param *args*: The ``identifier`` of the model. There can be only one positionnal or
                      keyword argument.
        :param *kwargs*: The ``identifier`` of the model. There can be only one positionnal or
                        keyword argument.
        :return: The :class:`~sheraf.models.indexation.BaseIndexedModel` matching the id.

        >>> class MyModel(sheraf.Model):
        ...     table = "my_model"
        ...     unique = sheraf.SimpleAttribute().index(unique=True)
        ...     multiple = sheraf.SimpleAttribute().index()
        ...
        >>> with sheraf.connection():
        ...     m = MyModel.create(unique="A", multiple="B")
        ...     assert MyModel.read(m.id) == m
        ...     assert MyModel.read(unique="A") == m
        ...
        >>> with sheraf.connection():
        ...     MyModel.read("invalid")
        Traceback (most recent call last):
            ...
        ModelObjectNotFoundException
        >>> with sheraf.connection():
        ...     MyModel.read(multiple="B")
        Traceback (most recent call last):
            ...
        MultipleIndexException
        """

        if len(args) + len(kwargs) != 1:
            raise TypeError(
                "BaseIndexedModel.read takes only one positionnal or named parameter"
            )

        if args:
            index_name = cls.primary_key
            key = args[0]

        else:
            index_name, key = list(kwargs.items())[0]

        try:
            index = cls.indexes()[index_name]
        except KeyError:
            raise sheraf.exceptions.InvalidIndexException(
                "{} is not a valid index".format(index_name)
            )

        if index.unique:
            return cls._read_unique_index(key, index_name)

        else:
            raise sheraf.exceptions.MultipleIndexException(
                "{} is a multiple index and cannot be used with 'read'".format(
                    index_name
                )
            )

    @classmethod
    def _read_unique_index(cls, key, index_name=None):
        try:
            mapping = cls.index_getitem(key, index_name)
            model = cls._decorate(mapping)
            return model

        except (KeyError, sheraf.exceptions.ModelObjectNotFoundException):
            raise sheraf.exceptions.ModelObjectNotFoundException(cls, key, index_name)

    @classmethod
    def _read_multiple_index(cls, key, index_name=None):
        try:
            mappings = cls.index_getitem(key, index_name)
            return (cls._decorate(mapping) for mapping in mappings)
        except (KeyError, sheraf.exceptions.ModelObjectNotFoundException):
            raise sheraf.exceptions.ModelObjectNotFoundException(cls, key, index_name)

    @classmethod
    def index_table_rebuild(cls, index_names=None):
        """
        Resets a model indexation tables.

        This method should be called if an attribute became indexed in an already
        populated database.

        :param index_names: A list of index names to reset. If `None`, all the
                            indexes will be reseted. The primary index cannot be
                            resetted.
        """
        if not index_names:
            indexes = cls.indexes().values()
        else:
            indexes = [
                index
                for index_name, index in cls.indexes().items()
                if index_name in index_names
            ]

        for index in indexes:
            if index.primary:
                continue

            try:
                cls.index_root_del(index)
            except KeyError:
                pass

        for m in cls.all():
            for index in indexes:
                if not index.primary:
                    m.index_set(index)

    @classmethod
    def filter(cls, predicate=None, **kwargs):
        """Shortcut for :func:`sheraf.queryset.QuerySet.filter`.

        :return: :class:`sheraf.queryset.QuerySet`
        """
        return sheraf.queryset.QuerySet(model_class=cls).filter(
            predicate=predicate, **kwargs
        )

    @classmethod
    def filter_raw(cls, *args, **kwargs):
        """
        Shortcut for :func:`sheraf.queryset.QuerySet.filter_raw`.

        :return: :class:`sheraf.queryset.QuerySet`
        """
        return sheraf.queryset.QuerySet(model_class=cls).filter_raw(*args, **kwargs)

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
            if self._persistent is not None and self.primary_key in self._persistent
            else None
        )
        return "<{} {}={}>".format(
            self.__class__.__name__, self.primary_key, identifier
        )

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return (
            hasattr(self, self.primary_key)
            and hasattr(other, self.primary_key)
            and self.identifier == other.identifier
        )

    def __setattr__(self, name, value):
        attribute = self.attributes.get(name)
        if attribute:
            is_first_instance = self.count() <= 1
            is_created = (
                self._persistent is not None and self.primary_key in self._persistent
            )

            for index in attribute.indexes.values():
                index_table_exists = self.index_table_initialized(index.key)
                is_indexable = is_first_instance or index_table_exists
                index.should_index_set = (
                    is_created and is_indexable and not index.primary
                )

                if not is_indexable:
                    warnings.warn(
                        "New index in an already populated table. %s.%s will not be indexed. "
                        'Consider calling %s.index_table_rebuild(["%s"]) to initialize the indexation table.'
                        % (
                            self.__class__.__name__,
                            name,
                            self.__class__.__name__,
                            name,
                        ),
                        sheraf.exceptions.IndexationWarning,
                        stacklevel=4,
                    )

                if not index.should_index_set:
                    continue

                old_values = index.values_func(index.attribute.read(self))
                new_values = index.values_func(value)
                del_values = old_values - new_values
                add_values = new_values - old_values

                self.index_del(index, del_values)
                self.index_set(index, add_values)

        super().__setattr__(name, value)

    @property
    def primary_key(self):
        """
        The primary key is the primary index of the model. It is generally 'id'.
        """
        return self.__class__.primary_key

    def index_del(self, index, keys=None):
        """
        Delete model instances from a given index.

        :param index: The index where the instances should be removed.
        :param keys: The keys to remove from the index. If :class:`None`, all
                     the current values of the index for the current model
                     are removed.
        """
        if not keys:
            keys = index.values_func(index.attribute.read(self))

        index_table = self.index_table(index_name=index.key)

        for key in keys:
            if key not in index_table:
                continue

            if index.unique:
                self._index_table_del_unique(index_table, key, self._persistent)
            else:
                self._index_table_del_multiple(index_table, key, self._persistent)

    def _index_table_del_unique(self, index_table, key, value):
        del index_table[key]

    def _index_table_del_multiple(self, index_table, key, value):
        index_table[key].remove(value)
        if len(index_table[key]) == 0:
            del index_table[key]

    def index_set(self, index, keys=None):
        """
        Sets model instances from a given index .

        :param index: The index where the instances should be set.
        :param keys: The keys to set in the index. If :class:`None`, all
                     the current values of the index for the current model
                     are set.
        """
        if not keys:
            keys = index.values_func(index.attribute.read(self))

        index_table = self.index_table(index_name=index.key)

        for key in keys:
            if index.unique:
                self._index_table_set_unique(index_table, key, self._persistent)
            else:
                self._index_table_set_multiple(index_table, key, self._persistent)

    def _index_table_set_unique(self, index_table, key, value):
        if key in index_table:
            raise sheraf.exceptions.UniqueIndexException
        index_table[key] = value

    def _index_table_set_multiple(self, index_table, key, value):
        index_list = index_table.setdefault(key, self.index_multiple_default())
        index_list.append(value)

    @property
    def identifier(self):
        """
        The identifier is the value of the primary_key for the current instance.
        If the primary_key is 'id', then the identifier might be an UUID.
        """
        return getattr(self, self.primary_key)

    @identifier.setter
    def identifier(self, value):
        return setattr(self, self.primary_key, value)

    def copy(self):
        copy = super().copy()
        if copy.primary_key:
            copy.reset(copy.primary_key)
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
        for index in self.indexes().values():
            self.index_del(index)

        for attr in self.attributes.values():
            attr.delete(self)

        # TODO: this should be done in 'index_del'
        try:
            self.index_delete(self.identifier)
        except KeyError:
            pass


class IndexedModelMetaclass(BaseIndexedModelMetaclass):
    """Internal class.

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
    id = sheraf.attributes.simples.SimpleAttribute().index(primary=True)

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
    def index_table(cls, database_name=None, index_name=None, setdefault=True):
        if index_name in (None, cls.primary_key):
            mapping = cls.index_table_default
            index_name = cls.primary_key
        else:
            mapping = cls.indexes()[index_name].mapping

        index_root = cls.index_root(database_name, setdefault)

        try:
            return index_root[index_name]
        except KeyError:
            if not setdefault:
                raise

        return index_root.setdefault(index_name, mapping())

    @classmethod
    def index_table_default(cls):
        return sheraf.types.LargeDict()

    @classmethod
    def _index_tables(cls, index_name=None):
        tables = []
        for db_name in (cls.database_name, cls._current_database_name()):
            if not db_name:
                continue

            try:
                tables.append(cls.index_table(db_name, index_name, False))
            except KeyError:
                continue

        return tables

    @classmethod
    def index_contains(cls, key, index_name=None):
        return any(key in index_table for index_table in cls._index_tables(index_name))

    @classmethod
    def index_getitem(cls, key, index_name=None):
        last_exc = None
        for index_table in cls._index_tables(index_name):
            try:
                return index_table[key]
            except KeyError as exc:
                last_exc = exc

        if last_exc:
            raise last_exc

        raise KeyError

    @classmethod
    def index_setitem(cls, key, value, index_name=None):
        cls.index_table(index_name)[key] = value

    @classmethod
    def index_iterkeys(cls, reverse=False, index_name=None):
        return itertools.chain.from_iterable(
            cls._table_iterkeys(table, reverse)
            for table in cls._index_tables(index_name)
        )

    @classmethod
    def index_delete(cls, key, index_name=None):
        for index_table in cls._index_tables():
            try:
                del index_table[key]
            except KeyError:
                pass

    @classmethod
    def database_root(cls, database_name=None):
        database_name = (
            database_name or cls.database_name or cls._current_database_name()
        )
        return sheraf.Database.current_connection(database_name).root()

    @classmethod
    def index_root(cls, database_name=None, setdefault=True):
        root = cls.database_root(database_name)
        try:
            return root[cls.table]
        except KeyError:
            if not setdefault:
                raise
            return root.setdefault(cls.table, sheraf.types.SmallDict())

    @classmethod
    def index_root_del(cls, index_name, database_name=None):
        del cls.index_root(database_name)[index_name]

    @classmethod
    def index_root_initialized(cls, database_name=None):
        for db_name in (database_name, cls.database_name, cls._current_database_name()):
            if not db_name:
                continue

            if cls.table in cls.database_root(db_name):
                return True

        return False

    @classmethod
    def index_table_initialized(cls, index_name, database_name=None):
        for db_name in (database_name, cls.database_name, cls._current_database_name()):
            if not db_name:
                continue

            try:
                if cls.index_root(db_name, False) and index_name in cls.index_root(
                    db_name, False
                ):
                    return True
            except KeyError:
                pass

        return False

    @classmethod
    def create(cls, *args, **kwargs):
        if cls.primary_key not in cls.attributes:
            raise sheraf.exceptions.SherafException(
                "{} inherit from IndexedModel but has no id attribute. Cannot create.".format(
                    cls.__name__
                )
            )

        return super().create(*args, **kwargs)

    @classmethod
    def count(cls, index_name=None):
        """
        :return: the number of instances.

        Using this method is faster than using ``len(MyModel.all())``.
        """
        return sum(len(table) for table in cls._index_tables(index_name))

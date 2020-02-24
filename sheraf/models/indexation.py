import itertools
import random
import sys
import uuid

import BTrees

import sheraf.exceptions
from sheraf.models.base import BaseModel, BaseModelMetaclass
import warnings


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
    """
    This class handles the whole indexation mechanism.

    By default, indexed models come with a `id` index which keys are unique.
    Further indexes can be created using the attributes
    :func:`~sheraf.attributes.base.BaseAttribute.index` method.
    """

    database_name = None
    _indexes = None
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
    def _table(cls, database_name=None, index_name=None):
        # indexed_attribute_name
        database_name = (
            database_name or cls.database_name or cls._current_database_name()
        )
        root = sheraf.Database.current_connection(database_name).root()

        if index_name in (None, "id"):
            mapping = cls._table_default
            index_name = "id"
        else:
            mapping = cls._indexes[index_name].mapping

        try:
            index_root = root[cls.table]
        except KeyError:
            index_root = root.setdefault(cls.table, sheraf.types.SmallDict())

        try:
            return index_root[index_name]
        except KeyError:
            return index_root.setdefault(index_name, mapping())

    @classmethod
    def _table_default(cls):
        return sheraf.types.LargeDict()

    @classmethod
    def _tables(cls, index_name=None):
        return (
            cls._table(db_name, index_name)
            for db_name in (cls.database_name, cls._current_database_name())
            if db_name
        )

    @classmethod
    def _tables_contains(cls, model_id, index_name=None):
        return any(model_id in table for table in cls._tables(index_name))

    @classmethod
    def _tables_getitem(cls, key, index_name=None):
        if cls.database_name:
            try:
                return cls._table(cls.database_name, index_name)[key]
            except KeyError:
                pass
        return cls._table(cls._current_database_name(), index_name)[key]

    @classmethod
    def _tables_iterkeys(cls, reverse=False, index_name=None):
        return itertools.chain.from_iterable(
            cls._table_iterkeys(table, reverse) for table in cls._tables(index_name)
        )

    @classmethod
    def _tables_del(cls, key, index_name=None):
        if cls.database_name:
            try:
                del cls._table(cls.database_name, index_name)[key]
                return
            except KeyError:
                pass
        del cls._table(sheraf.Database.current_name(), index_name)[key]

    @classmethod
    def _delete_index_table(cls, index_name):
        database_name = cls.database_name or cls._current_database_name()
        root = sheraf.Database.current_connection(database_name).root()
        index_root = root[cls.table]

        del index_root[index_name]

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
    def read_these(cls, id=None, **kwargs):
        """
        Read models from a collection of keys.
        If an instance id does not exist, a
        :class:`~sheraf.exceptions.ModelObjectNotFoundException` is raised.

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

        if len(kwargs) > 1:
            raise TypeError(
                "IndexedModel.read takes exactly one argument ({} given)".format(
                    len(kwargs)
                )
            )

        if not kwargs:
            kwargs["id"] = id

        index_name, keys = list(kwargs.items())[0]

        if index_name == "id" or (
            index_name in cls.indexes() and cls.indexes()[index_name].unique
        ):
            return (cls._read_unique_index(key, index_name) for key in keys)

        elif index_name in cls.indexes():
            return itertools.chain.from_iterable(
                cls._read_multiple_index(key, index_name) for key in keys
            )

        else:
            raise sheraf.exceptions.InvalidIndexException(
                "{} is not a valid index".format(index_name)
            )

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

        root = sheraf.Database.current_connection(cls._current_database_name()).root()
        index_tables = root.get(cls.table)
        for index in model.indexes().values():
            if len(table) == 0 or (index_tables and index.key in index_tables):
                model.update_index(index)
            else:
                warnings.warn(
                    "New index in an already populated table. %s.%s will not be indexed. "
                    'Consider calling %s.reset_indexes(["%s"]) to initialize the indexation table.'
                    % (cls.__name__, index.key, cls.__name__, index.key,),
                    sheraf.exceptions.IndexationWarning,
                    stacklevel=2,
                )

        table[id] = model._persistent
        model.id = id
        return model

    @classmethod
    def read(cls, id=None, **kwargs):
        """Read models in an index.
        The function takes only one parameter which key is the index where to
        search, and which value is the index identifier. If the index is
        multiple, a :class:`~sheraf.exceptions.MultipleIndexException` is
        raised.
        By default the index used is the `id` index.

        :return: The model matching the key.

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

        if len(kwargs) > 1:
            raise TypeError(
                "IndexedModel.read takes exactly one argument ({} given)".format(
                    len(kwargs)
                )
            )

        if not kwargs:
            kwargs["id"] = id

        index_name, key = list(kwargs.items())[0]

        if index_name == "id" or (
            index_name in cls.indexes() and cls.indexes()[index_name].unique
        ):
            return cls._read_unique_index(key, index_name)

        elif index_name in cls.indexes():
            raise sheraf.exceptions.MultipleIndexException(
                "{} is a multiple index and cannot be used with 'read'".format(
                    index_name
                )
            )

        else:
            raise sheraf.exceptions.InvalidIndexException(
                "{} is not a valid index".format(index_name)
            )

    @classmethod
    def _read_unique_index(cls, key, index_name=None):
        try:
            mapping = cls._tables_getitem(key, index_name)
            model = cls._decorate(mapping)

            # TODO: Remove this when all the ideas will be in the persistent
            if index_name == "id" and "id" not in model._persistent:
                model.id = key
                model.fresh_id = True
            else:
                model.fresh_id = False

            return model

        except (KeyError, sheraf.exceptions.ModelObjectNotFoundException):
            raise sheraf.exceptions.ModelObjectNotFoundException(cls, key, index_name)

    @classmethod
    def _read_multiple_index(cls, key, index_name=None):
        try:
            mappings = cls._tables_getitem(key, index_name)
            return (cls._decorate(mapping) for mapping in mappings)
        except (KeyError, sheraf.exceptions.ModelObjectNotFoundException):
            raise sheraf.exceptions.ModelObjectNotFoundException(cls, key, index_name)

    @classmethod
    def reset_indexes(cls, index_names=None):
        """
        Resets a model indexation tables.

        This method should be called if an attribute became indexed in an already
        populated database.

        :param index_names: A list of index names to reset. If `None`, all the
                            indexes will be reseted.
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
            try:
                cls._delete_index_table(index)
            except KeyError:
                pass

        for m in cls.all():
            for index in indexes:
                m.update_index(index)

    @classmethod
    def count(cls, index_name=None):
        """
        :return: the number of instances.

        Using this method is faster than using ``len(MyModel.all())``.
        """
        return sum(len(table) for table in cls._tables(index_name))

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

    @classmethod
    def indexes(cls):
        if cls._indexes is None:
            cls._indexes = {}
            for attribute_name, attribute in cls.attributes.items():
                for index_key, index in attribute.indexes.items():
                    index.key = index_key or attribute.key(cls)
                    cls._indexes[index.key] = index

        return cls._indexes

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

    def _find_index(self, name):
        index = self.indexes().get(name)
        if index:
            return index

        attr = self.attributes.get(name)
        if attr:
            for index in attr.indexes.values():
                return index

    def __setattr__(self, name, value):
        root = sheraf.Database.current_connection(self.database_name).root()
        index = self._find_index(name)
        table = root.get(self.table, {})
        is_created = self._persistent is not None and "id" in self._persistent
        is_indexable = len(table.get("id", [])) <= 1 or (index and index.key in table)
        is_indexed = index and is_indexable
        if index and not is_indexable:
            warnings.warn(
                "New index in an already populated table. %s.%s will not be indexed. "
                'Consider calling %s.reset_indexes(["%s"]) to initialize the indexation table.'
                % (self.__class__.__name__, name, self.__class__.__name__, name,),
                sheraf.exceptions.IndexationWarning,
                stacklevel=4,
            )

        if is_created and is_indexed:
            self.delete_index(index)

        super(IndexedModel, self).__setattr__(name, value)

        if is_created and is_indexed:
            self.update_index(index)

    def delete_index(self, index):
        """
        Delete a model instance for a given index.
        """
        index_table = self._table(index_name=index.key)
        for value in index.get_values(self):
            # Suggestion: test a faire plus tot. Car si cette cond. est verifiee alors
            # c'est qu'on n'a pas fait d'indexation pour cause de compatibilite
            if value not in index_table:
                continue

            if index.unique:
                del index_table[value]
            else:
                index_table[value].remove(self._persistent)
                if len(index_table[value]) == 0:
                    del index_table[value]

    def update_index(self, index):
        """
        Creates or updates the model instance for a given index.
        """

        index_table = self._table(index_name=index.key)

        # TODO: Handle multiple indexes
        for value in index.get_values(self):
            if not index.unique:
                # TODO: Is LargeList the right the right collection here?
                index_list = index_table.setdefault(value, sheraf.types.LargeList())
                index_list.append(self._persistent)
            else:
                if value in index_table:
                    raise sheraf.exceptions.UniqueIndexException
                index_table[value] = self._persistent

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
        for index in self.indexes().values():
            self.delete_index(index)

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

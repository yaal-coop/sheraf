from BTrees.OOBTree import OOBTree
from sheraf.attributes.indexdetails import IndexDetails


READ_MEMOIZATION = False
WRITE_MEMOIZATION = True


def set_read_memoization(should_memoize_read):
    global READ_MEMOIZATION
    READ_MEMOIZATION = should_memoize_read


def set_write_memoization(should_memoize_write):
    global WRITE_MEMOIZATION
    WRITE_MEMOIZATION = should_memoize_write


class BaseAttribute(object):
    """
    Base type of all attributes of a base model.

    :param default: The value this attribute will be initialized with. If it is a callable object,
                    it will be called on initialization, else it will simply be copied. The callable
                    object can take either no argument, or one argument that will be the parent model.
    :type default: a callable object or a simple object
    :param key: The key to identify the attribute in its parent persistent mapping.
    :param lazy: If True, the objet carried by the attribute is created on the first
                          read or write access. If False, it is created when the model object
                          is created. Default is True.
    :type lazy: :class:`bool`
    :param read_memoization: Whether this attribute should be memoized on read. ``False`` by default.
    :type read_memoization: :class:`bool`
    :param write_memoization: Whether this attribute should be memoized on write. ``True`` by default.
    :type write_memoization: :class:`bool`

    When an attribute is memoized, its next reading will not result in a new database access.
    Attributes:
    - indexes:    a dictionary of Indexes. The key with value None stands for this attribute's name.
    """

    default_index_mapping = OOBTree

    def __init__(
        self,
        default=None,
        key=None,
        lazy=True,
        read_memoization=None,
        write_memoization=None,
        store_default_value=True,
    ):
        self._default_value = default
        self._default_key = None
        self._key = key
        self.read_memoization = (
            READ_MEMOIZATION if read_memoization is None else read_memoization
        )
        self.write_memoization = (
            WRITE_MEMOIZATION if write_memoization is None else write_memoization
        )
        self.lazy = lazy
        self.store_default_value = store_default_value
        self.indexes = {}

    def set_default_key(self, key):
        self._default_key = key

    def create(self, parent):
        """
        :return: The attribute's defined default value. If it is a callable, return
                 the result of calling it instead.
        """
        if not callable(self._default_value):
            return self._default_value

        try:
            return self._default_value()
        except TypeError:
            return self._default_value(parent)

    def is_created(self, parent):
        """
        :param parent: The owner of this attribute
        :return: true if the object is effectively created"""
        return self.key(parent) in parent.mapping

    def key(self, parent):
        """:return: the key that identifies this attribute in its owner object"""
        if self._key is None:
            return self._default_key

        if isinstance(self._key, (list, tuple)):
            for key in self._key:
                if key in parent.mapping:
                    return key
            return self._key[0]

        return self._key

    def read_raw(self, parent):
        # Internal.
        # :param parent: The owner of this attribute
        # :return: the raw representation of this attribute (ie as stored in ZODB)
        try:
            return parent.mapping[self.key(parent)]
        except KeyError:
            default_value = self.serialize(self.create(parent))
            if self.store_default_value:
                parent.mapping[self.key(parent)] = default_value
            return default_value

    def write_raw(self, parent, value):
        # Internal.
        # :param parent: The owner of this attribute
        # :param value: The value assigned to this attribute
        # assigns the value parameter to this attribute
        parent.mapping[self.key(parent)] = value
        return value

    def serialize(self, value):
        """Get data and transform it into something ZODB can store.

        :param value: The input data.
        :return: The transformed data.
        """
        return value

    def deserialize(self, value):
        """Get raw data and transform it into something more convenient to use.

        :param value: The input data.
        :return: The transformed data.
        """
        return value

    def read(self, parent):
        """Reads some raw data from the parent model and transform it into
        something more convenient to use. Most of the time, you should use
        :func:`~sheraf.attributes.base.BaseAttribute.deserialize`.

        :param parent: The model parent.
        :return: the transformed value of this attribute
        """
        return self.deserialize(self.read_raw(parent))

    def write(self, parent, value):
        """Takes user data, transform it into something ZODB can store, and
        store it into the model parent persistent.

        :param parent: The owner object of this attribute
        :param value: The user data to store.
        :return: The stored and reread data. In some cases it may be different that the input data.
        """
        written_value = self.write_raw(parent, self.serialize(value))
        return self.deserialize(written_value)

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        """Updates the value of the attribute.

        :param old_value: The previous value the attribute had.
        :param new_value: The new value that the attribute should be updated with.
        :param addition: On collections, adds elements to the attribute if they are present in `new_value` and not in `old_value`, defaults to `True`.
        :param edition: On collections, edits the attribute element if present on both `old_value` and `new_value`, defaults to `True`.
        :param deletion: On collections, removes an element if present in `old_value` and absent from `new_value`, default to `False`.
        :param replacement: Replace sub-collections or sub-models instead of editing them in-place, defaults to `False`.
        """
        return new_value if edition else old_value

    def delattr(self, parent):
        # Internal. delete attribute from its owner
        # TODO: We should remove this try/except
        try:
            del parent.mapping[self.key(parent)]
        except KeyError:
            pass

    def save(self, parent):
        pass

    def delete(self, parent):
        pass

    def index(
        self,
        unique=False,
        key=None,
        values=None,
        search=None,
        mapping=None,
        primary=False,
    ):
        """
        Indexing an attribute allows very fast reading with :func:`~sheraf.queryset.QuerySet.filter` calls.

        :param unique: If the attribute is unique, and two models have the same value for this
                      attribute, a :class:`~sheraf.exceptions.UniqueIndexException` is raised
                      when trying to write the second one. Automatically set to :class:`True` if
                      *primary* is :class:`True`.
        :param key: The key the index will use. By default, just the attribute name is used.
        :param values: A callable that takes the current attribute value and returns a collection of values to index. Each generated value will be indexed each time this attribute is edited. It may take time if the generated collection is large. By default, the current attribute raw value is used.
        :param primary: If true, this will be the default index for the model. `False` by default.

        When indexes are used, **lazy** is disabled.

        >>> class People(sheraf.Model):
        ...     table = "index_people"
        ...
        ...     # Simple indexing
        ...     name = sheraf.SimpleAttribute().index()
        ...
        ...     # Emails can only be owned once
        ...     email = sheraf.SimpleAttribute().index(unique=True)
        ...
        ...     # Indexing people by their decade
        ...     age = sheraf.SimpleAttribute().index(key="decade", values=lambda age: {age // 10})
        ...
        >>> with sheraf.connection(commit=True):
        ...     m = People.create(name="George Abitbol", email="george@abitbol.com", age=55)
        ...
        >>> with sheraf.connection():
        ...     assert [m] == People.filter(name="George Abitbol")
        ...     assert [m] == People.filter(decade=5)
        ...
        >>> with sheraf.connection():
        ...     People.create(name="Peter", email="george@abitbol.com", age=35)
        Traceback (most recent call last):
            ...
        UniqueIndexException
        """
        self.indexes[key] = IndexDetails(
            self,
            unique,
            key,
            values,
            search,
            mapping or self.default_index_mapping,
            primary,
        )
        self.lazy = False

        return self

    def values(self, value):
        """
        The default transformation that will be applied when storing data if this attribute is indexed
        but the :func:`~sheraf.attributes.base.BaseAttribute.index` `values_func` parameter is not provided.

        By default no transformation is applied, and the `value` parameter is returned in a :class:`set`.

        This method can be overload so a custom transformation is applied.
        """
        return {value}

    def search(self, value):
        """
        The default transformation that will be applied when searching for data if this attribute is indexed
        but the :func:`~sheraf.attributes.base.BaseAttribute.index` `search_func` parameter is not provided.

        By default this calls :meth:`~sheraf.attributes.base.BaseAttribute.values`.

        This method can be overload so a custom transformation is applied.
        """
        return self.values(value)

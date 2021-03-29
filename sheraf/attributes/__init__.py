import warnings
from BTrees.OOBTree import OOBTree
from sheraf.attributes.index import Index


def set_read_memoization(should_memoize_read):
    Attribute.read_memoization = should_memoize_read


def set_write_memoization(should_memoize_write):
    Attribute.write_memoization = should_memoize_write


class Attribute(object):
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
    nullok = True
    noneok = False
    read_memoization = False
    write_memoization = True

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
        self.attribute_name = None
        self._key = key

        if read_memoization is not None:
            self.read_memoization = read_memoization

        if write_memoization is not None:
            self.write_memoization = write_memoization

        self.lazy = lazy
        self.store_default_value = store_default_value
        self.indexes = {}

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.attribute_name}>"

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
        # the key that identifies this attribute in its owner object
        if self._key is None:
            return self.attribute_name

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
        # Get data and transform it into something ZODB can store.

        return value

    def deserialize(self, value):
        # Get raw data and transform it into something more convenient to use.

        return value

    def read(self, parent):
        # Reads some raw data from the parent model and transform it into
        # something more convenient to use. Most of the time, you should use
        # Attribute.deserialize

        return self.deserialize(self.read_raw(parent))

    def write(self, parent, value):
        # Takes user data, transform it into something ZODB can store, and
        # store it into the model parent persistent.

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

    def save(self, parent):
        pass

    def delete(self, parent):
        try:
            del parent.mapping[self.key(parent)]
        except KeyError:
            pass

    def index(
        self,
        unique=False,
        key=None,
        values=None,
        search=None,
        mapping=None,
        primary=False,
        nullok=None,
        noneok=None,
    ):
        """
        This method is a shortcut that inits a
        :class:`~sheraf.attributes.index.Index` object on the current attribute.
        It takes the same arguments as :class:`~sheraf.attributes.index.Index` except that by default:

        - the index name will be this attribute name;
        - the mapping parameter will be this attribute `default_index_mapping` parameter;
        - the values parameter will be this attribute :meth:`~sheraf.attributes.Attribute.values` method;
        - the search parameter will be this attribute :meth:`~sheraf.attributes.Attribute.search` method;
        - the noneok parameter will be this attribute `noneok` parameter
        - the nullok parameter will be this attribute `nullok` parameter
        """
        self.indexes[key] = Index(
            self,
            unique=unique,
            key=key,
            values=values or self.values,
            search=search or values or self.search or self.values,
            mapping=mapping or self.default_index_mapping,
            primary=primary,
            nullok=nullok if nullok is not None else self.nullok,
            noneok=noneok if noneok is not None else self.noneok,
        )
        self.lazy = False

        return self

    def values(self, value):
        """
        The default transformation that will be applied when storing data if this attribute is indexed
        but the :func:`~sheraf.attributes.Attribute.index` `values_func` parameter is not provided.

        By default no transformation is applied, and the `value` parameter is returned in a :class:`set`.

        This method can be overload so a custom transformation is applied.
        """
        return {self.serialize(value)}

    def search(self, value):
        """
        The default transformation that will be applied when searching for data if this attribute is indexed
        but the :func:`~sheraf.attributes.Attribute.index` `search_func` parameter is not provided.

        By default this calls :meth:`~sheraf.attributes.Attribute.values`.

        This method can be overload so a custom transformation is applied.
        """
        return self.values(value)


class BaseAttribute(Attribute):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "sheraf.BaseAttribute has been renamed sheraf.Attribute. The old name will be removed in sheraf 0.5.0",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

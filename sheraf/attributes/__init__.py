import warnings

from BTrees.OOBTree import OOBTree
from sheraf.attributes.index import Index


def set_read_memoization(should_memoize_read):
    Attribute.read_memoization = should_memoize_read


def set_write_memoization(should_memoize_write):
    Attribute.write_memoization = should_memoize_write


class Attribute:
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
        self.cb_creation = []
        self.cb_edition = []
        self.cb_deletion = []

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.attribute_name}>"

    @property
    def has_primary_index(self):
        return any(index.primary for index in self.indexes.values())

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
        # :return: the raw representation of this attribute
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
        # Get data and transform it into something that can be stored.

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
        # Takes user data, transform it into something that can be stored, and
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
        index_keys_func=None,
        search_keys_func=None,
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
        - the index_keys_func parameter will be this attribute :meth:`~sheraf.attributes.Attribute.index_keys` method;
        - the search_keys_func parameter will be this attribute :meth:`~sheraf.attributes.Attribute.search_keys` method;
        - the noneok parameter will be this attribute `noneok` parameter
        - the nullok parameter will be this attribute `nullok` parameter
        """
        if values and not index_keys_func:
            warnings.warn(
                "Attribute.index 'values' attribute is deprecated and will be removed in sheraf 0.6. "
                "Please use 'index_keys_func' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            index_keys_func = values

        if search and not search_keys_func:
            warnings.warn(
                "Attribute.index 'search' attribute is deprecated and will be removed in sheraf 0.6. "
                "Please use 'search_keys_func' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            search_keys_func = search

        if hasattr(self, "values") and not index_keys_func:
            warnings.warn(
                "Attribute 'values' method is deprecated and will be removed in sheraf 0.6. "
                "Please use 'index_keys' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            index_keys_func = self.values

        if hasattr(self, "search") and not search_keys_func:
            warnings.warn(
                "Attribute.index 'search' attribute is deprecated and will be removed in sheraf 0.6. "
                "Please use 'search_keys' instead",
                DeprecationWarning,
                stacklevel=2,
            )
            search_keys_func = self.search

        self.indexes[key] = Index(
            self,
            unique=unique,
            key=key,
            index_keys_func=index_keys_func or values or self.index_keys,
            search_keys_func=search_keys_func
            or search
            or index_keys_func
            or self.search_keys
            or self.index_keys,
            mapping=mapping or self.default_index_mapping,
            primary=primary,
            nullok=nullok if nullok is not None else self.nullok,
            noneok=noneok if noneok is not None else self.noneok,
        )
        self.lazy = False

        return self

    def index_keys(self, value):
        """
        The default transformation that will be applied when storing data if this attribute is indexed
        but the :func:`~sheraf.attributes.Attribute.index` `values_func` parameter is not provided.

        By default no transformation is applied, and the `value` parameter is returned in a :class:`set`.

        This method can be overload so a custom transformation is applied.
        """
        return {self.serialize(value)}

    def search_keys(self, value):
        """
        The default transformation that will be applied when searching for data if this attribute is indexed
        but the :func:`~sheraf.attributes.Attribute.index` `search_keys_func` parameter is not provided.

        By default this calls :meth:`~sheraf.attributes.Attribute.values`.

        This method can be overload so a custom transformation is applied.
        """
        return self.index_keys(value)

    def index_keys_func(self, *args, **kwargs):
        """
        Shortcut for :meth:`~sheraf.attributes.index.Index.index_keys_func` for
        the index that has the same name than this attribute.
        """
        return self.indexes[self.attribute_name].index_keys_func(*args, **kwargs)

    def search_keys_func(self, *args, **kwargs):
        """
        Shortcut for :meth:`~sheraf.attributes.index.Index.search_keys_func` for
        the index that has the same name than this attribute.
        """
        return self.indexes[self.attribute_name].search_keys_func(*args, **kwargs)

    def on_creation(self, *args, **kwargs):
        """
        Decorator for callbacks to call on an attribute creation. The callback
        will be executed before the attribute is created. If the callback yields,
        the part after the yield will be executed after the creation.

        The callback will be passed the new value of the attribute.

        The callback can be freely named.

        >>> class Cowboy(sheraf.Model):
        ...     table = "old_cowboys_creation"
        ...     age = sheraf.IntegerAttribute()
        ...
        ...     @age.on_creation
        ...     def create_age(self, new):
        ...         print("New cowboy aged of", new)
        ...
        >>> with sheraf.connection():
        ...     george = Cowboy.create(age=50)
        New cowboy aged of 50
        """

        def wrapper(func):
            self.cb_creation.append(func)
            return func

        return wrapper if not args else wrapper(args[0])

    def on_edition(self, *args, **kwargs):
        """
        Decorator for callbacks to call on an attribute edition. The callback
        will be executed before the attribute is edited. If the callback yields,
        the part after the yield will be executed after the update.

        The callback will be passed the old and the new value of the attribute.

        The callback can be freely named.

        >>> class Cowboy(sheraf.Model):
        ...     table = "old_cowboys_edition"
        ...     age = sheraf.IntegerAttribute()
        ...
        ...     @age.on_edition
        ...     def update_age(self, new, old):
        ...         print("I was", old, "years old")
        ...         yield
        ...         print("Now I am", new, "years old")
        ...
        >>> with sheraf.connection():
        ...     george = Cowboy.create(age=50)
        ...     george.age = 51
        I was 50 years old
        Now I am 51 years old
        """

        def wrapper(func):
            self.cb_edition.append(func)
            return func

        return wrapper if not args else wrapper(args[0])

    def on_deletion(self, *args, **kwargs):
        """
        Decorator for callbacks to call on an attribute deletion. The callback
        will be executed before the attribute is deleted. If the callback yields,
        the part after the yield will be executed after the deletion.

        The callback will be passed the old value of the attribute.

        The callback can be freely named.

        >>> class Cowboy(sheraf.Model):
        ...     table = "old_cowboys_deletion"
        ...     age = sheraf.IntegerAttribute()
        ...
        ...     @age.on_deletion
        ...     def delete_age(self, old):
        ...         print("Deleting age of", 50)
        ...
        >>> with sheraf.connection():
        ...     george = Cowboy.create(age=50)
        ...     del george.age
        Deleting age of 50
        """

        def wrapper(func):
            self.cb_deletion.append(func)
            return func

        return wrapper if not args else wrapper(args[0])

    def on_change(self, *args, **kwargs):
        """
        Shortcut for :meth:`~sheraf.attributes.Attribute.on_creation`,
        :meth:`~sheraf.attributes.Attribute.on_edition`
        and :meth:`~sheraf.attributes.Attribute.on_deletion` at the
        same time.
        """

        def wrapper(func):
            self.cb_creation.append(func)
            self.cb_edition.append(func)
            self.cb_deletion.append(func)
            return func

        return wrapper if not args else wrapper(args[0])

    def default(self, func):
        """
        Decorator for a callback to call to generate a default value for
        the attribute.

        >>> class Cowboy(sheraf.Model):
        ...     table = "default_cowboys"
        ...     age = sheraf.IntegerAttribute()
        ...
        ...     @age.default
        ...     def default_age(self):
        ...         return 42
        ...
        >>> with sheraf.connection(commit=True):
        ...     george = Cowboy.create()
        ...     george.age
        42
        """
        self._default_value = func

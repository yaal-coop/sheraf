READ_MEMOIZATION = False
WRITE_MEMOIZATION = True


def set_read_memoization(should_memoize_read):
    global READ_MEMOIZATION
    READ_MEMOIZATION = should_memoize_read


def set_write_memoization(should_memoize_write):
    global WRITE_MEMOIZATION
    WRITE_MEMOIZATION = should_memoize_write


class BaseAttribute(object):
    """Base type of all attributes of a base model.

    :param default: The value this attribute will be initialized with. If it is a callable object,
                    it will be called on initialization, else it will simply be copied. The callable
                    object can take either no argument, or one argument that will be the parent model.
    :type default: a callable object or a simple object
    :param key: The key to identify the attribute in its parent persistent mapping.
    :param lazy_creation: If True, the objet carried by the attribute is created on the first
                          read or write access. If False, it is created when the model object
                          is created. Default is True.
    :type lazy_creation: :class:`bool`
    :param read_memoization: Whether this attribute should be memoized on read. ``False`` by default.
    :type read_memoization: :class:`bool`
    :param write_memoization: Whether this attribute should be memoized on write. ``True`` by default.
    :type write_memoization: :class:`bool`

    When an attribute is memoized, its next reading will not result in a new database access.
    """

    def __init__(
        self,
        default=None,
        key=None,
        lazy_creation=True,
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
        self.lazy_creation = lazy_creation
        self.store_default_value = store_default_value

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
        return self.key(parent) in parent._persistent

    def key(self, parent):
        """:return: the key that identifies this attribute in its owner object"""
        if self._key is None:
            return self._default_key

        if isinstance(self._key, (list, tuple)):
            for key in self._key:
                if key in parent._persistent:
                    return key
            return self._key[0]

        return self._key

    def read_raw(self, parent):
        # Internal.
        # :param parent: The owner of this attribute
        # :return: the raw representation of this attribute (ie as stored in ZODB)
        try:
            return parent._persistent[self.key(parent)]
        except KeyError:
            default_value = self.create(parent)
            if self.store_default_value:
                parent._persistent[self.key(parent)] = default_value
            return default_value

    def write_raw(self, parent, value):
        # Internal.
        # :param parent: The owner of this attribute
        # :param value: The value assigned to this attribute
        # assigns the value parameter to this attribute
        parent._persistent[self.key(parent)] = value
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
        del parent._persistent[self.key(parent)]

    def save(self, parent):
        pass

    def delete(self, parent):
        pass

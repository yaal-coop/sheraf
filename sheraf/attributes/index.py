from BTrees.OOBTree import OOBTree


class Index:
    """
    :param attribute: The attribute being indexed
    :type attribute: class BaseAttribute
    :param key: The key the index will use. By default, just the attribute name is used.
    :param unique: If the attribute is unique, and two models have the same value for this
                   attribute, a :class:`~sheraf.exceptions.UniqueIndexException` is raised
                   when trying to write the second one. Automatically set to :class:`True` if
                   primary is :class:`True`.
    :type unique: bool
    :param key: The key the index will use. By default, just the attribute name is used.
    :param values A callable that takes the current attribute value and returns a
                  collection of values to index. Each generated value will be
                  indexed each time this attribute is edited. It may take time if
                  the generated collection is large. By default the attribute
                  :meth:`~sheraf.attributes.base.BaseAttribute.values` method is
                  applied.
    :param search: A callable that takes some raw data and returns a collection
                   of values to search in the index. By default, the
                   :meth:`~sheraf.attributes.base.BaseAttribute.search` method is
                   used.
    :param mapping: The mapping object to be used to store the indexed values. OOBTree by
                    default.
    :param nullok: If `True`, `None` or empty values can be indexed. `True` by default.
    :param noneok: Ignored in if `nullok` is `True`. Else, if `noneok` is  `True`, `None` values can be indexed. `False` by default."""

    def __init__(
        self,
        attribute_name=None,
        unique=False,
        key=None,
        values=None,
        search=None,
        mapping=None,
        primary=False,
        nullok=None,
        noneok=None,
        attribute=None,
    ):
        self.attribute = attribute
        self.attribute_name = attribute_name
        self.unique = unique or primary
        self.key = key
        self._values_func = values
        self._search_func = search or values
        self.mapping = mapping or OOBTree
        self.primary = primary
        self.nullok = nullok
        self.noneok = noneok

    def __repr__(self):
        if self.primary:
            return "<Index key={} unique={} primary>".format(self.key, self.unique)
        return "<Index key={} unique={}>".format(self.key, self.unique)

    @property
    def values_func(self):
        return self._values_func or self.attribute.values

    @property
    def search_func(self):
        return self._search_func or self.attribute.search

    def get_model_values(self, model):
        return self.get_values(self.attribute.read(model))

    def get_values(self, keys):
        nullok = self.nullok if self.nullok is not None else self.attribute.nullok
        noneok = self.noneok if self.noneok is not None else self.attribute.noneok

        if not nullok:  # Empty values are not indexed
            return {v for v in self.values_func(keys) if v}

        elif not noneok:  # None values are not indexed
            return {v for v in self.values_func(keys) if v is not None}

        else:  # Everything is indexed
            return self.values_func(keys)

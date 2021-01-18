class IndexDetails:
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
    :param values_func: A callable that takes the current attribute value and returns a
                        collection of values to index. Each generated value will be
                        indexed each time this attribute is edited. It may take time if
                        the generated collection is large. By default the attribute
                        :meth:`~sheraf.attributes.base.BaseAttribute.values` method is
                        applied.
    :param search_func: A callable that takes some raw data and returns a collection
                        of values to search in the index. By default, the
                        :meth:`~sheraf.attributes.base.BaseAttribute.search` method is
                        used.
    :param mapping: The mapping object to be used to store the indexed values. OOBTree by
                    default.
    """

    unique = False
    key = None
    values_func = None
    search_func = None
    attribute = None
    mapping = None
    primary = False

    def __init__(
        self, attribute, unique, key, values_func, search_func, mapping, primary
    ):
        self.attribute = attribute
        self.unique = unique or primary
        self.key = key
        self.values_func = values_func or attribute.values
        self.search_func = search_func or values_func or attribute.search
        self.mapping = mapping
        self.primary = primary

    def __repr__(self):
        if self.primary:
            return "<IndexDetails key={} unique={} primary>".format(
                self.key, self.unique
            )
        return "<IndexDetails key={} unique={}>".format(self.key, self.unique)

    def get_values(self, model):
        return self.values_func(self.attribute.read(model))

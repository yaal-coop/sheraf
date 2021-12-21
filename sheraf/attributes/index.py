import warnings

from BTrees.OOBTree import OOBTree


class Index:
    """
    Indexes should be either created as :class:`~sheraf.models.indexation.IndexedModel` class parameters,
    or with the attributes :func:`~sheraf.attributes.Attribute.index` method.

    :param attributes: The attributes being indexed. They can be either
        :class:`~sheraf.attributes.Attribute` or strings representing
        the attributes names in the model.
    :type *attributes: A collection of :class:`~sheraf.attributes.Attribute` or strings.
    :param key: The key the index will use. By default, it takes the name it has
                as a :class:`~sheraf.models.indexation.IndexedModel` attribute.
                If the :func:`~sheraf.attributes.Attribute.index` is used,
                the key is the :class:`~sheraf.attributes.Attribute` name.
    :param unique: If the index is unique, and two models have the same value for this
                   model, a :class:`~sheraf.exceptions.UniqueIndexException` is raised
                   when trying to write the second one. Automatically set to :class:`True` if
                   primary is :class:`True`.
    :type unique: bool
    :param index_keys_func: A callable that takes the current attribute value and returns a
                   single key, or a collection of keys, where the model instance will be indexed.
                   The keys will be regenerated each time this attribute will be edited,
                   and the index will be updated accordingly.
                   It may take time if
                   the generated collection is large. By default the attribute
                   :meth:`~sheraf.attributes.Attribute.index_keys` method is
                   applied.
    :param search_keys_func: A callable that takes some raw data and returns a collection
                   of keys to search in the index. By default, the
                   :meth:`~sheraf.attributes.Attribute.search_keys_func` method is
                   used.
    :param mapping: The mapping object to be used to store the indexed values.
                   By default the `index_mapping` class attribute is used.
                   If you know that the keys of the index will always be a
                   specific type, like integers, you might way to use this
                   attribute to use specialized datastructures.
    :param nullok: If `True`, `None` or empty values can be indexed. `True` by default.
    :param noneok: Ignored in if `nullok` is `True`. Else, if `noneok` is
                   `True`, `None` values can be indexed. `False` by default."
    :param auto: Defaults to `True`, enable the automatic index update. When set to `False` the index won't be updated when the attributes are updated.

    >>> class People(sheraf.Model):
    ...     table = "index_people"
    ...
    ...     # Simple indexing
    ...     name = sheraf.SimpleAttribute()
    ...     nameindex = sheraf.Index("name")
    ...
    ...     # Indexing with the .index() shortcut
    ...     size = sheraf.IntegerAttribute().index()
    ...
    ...     # Emails can only be owned once
    ...     email = sheraf.SimpleAttribute().index(unique=True)
    ...
    ...     # Indexing people by their decade
    ...     age = sheraf.SimpleAttribute().index(key="decade", index_keys_func=lambda age: {age // 10})
    ...
    >>> with sheraf.connection(commit=True):
    ...     m = People.create(
    ...         name="George Abitbol",
    ...         size=180,
    ...         email="george@abitbol.com",
    ...         age=55,
    ...     )
    ...
    >>> with sheraf.connection():
    ...     assert [m] == People.filter(nameindex="George Abitbol")
    ...     assert [m] == People.filter(size=180)
    ...     assert [m] == People.filter(decade=5)
    ...
    >>> with sheraf.connection():
    ...     People.create(name="Peter", size=175, email="george@abitbol.com", age=35)
    Traceback (most recent call last):
        ...
    UniqueIndexException
    """

    default_mapping = OOBTree

    def __init__(
        self,
        *attributes,
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
        auto=True,
    ):
        if values and not index_keys_func:
            warnings.warn(
                "Index 'values' parameter is deprecated and will be removed in sheraf 0.6. "
                "Please use 'index_keys_func' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            index_keys_func = values

        if search and not search_keys_func:
            warnings.warn(
                "Index 'search' parameter is deprecated and will be removed in sheraf 0.6. "
                "Please use 'search_keys_func' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            search_keys_func = search

        self.attributes = attributes
        self.unique = unique or primary
        self.key = key
        self.default_index_keys_func = index_keys_func
        self._search_keys_func = search_keys_func or index_keys_func
        self.index_keys_funcs = {}
        self.mapping = mapping or self.default_mapping
        self.primary = primary
        self.nullok = nullok
        self.noneok = noneok
        self.auto = auto

    def __repr__(self):
        if self.primary:
            return f"<Index key={self.key} unique={self.unique} primary>"
        return f"<Index key={self.key} unique={self.unique}>"

    def index_keys_func(self, *args, **kwargs):
        """
        This decorator sets a index_keys method, for one, several or all of the index attributes.

        - If no positionnal argument is passed, then this sets a default index_keys function for the
          index.
        - You can pass one or several attributes or attributes names to set a specific index_keys method
          for those attributes.
        - If you do set a specific index_keys method for one or several attributes, the decorated function
          will be given the attribute index_keys as positionnal arguments, in the order they were passed
          to the decorator.

        The decorated function must return a single key, or a collection of keys, where the index
        will store the current model instance. Depending on the `noneok` and `nullok`
        :class:`~sheraf.attributes.index.Index` parameters, `None` and falsy index keys might be
        ignored.

        >>> class Cowboy(sheraf.Model):
        ...     table = "any_values_table"
        ...     first_name = sheraf.StringAttribute()
        ...     last_name = sheraf.StringAttribute()
        ...     surname = sheraf.StringAttribute()
        ...     name_parts = sheraf.Index(first_name, last_name, surname)
        ...
        ...     @name_parts.index_keys_func
        ...     def default_name_indexation(self, values):
        ...         return values.lower()
        ...
        ...     @name_parts.index_keys_func(first_name, "last_name")
        ...     def full_name(self, first, last):
        ...         return f"{first} {last}".lower()
        ...
        >>> with sheraf.connection():
        ...     m = Cowboy.create(first_name="George", last_name="Abitbol", surname="Georgy")
        ...     assert m in Cowboy.search(name_parts="george abitbol")
        ...     assert m in Cowboy.search(name_parts="georgy")

        .. note :: You can use :meth:`~sheraf.models.indexation.BaseIndexedModel.index_keys`
                   to check the index keys your custom function generates.
        """

        # Guess if the decorator has been called with or without parenthesis
        if args and (len(args) > 1 or not callable(args[0])):
            attributes = args
            args = []
        else:
            attributes = []

        def wrapper(func):
            # If no attribute is passed as a positionnal argument,
            # the method will be the default values method
            if not attributes:
                self.default_index_keys_func = func

                if self._search_keys_func is None:
                    self._search_keys_func = func

            # Else the method will be assigned to each attribute
            self.index_keys_funcs.setdefault(func, []).append(attributes)

            return func

        return wrapper if not args else wrapper(args[0])

    def values(self, *args, **kwargs):
        warnings.warn(
            "Index 'values' method is deprecated and will be removed in sheraf 0.6. "
            "Please use 'index_keys_func' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.index_keys_func(*args, **kwargs)

    def search_keys_func(self, *args, **kwargs):
        """
        This decorator sets the search_keys method for the index. It should return
        a single key to search in the index, or a collection of keys to
        search in the index. If it returns an indexed collection, by default the
        model instances will be returned in the order the index keys will be iterated.

        >>> class Model(sheraf.Model):
        ...     table = "any_search_table"
        ...     foo = sheraf.StringAttribute()
        ...     bar = sheraf.StringAttribute()
        ...     theindex = sheraf.Index(foo, bar)
        ...
        ...     @theindex.search_keys_func
        ...     def the_search_method(self, values):
        ...         return values.lower()
        ...
        >>> with sheraf.connection():
        ...     m = Model.create(foo="foo", bar="bar")
        ...     assert m in Model.search(theindex="foo")
        ...     assert m in Model.search(theindex="BAR")

        .. note :: You can use :meth:`~sheraf.models.indexation.BaseIndexedModel.search_keys`
                   to check the index keys your custom function generates.
        """

        def wrapper(func):
            self._search_keys_func = func
            return func

        return wrapper if not args else wrapper(args[0])

    def search(self, *args, **kwargs):
        warnings.warn(
            "Index 'search' method is deprecated and will be removed in sheraf 0.6. "
            "Please use 'search_keys_func' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.search_keys_func(*args, **kwargs)

    def get_model_index_keys(self, model):
        return {
            v
            for func, attr_groups in self.index_keys_funcs.items()
            for attributes in attr_groups
            for v in self.get_index_keys(model, attributes, func)
        }

    def get_index_keys(self, model, attributes, func):
        values = self.call_index_keys_func(model, attributes, func)

        if not self.nullok:  # Empty values are not indexed
            return {v for v in values if v}

        elif not self.noneok:  # None values are not indexed
            return {v for v in values if v is not None}

        else:  # Everything is indexed
            return values

    def call_index_keys_func(self, model, attributes, func):
        if not all(attribute.is_created(model) for attribute in attributes):
            return {}

        values = [attribute.read(model) for attribute in attributes]

        if not func:
            return set(values)

        try:
            values = func(*values)
        except TypeError as exc:
            if "positional argument" not in str(exc):
                raise
            values = func(model, *values)

        values = values if isinstance(values, (list, set, tuple, dict)) else {values}
        return values

    def call_search_func(self, model, value):
        if not self._search_keys_func:
            return {value}

        try:
            values = self._search_keys_func(value)
        except TypeError as exc:
            if "positional argument" not in str(exc):
                raise
            values = self._search_keys_func(model, value)

        values = values if isinstance(values, (list, set, tuple, dict)) else {values}
        return values

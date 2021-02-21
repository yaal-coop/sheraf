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
    :param values: A callable that takes the current attribute value and returns a
                   collection of values to index. Each generated value will be
                   indexed each time this attribute is edited. It may take time if
                   the generated collection is large. By default the attribute
                   :meth:`~sheraf.attributes.Attribute.values` method is
                   applied.
    :param search: A callable that takes some raw data and returns a collection
                   of values to search in the index. By default, the
                   :meth:`~sheraf.attributes.Attribute.search` method is
                   used.
    :param mapping: The mapping object to be used to store the indexed values.
                   By default :class:`~BTrees.OOBTree.OOBTree` is used.
    :param nullok: If `True`, `None` or empty values can be indexed. `True` by default.
    :param noneok: Ignored in if `nullok` is `True`. Else, if `noneok` is
                   `True`, `None` values can be indexed. `False` by default."

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
    ...     age = sheraf.SimpleAttribute().index(key="decade", values=lambda age: {age // 10})
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

    def __init__(
        self,
        *attributes,
        unique=False,
        key=None,
        values=None,
        search=None,
        mapping=None,
        primary=False,
        nullok=None,
        noneok=None,
    ):
        self.attributes = attributes
        self.unique = unique or primary
        self.key = key
        self.default_values_func = values
        self.search_func = search or values
        self.values_funcs = {}
        self.mapping = mapping or OOBTree
        self.primary = primary
        self.nullok = nullok
        self.noneok = noneok

    def __repr__(self):
        if self.primary:
            return "<Index key={} unique={} primary>".format(self.key, self.unique)
        return "<Index key={} unique={}>".format(self.key, self.unique)

    def values(self, *args, **kwargs):
        """
        This can be used either as a decorator or a regular method. Both ways
        it sets a values method, for one, several or all of the index attributes.

        As a decorator:

        - If no positionnal argument is passed, then this sets a default values function for the
          index.
        - You can pass one or several attributes or attributes names to set a specific values method
          for those attributes.

        >>> class Model(sheraf.Model):
        ...     table = "any_table"
        ...     foo = sheraf.StringAttribute()
        ...     bar = sheraf.StringAttribute()
        ...     baz = sheraf.StringAttribute()
        ...     theindex = sheraf.Index(foo, bar, baz)
        ...
        ...     @theindex.values
        ...     def the_default_values_method(self, values):
        ...         return {values.lower()}
        ...
        ...     @theindex.values(bar, "baz")
        ...     def the_baz_values_method(self, values):
        ...         return {values.upper()}
        ...
        >>> with sheraf.connection():
        ...     m = Model.create(foo="Foo", bar="Bar", baz="Baz")
        ...     assert m in Model.filter(theindex="foo")
        ...     assert m in Model.filter(theindex="BAR")
        ...     assert m in Model.filter(theindex="BAZ")

        As a regular method:

        >>> class Model(sheraf.Model):
        ...     table = "any_other_table"
        ...     first_name = sheraf.StringAttribute()
        ...     last_name = sheraf.StringAttribute()
        ...
        ...     name = sheraf.Index(first_name, last_name).values(
        ...         first_name=lambda x: {x.lower()}
        ...     )
        """

        if kwargs:
            for attribute_name, func in kwargs.items():
                self.values_funcs.setdefault(func, []).append(attribute_name)
            return self

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
                self.default_values_func = func

                if self.search_func is None:
                    self.search_func = func

            # Else the method will be assigned to each attribute
            for attribute in attributes:
                self.values_funcs.setdefault(func, []).append(attribute)

            return func

        return wrapper if not args else wrapper(args[0])

    def search(self, *args, **kwargs):
        """
        This decorator sets the search method for the index.

        >>> class Model(sheraf.Model):
        ...     table = "any_table"
        ...     foo = sheraf.StringAttribute()
        ...     bar = sheraf.StringAttribute()
        ...     theindex = sheraf.Index(foo, bar)
        ...
        ...     @theindex.search
        ...     def the_search_method(self, values):
        ...         return {values.lower()}
        ...
        >>> with sheraf.connection():
        ...     m = Model.create(foo="foo", bar="bar")
        ...     assert m in Model.search(theindex="foo")
        ...     assert m in Model.search(theindex="BAR")
        """

        def wrapper(func):
            self.search_func = func
            return func

        return wrapper if not args else wrapper(args[0])

    def get_model_values(self, model):
        if self.default_values_func not in self.values_funcs:
            attrs_with_func = [
                attr for attrs in self.values_funcs.values() for attr in attrs
            ]
            self.values_funcs[self.default_values_func] = [
                attribute
                for attribute in self.attributes
                if attribute not in attrs_with_func
            ]
        return {
            v
            for func, attributes in self.values_funcs.items()
            for attribute in attributes
            for v in self.get_values(model, attribute, func)
        }

    def get_values(self, model, attribute, func):
        values = self.call_values_func(model, attribute, func)

        if not self.nullok:  # Empty values are not indexed
            return {v for v in values if v}

        elif not self.noneok:  # None values are not indexed
            return {v for v in values if v is not None}

        else:  # Everything is indexed
            return values

    def call_values_func(self, model, attribute, func):
        if not attribute.is_created(model):
            return {}

        value = attribute.read(model)

        if not func:
            return {value}
        try:
            return func(value)
        except TypeError:
            return func(model, value)

    def call_search_func(self, model, value):
        if not self.search_func:
            return {value}
        try:
            return self.search_func(value)
        except TypeError:
            return self.search_func(model, value)

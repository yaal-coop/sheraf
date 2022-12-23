import itertools
import operator
from collections import OrderedDict
from collections.abc import Iterable
from collections.abc import Iterator

import sheraf.constants
from sheraf.exceptions import InvalidFilterException
from sheraf.exceptions import InvalidOrderException
from sheraf.tools.more_itertools import unique_everseen


class QuerySet:
    """
    A :class:`~sheraf.queryset.QuerySet` is a collection containing
    :class:`~sheraf.models.Model` instances. Like in a regular :class:`set`,
    objects are unique, but the main difference is that
    :class:`~sheraf.queryset.QuerySet` keeps the insertion order.

    :param iterable: A collection of models. If `iterable` is None, then
        `model` must be set.
    :type iterable: Iterable
    :param model_class: A model class to iterate over. If `model` is None, then
        `iterable` must be set. If both are set, `model_class` is ignored.
    :type reversed_iterable: A Model class
    :param predicate: a callable takes an instance as parameter and return a
        Boolean (if True, the instance will be returned in the iteration). If
        None, everything is returned.
    :type predicate: Predicate
    :param kwargs: A dictionnary containing the values expected from the model
        parameters. If `kwargs` is `{"foo": "bar"}` then the queryset will only
        contains models which attribute `foo` is `"bar"`.

    For the following examples, let us work with a simple **Cowboy** model. For
    the sake of simplicity we use a
    :class:`~sheraf.models.IntOrderedNamedAttributesModel` so the first instance
    created will have id 0, the second will have id 1 and so on...

    >>> class Cowboy(sheraf.IntOrderedNamedAttributesModel):
    ...     table = "queryset_people"
    ...     name = sheraf.SimpleAttribute()
    ...     age = sheraf.SimpleAttribute()
    ...
    >>> with sheraf.connection(commit=True):
    ...     peter = Cowboy.create(name="Peter", age=30)
    ...     steven = Cowboy.create(name="Steven", age=30)
    ...     george = Cowboy.create(name="George Abitbol", age=50)

    :class:`~sheraf.queryset.QuerySet` are mostly created by doing requests on a
    Model with :func:`~sheraf.models.indexation.IndexedModel.all`,
    :func:`~sheraf.models.indexation.IndexedModel.filter` or
    :func:`~sheraf.models.indexation.IndexedModel.order`, but can also be
    initialized with custom data.

    >>> with sheraf.connection():
    ...    a = Cowboy.all() # returns a QuerySet with all Cowboy
    ...    b = QuerySet([peter, steven, george]) # This is an equivalent custom QuerySet
    ...    assert list(a) == list(b)

    :class:`~sheraf.queryset.QuerySet` behave like iterators, and can only be
    consumed once.

    >>> with sheraf.connection():
    ...    everybody = Cowboy.all()
    ...    assert [peter, steven, george] == list(everybody)
    ...    assert [] == everybody

    .. note :: :class:`~sheraf.queryset.QuerySet` can be compared against
        anything iterable, but the comparison will consume the
        :class:`~sheraf.queryset.QuerySet`.

    :class:`~sheraf.queryset.QuerySet` keeps the order of insertion.

    >>> assert QuerySet([peter, steven]) != QuerySet([steven, peter])

    :class:`~sheraf.queryset.QuerySet` supports slicing. Slices returns another
    :class:`~sheraf.queryset.QuerySet`.

    >>> with sheraf.connection():
    ...     assert peter == Cowboy.all()[0]
    ...     assert QuerySet([peter, steven]) == Cowboy.all()[0:2]
    ...     assert QuerySet([peter, steven, george]) == Cowboy.all()[0:]
    """

    def __init__(
        self,
        iterable=None,
        model_class=None,
        predicate=None,
        primary_key=None,
        **kwargs,
    ):
        self.filters = OrderedDict(kwargs)
        self._iterable = iterable
        self._iterator = None
        self._predicate = predicate
        self._start = None
        self._stop = None
        self._step = None
        self.model = model_class
        if primary_key:
            self.primary_key = primary_key
        elif model_class:
            self.primary_key = model_class.primary_key()
        self.orders = OrderedDict()

        if iterable is None and model_class is None:
            self._iterable = []

        self.__iter__()

    def __iter__(self):
        return self

    def __repr__(self):
        result = "<QuerySet"
        if self.model:
            result = f"{result} model={self.model.__name__}"

        if self._iterable:
            result = f"{result} iterable={self._iterable}"

        if self._predicate:
            result = f"{result} predicate={self._predicate}"

        if self.filters:
            filters = ", ".join(f"{k}={v[1]}" for k, v in self.filters.items())
            result = f"{result} filters=({filters})"

        result = f"{result}>"
        return result

    def __next__(self):
        if not self._iterator:
            self._init_iterator()

        return next(self._iterator)

    def __eq__(self, other):
        if isinstance(other, Iterable):
            return all(
                a == b
                for a, b in itertools.zip_longest(
                    iter(self), iter(other), fillvalue=object()
                )
            )
        return super().__eq__(other)

    def __and__(self, other):
        return QuerySet(
            set(self) & set(other),
            self.model if self.model == other.model else None,
        )

    def __or__(self, other):
        return QuerySet(
            set(self) | set(other),
            self.model if self.model == other.model else None,
        )

    def __xor__(self, other):
        return QuerySet(
            set(self) ^ set(other),
            self.model if self.model == other.model else None,
        )

    def __add__(self, other):
        return QuerySet(
            unique_everseen(itertools.chain(self, other)),
            self.model if self.model == other.model else None,
        )

    def __bool__(self):
        try:
            next(self.copy())
            self._iterator = None
            return True
        except StopIteration:
            return False

    def __getitem__(self, item):
        qs = self.copy()

        if isinstance(item, slice):
            qs._start, qs._stop, qs._step = item.start, item.stop, item.step
            return qs

        else:
            qs._start, qs._stop, qs._step = item, item + 1, 1
            return next(qs)

    def __len__(self):
        """
        :return: The number of objects in the
            :class:`~sheraf.queryset.QuerySet`.

        >>> with sheraf.connection():
        ...     assert Cowboy.create()
        ...     qs = Cowboy.all()
        ...     assert len(qs) == 1
        """
        # No shortcut possible when there is a predicate,
        # or when there are several filters
        if self._predicate or not self.model or len(self.filters) > 1:
            return sum(1 for _ in self.copy())

        # We basically want to search all the models
        if not self.filters:
            return self.model.count()

        # Take the unique filter, and hope it is indexed
        index_name = list(self.filters.keys())[0]
        _, filter_value, filter_search_func = list(self.filters.values())[0]
        if index_name not in self.model.indexes:
            return sum(1 for _ in self.copy())

        index = self.model.indexes[index_name]
        if filter_search_func:
            index_values = index.details.call_search_func(self.model, filter_value)
        else:
            index_values = filter_value

        if index.details.unique:
            return sum(int(index.has_item(v)) for v in index_values)

        else:
            return sum(
                len(index.get_item(v)) for v in index_values if index.has_item(v)
            )

    @property
    def indexed_filters(self):
        return [
            (
                name,
                value,
                search_func,
                self.orders.get(name) == sheraf.constants.DESC,
            )
            for (name, value, search_func) in self.filters.values()
            if name in self.model.indexes and self.model.indexes[name].details.auto
        ]

    @property
    def non_indexed_filters(self):
        return [
            (name, value)
            for (name, value, _) in self.filters.values()
            if (name not in self.model.indexes and name in self.model.attributes)
            or (
                name in self.model.indexes and not self.model.indexes[name].details.auto
            )
        ]

    @property
    def first_indexed_order(self):
        for name, value in self.orders.items():
            if (
                self.model
                and name in self.model.indexes
                and self.model.indexes[name].details.auto
            ):
                return name, value

    def get_index_keys(self, index, filter_value, search_func, reverse):
        if not filter_value:
            return index.iterkeys(reverse=reverse)

        if search_func:
            return index.details.call_search_func(self.model, filter_value)

        return [filter_value]

    def _objects_ids(self, index_name, filter_value, search_func, reverse):
        index = self.model.indexes[index_name]
        keys = self.get_index_keys(index, filter_value, search_func, reverse)

        if index.details.unique:
            mappings = (index.get_item(key, True) for key in keys)

        else:
            mappings_lists = (index.get_item(key, True) for key in keys)
            mappings = (m for l in mappings_lists if l for m in l)

        return (m[self.model.primary_key()] for m in mappings if m)

    def _multiple_indexes_iterator(self):
        ids_sets = (set(self._objects_ids(*index)) for index in self.indexed_filters)
        raw_ids = set.intersection(*ids_sets)

        pk_attribute = self.model.attributes[self.model.primary_key()]
        ids = (pk_attribute.deserialize(id_) for id_ in raw_ids)
        return ids

    def _single_index_iterator(
        self, index_name, filter_value=None, search_func=None, reverse=False
    ):
        """
        Returns an iterator over one indexed attribute.
        """
        pk_attribute = self.model.attributes[self.model.primary_key()]

        raw_ids = self._objects_ids(index_name, filter_value, search_func, reverse)
        unique_raw_ids = unique_everseen(raw_ids)
        ids = (pk_attribute.deserialize(id_) for id_ in unique_raw_ids)
        return ids

    def _primary_index_iterator(self):
        pk_index = self.model.indexes[self.primary_key]
        pk_attribute = self.model.attributes[self.model.primary_key()]

        reverse = self.orders.get(self.primary_key) == sheraf.constants.DESC
        if self.primary_key == self.model.primary_key():
            ids = pk_index.iterkeys(reverse)

        elif self.model.indexes[self.primary_key].details.unique:
            ids = (
                pk_attribute.deserialize(mapping[self.model.primary_key()])
                for mapping in pk_index.itervalues(reverse)
            )

        else:
            ids = (
                pk_attribute.deserialize(id)
                for mappings in pk_index.itervalues(reverse)
                for id in mappings.keys()
            )

        return ids

    def _init_iterator(self):
        if self._iterable:
            iterator = iter(self._iterable)

        elif not self.model:
            iterator = iter([])

        # iterator on the first indexed filtered attribute
        elif self.indexed_filters:
            iterator = self._single_index_iterator(*self.indexed_filters[0])

        # iterator on the first indexed orderde attribute
        elif self.first_indexed_order:
            iterator = self._single_index_iterator(
                index_name=self.first_indexed_order[0],
                reverse=self.first_indexed_order[1],
            )

        # iterate all items on the primary key
        else:
            iterator = self._primary_index_iterator()

        # instanciate model objects
        if self.model:
            iterator = (
                self.model.read(key) if not isinstance(key, self.model) else key
                for key in iterator
            )

        # Checks the models fits all the filters
        iterator = (
            model for model in iterator if self._model_has_expected_values(model)
        )

        # Successively sorts the list from the less important
        # order to the most important order.
        already_ordered = (
            not self.indexed_filters
            and self.first_indexed_order
            and len(self.orders) == 1
        )
        if self.orders and not already_ordered:
            iterable = iterator
            for attribute, order in reversed(self.orders.items()):
                # those calls to 'sorted' have a HUGE impact on read perfs
                iterable = sorted(
                    iterable,
                    key=operator.attrgetter(attribute),
                    reverse=(order == sheraf.constants.DESC),
                )
            iterator = iter(iterable)

        # Only select a slice of the wanted models
        if self._start is not None or self._stop is not None or self._step is not None:
            iterator = itertools.islice(iterator, self._start, self._stop, self._step)

        self._iterator = iterator

    def _model_has_expected_values(self, model):
        if not all(
            getattr(model, filter_name) == expected_value
            for filter_name, expected_value in self.non_indexed_filters
        ):
            return False

        if not all(
            (
                set(model.indexes[name].details.call_search_func(model, value))
                & set(model.indexes[name].details.get_model_index_keys(model))
            )
            if search_func
            else (value in model.indexes[name].details.get_model_index_keys(model))
            for name, value, search_func, _ in self.indexed_filters
        ):
            return False

        return not self._predicate or self._predicate(model)

    def count(self):
        return len(self)

    def copy(self):
        """Copies the :class:`~sheraf.queryset.QuerySet` without consuming it.

        >>> with sheraf.connection():
        ...     peter = Cowboy.create(name="Peter")
        ...     steven = Cowboy.create(name="Steven")
        ...     george = Cowboy.create(name="George")
        ...     qall = Cowboy.all()
        ...     qcopy = qall.copy()
        ...
        ...     assert [peter, steven, george] == qall
        ...     # now qall is consumed
        ...
        ...     assert [peter, steven, george] == qcopy
        ...     # now qcopy is consumed
        """

        if isinstance(self._iterable, Iterator):
            self._iterable, iterable = itertools.tee(self._iterable)
        else:
            iterable = self._iterable

        qs = QuerySet(iterable, self.model)
        qs.filters = self.filters.copy()
        qs.orders = self.orders.copy()
        qs._predicate = self._predicate
        return qs

    def delete(self):
        """Delete the objects contained in the queryset.

        Avoids problems when itering on deleted objects.
        """
        identifiers = [(m.__class__, m.identifier) for m in self]
        for klass, identifier in identifiers:
            klass.read(identifier).delete()

    def filter(self, predicate=None, **kwargs):
        """Refine a copy of the current :class:`~sheraf.queryset.QuerySet` with
        further tests.

        :param predicate: filter instance by returning a truthy value.
            If `None` everything is selected.
        :type predicate: callable object
        :param kwargs: A dictionnary containing the values expected from the
            model parameters. If ``kwargs`` is ``{"foo": "bar"}`` then the
            queryset will only contains models which attribute ``foo``
            is ``"bar"``.
        :type kwargs: A dictionary which keys must be valid attributes of the
            model iterated.
        :return: A copy of the current :class:`~sheraf.queryset.QuerySet`
            refined with further tests.
        :return type: :class:`~sheraf.queryset.QuerySet`

        It is possible to chain :func:`~sheraf.queryset.QuerySet.filter` calls:

        >>> with sheraf.connection():
        ...    assert Cowboy.filter(name="George Abitbol", age=50) == \\
        ...           Cowboy.filter(name="George Abitbol").filter(age=50)
        ...
        >>> with sheraf.connection():
        ...    assert Cowboy.filter(lambda person: "Abitbol" in person.name, age=50) == \\
        ...           Cowboy.filter(lambda person: "Abitbol" in person.name).filter(age=50)

        An attribute cannot be filtered twice:

        >>> with sheraf.connection():
        ...    Cowboy.filter(age=30).filter(age=40)
        Traceback (most recent call last):
            ...
        sheraf.exceptions.InvalidFilterException: Some filter parameters appeared twice

        .. note::   Filtering on indexed attributes is more performant than filtering on non-indexed attributes. See :func:`~sheraf.attributes.Attribute.index`.
        """
        return self._filter(False, predicate=predicate, **kwargs)

    def search(self, **kwargs):
        """
        Refine a copy of the current :class:`~sheraf.queryset.QuerySet` with further tests.

        This method is very similar to :func:`~sheraf.queryset.QuerySet.filter` except the
        values it takes are transformed with the same way values are transformed at indexation.
        TODO: pas très clair

        For instance, if an attribute indexes its values with a lowercase search_func, the
        :func:`~sheraf.queryset.QuerySet.search` attributes will go through the same
        search_func. Hence it allows to pass uppercase filter values, while
        :func:`~sheraf.queryset.QuerySet.filter` does not allow this.

        >>> class MyCustomModel(sheraf.Model):
        ...     table = "my_custom_model"
        ...     my_attribute = sheraf.SimpleAttribute().index(
        ...        index_keys_func=lambda string: {string.lower()}
        ...     )
        ...
        >>> with sheraf.connection(commit=True):
        ...     m = MyCustomModel.create(my_attribute="FOO")
        ...
        >>> with sheraf.connection():
        ...     assert [m] == MyCustomModel.search(my_attribute="foo")
        ...     assert [m] == MyCustomModel.filter(my_attribute="foo")
        ...
        ...     assert [m] == MyCustomModel.search(my_attribute="FOO")
        ...     assert [] == MyCustomModel.filter(my_attribute="FOO")
        """

        return self._filter(True, **kwargs)

    def _filter(self, search_func, predicate=None, **kwargs):
        qs = self.copy()
        if self.model:
            for filter_name in kwargs.keys():
                if (
                    filter_name not in self.model.attributes
                    and filter_name not in self.model.indexes
                ):
                    raise sheraf.exceptions.InvalidFilterException(
                        "{} has no attribute {}".format(
                            self.model.__name__, filter_name
                        )
                    )
        kwargs_values = OrderedDict(
            {
                filter_name: (filter_name, filter_value, search_func)
                for filter_name, filter_value in kwargs.items()
            }
        )
        common_attributes = set(qs.filters) & set(kwargs_values)
        invalid_common_attributes = any(
            key for key in common_attributes if qs.filters[key] != kwargs_values[key]
        )
        if invalid_common_attributes:
            raise InvalidFilterException("Some filter parameters appeared twice")

        qs.filters.update(kwargs_values)

        if not qs._predicate:
            qs._predicate = predicate

        elif predicate:
            old_predicate = qs._predicate
            qs._predicate = lambda m: old_predicate(m) and predicate(m)

        return qs

    def order(self, *args, **kwargs):
        """Copies the current :class:`~sheraf.queryset.QuerySet` and adds more
        order to it.

        :param args: There can be only one positionnal argument. Choose to iterate
            over ids in an ascending or a descending way.
        :type args: ``sheraf.ASC`` or ``sheraf.DESC``
        :param kwargs: Further parameters will set an order on the matching
            model attributes.
        :type kwargs: A dictionary which keys must be valid attributes of the
            model iterated, and the values must be ``sheraf.ASC`` or
            ``sheraf.DESC``
        :return: A copy of the current :class:`~sheraf.queryset.QuerySet` with
            refined order.
        :return type: :class:`~sheraf.queryset.QuerySet`

        The default order is the ascending model ids.

        >>> with sheraf.connection(commit=True):
        ...     peter = Cowboy.create(name="Peter", age=35)
        ...     steven = Cowboy.create(name="Steven", age=35)
        ...     george = Cowboy.create(name="George", age=50)
        ...
        >>> with sheraf.connection():
        ...     assert [peter, steven, george] == Cowboy.all()
        ...     assert [peter, steven, george] == Cowboy.all().order(sheraf.ASC)
        ...     assert [george, steven, peter] == Cowboy.all().order(sheraf.DESC)
        ...
        ...     assert [george, peter, steven] == Cowboy.all().order(name=sheraf.ASC)
        ...     assert [steven, peter, george] == Cowboy.all().order(name=sheraf.DESC)

        Several order parameters can be passed, either as arguments of the
        function, or by calling :func:`~sheraf.queryset.QuerySet.order` calls.

        >>> with sheraf.connection():
        ...     assert [george, peter, steven] == Cowboy.all().order(age=sheraf.DESC, name=sheraf.ASC)

        .. note:: Sorting on indexed attributes is more performant than
            sorting on other attributes. See
            :func:`~sheraf.attributes.Attribute.index`.
            The less :func:`~sheraf.queryset.QuerySet.order` parameters are
            passed, the better performances will be.
        """
        if not self.model and (args or not kwargs):
            raise InvalidOrderException(
                "QuerySets without models should have explict order arguments"
            )

        if len(args) > 1:
            raise InvalidOrderException(
                "Only one 'order' positionnal parameter is allowed."
            )

        qs = self.copy()

        if self.model:
            for attribute, value in kwargs.items():
                if attribute not in self.model.attributes:
                    raise sheraf.exceptions.InvalidOrderException(
                        f"{self.model.__name__} has no attribute {attribute}"
                    )

                if value not in (sheraf.constants.ASC, sheraf.constants.DESC):
                    raise sheraf.exceptions.InvalidOrderException(
                        "Parameter {} has an invalid order value {}".format(
                            attribute, value
                        )
                    )

        if len(args) > 0:
            identifier = args[0]
            if identifier not in (sheraf.constants.ASC, sheraf.constants.DESC):
                raise InvalidOrderException(
                    f"Parameter id has an invalid order value {identifier}"
                )

            if self.primary_key in qs.orders:
                raise InvalidOrderException("Id order has been set twice")

            qs.orders[self.primary_key] = identifier

        common_attributes = set(qs.orders) & set(kwargs)
        if common_attributes:
            raise InvalidOrderException("Some order parameters appeared twice")

        qs.orders.update(kwargs)

        return qs

    def get(self):
        """If the :class:`~sheraf.queryset.QuerySet` contains one, and only one
        item, this method returns the item. If the
        :class:`~sheraf.queryset.QuerySet` contains several objects, it raises a
        :class:`~sheraf.exceptions.QuerySetUnpackException`. If the
        :class:`~sheraf.queryset.QuerySet` is empty, it raises a
        :class:`~sheraf.exceptions.EmptyQuerySetUnpackException`.

        >>> with sheraf.connection():
        ...     peter = Cowboy.create(name="Peter")
        ...     steven = Cowboy.create(name="Steven")
        ...     assert peter == Cowboy.filter(name="Peter").get()
        ...     Cowboy.all().get()
        Traceback (most recent call last):
            ...
        sheraf.exceptions.TooManyValuesSetUnpackException: Trying to unpack a QuerySet with multiple elements <QuerySet model=Cowboy>
        >>> with sheraf.connection():
        ...     Cowboy.filter(age=30).get()
        Traceback (most recent call last):
            ...
        sheraf.exceptions.EmptyQuerySetUnpackException: Trying to unpack an empty QuerySet
        >>> with sheraf.connection():
        ...     Cowboy.filter(name="Unknown cowboy").get()
        Traceback (most recent call last):
            ...
        sheraf.exceptions.EmptyQuerySetUnpackException: Trying to unpack an empty QuerySet
        """
        try:
            element = next(self)
        except StopIteration:
            raise sheraf.exceptions.EmptyQuerySetUnpackException(queryset=self)

        try:
            next(self)
        except StopIteration:
            return element
        else:
            raise sheraf.exceptions.TooManyValuesSetUnpackException(queryset=self)

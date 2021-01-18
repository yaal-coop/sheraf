import itertools
import operator
from collections import OrderedDict

from BTrees.OOBTree import OOTreeSet, union, intersection, difference

import sheraf.constants
from sheraf.exceptions import InvalidFilterException, InvalidOrderException

from collections.abc import Iterable, Sized
from sheraf.tools.more_itertools import unique_everseen


class QuerySet(object):
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
    ...     assert QuerySet([peter]) == Cowboy.all()[0]
    ...     assert QuerySet([george]) == Cowboy.all()[-1]
    ...     assert QuerySet([peter, steven]) == Cowboy.all()[0:2]
    ...     assert QuerySet([peter, steven, george]) == Cowboy.all()[0:]
    """

    def __init__(self, iterable=None, model_class=None, predicate=None, **kwargs):
        self.filters = OrderedDict(kwargs)
        self._iterable = iterable
        self._iterator = None
        self._predicate = predicate
        self.model = model_class
        self.orders = OrderedDict()

        if iterable is None and model_class is None:
            self._iterable = []

        self.__iter__()

    def __iter__(self):
        return self

    def __repr__(self):
        if self.model:
            return "<QuerySet model={}>".format(self.model.__name__)

        if self._iterable:
            return "<QuerySet iterable={}>".format(self._iterable)

        return "<QuerySet>"

    def _model_has_expected_values(self, model):
        for filter_name, expected_value, filter_transformation in self.filters.values():
            if filter_name in model.indexes():
                index = model.indexes()[filter_name]
                if filter_transformation:
                    if not set(index.details.search_func(expected_value)) & set(
                        index.details.get_values(model)
                    ):
                        return False
                else:
                    if expected_value not in index.details.get_values(model):
                        return False

            elif filter_name in model.attributes:
                if getattr(model, filter_name) != expected_value:
                    return False
        return True

    def __next__(self):
        if not self._iterator:
            self._init_iterator()

        while True:
            try:
                model = next(self._iterator)
            except sheraf.exceptions.ModelObjectNotFoundException:
                continue

            if self._model_has_expected_values(model) and (
                not self._predicate or self._predicate(model)
            ):
                return model

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
        return QuerySet(intersection(OOTreeSet(self), OOTreeSet(other)))

    def __or__(self, other):
        return QuerySet(union(OOTreeSet(self), OOTreeSet(other)))

    def __xor__(self, other):
        return QuerySet(difference(OOTreeSet(self), OOTreeSet(other)))

    def count(self):
        """
        :return: The number of objects in the
            :class:`~sheraf.queryset.QuerySet`, but consumes it.

        >>> with sheraf.connection():
        ...     assert Cowboy.create()
        ...     qs = Cowboy.all()
        ...     assert qs.count() == 1
        ...     assert qs.count() == 0
        """
        return sum(1 for _ in self)

    def __getitem__(self, item):
        self._init_iterator()

        if isinstance(item, slice):
            start, stop, step = item.start, item.stop, item.step
        else:
            start, stop, step = item, item + 1, 1

        if self.model:
            maxid = self.model.count()
        elif isinstance(self._iterable, Sized):
            maxid = len(self._iterable)
        elif (start is None or start >= 0) and (stop is None or stop >= 0):
            maxid = None
        else:
            raise ValueError(
                "When a QuerySet contains an unknown sized object, slicing values must be > 0"
            )

        if maxid:
            if isinstance(item, slice):
                start = item.start
                stop = item.stop
                step = item.step
                if start and start < 0:
                    start %= maxid
                if stop and stop < 0:
                    stop %= maxid
            else:
                start, stop, step = item % maxid, (item % maxid) + 1, 1

        # TODO: Avoid to recreate a QuerySet and avoid itertools.islice
        return QuerySet(itertools.islice(self._iterator, start, stop, step))

    def _init_indexed_iterator(self, filter_name, filter_value, filter_transformation):
        index = self.model.indexes()[filter_name]
        index_values = (
            index.details.search_func(filter_value)
            if filter_transformation
            else [filter_value]
        )

        self._iterator = self.model.read_these_valid(**{filter_name: index_values})

        if not index.details.unique:
            self._iterator = unique_everseen(self._iterator, lambda m: m.identifier)

    def _init_default_iterator(self, reverse=False):
        if not self.model:
            self._iterator = iter(self._iterable)
            return

        indexed_filters = (
            (name, value, transformation)
            for (name, value, transformation) in self.filters.values()
            if name in self.model.indexes()
        )

        for name, value, transformation in indexed_filters:
            self._init_indexed_iterator(name, value, transformation)

            if self._iterator:
                return

        if not self._iterator:
            identifier_index = self.model.indexes()[self.model.primary_key()]
            keys = identifier_index.iterkeys(reverse)
            self._iterator = self.model.read_these(keys)

    def _init_iterator(self):
        # The default sort order is by ascending identifier
        if not self.orders:
            self._init_default_iterator()
            return

        # If there is only one sort option, and it is over the primary key
        # we can use iterators instead of sorting the whole collection.
        if (
            self.model
            and len(self.orders) == 1
            and self.model.primary_key() in self.orders
        ):
            self._init_default_iterator(
                self.orders[self.model.primary_key()] == sheraf.constants.DESC
            )
            return

        # Else we need to sort the collection.
        # So we successively sort the list from the less important
        # order to the most important order.
        if self._iterable is None:
            keys = self.model.indexes()[self.model.primary_key()].iterkeys()
            self._iterable = self.model.read_these(keys)

        for attribute, order in reversed(self.orders.items()):
            self._iterable = sorted(
                self._iterable,
                key=operator.attrgetter(attribute),
                reverse=(order == sheraf.constants.DESC),
            )

        self._iterator = iter(self._iterable)

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

        qs = QuerySet(self._iterable, self.model)
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

        .. note::   Filtering on indexed attributes is more performant than filtering on non-indexed attributes. See :func:`~sheraf.attributes.base.BaseAttribute.index`.
        """
        return self._filter(False, predicate=predicate, **kwargs)

    def search(self, **kwargs):
        """
        Refine a copy of the current :class:`~sheraf.queryset.QuerySet` with further tests.

        This method is very similar to :func:`~sheraf.queryset.QuerySet.filter` except the
        values it takes are transformed with the same way values are transformed at indexation.
        TODO: pas très clair

        For instance, if an attribute indexes its values with a lowercase transformation, the
        :func:`~sheraf.queryset.QuerySet.search` attributes will go through the same
        transformation. Hence it allows to pass uppercase filter values, while
        :func:`~sheraf.queryset.QuerySet.filter` does not allow this.

        >>> class MyCustomModel(sheraf.Model):
        ...     table = "my_custom_model"
        ...     my_attribute = sheraf.SimpleAttribute().index(
        ...        values=lambda string: {string.lower()}
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

    def _filter(self, transformation, predicate=None, **kwargs):
        qs = self.copy()
        if self.model:
            for filter_name in kwargs.keys():
                if (
                    filter_name not in self.model.attributes
                    and filter_name not in self.model.indexes()
                ):
                    raise sheraf.exceptions.InvalidFilterException(
                        "{} has no attribute {}".format(
                            self.model.__name__, filter_name
                        )
                    )
        kwargs_values = OrderedDict(
            {
                filter_name: (filter_name, filter_value, transformation)
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
        ...     peter = Cowboy.create(name="Peter")
        ...     steven = Cowboy.create(name="Steven")
        ...     george = Cowboy.create(name="George")
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

        .. warning:: Arguments order is only kept since ``Python 3.6``, so
            using multiple `order` parameters will result on undefined order
            for ``Python 3.5-``. If you are using ``Python 3.5-`` and need
            several :class:`~sheraf.queryset.QuerySet` orders, prefer chaining
            `order` method calls.

        >>> with sheraf.connection(): # TODO: not skip # doctest: +SKIP
        ...     assert [george, peter, steven] == Cowboy.all().order(age=sheraf.DESC)
        ...     assert [george, steven, peter] == Cowboy.all().order(age=sheraf.DESC) \\
        ...                                                   .order(name=sheraf.ASC)
        >>> # Only since Python 3.6 # doctest: +SKIP
        ... with sheraf.connection():
        ...     assert [george, steven, peter] == Cowboy.all().order(age=sheraf.DESC, name=sheraf.ASC)

        .. note:: Sorting on indexed attributes is more performant than
            sorting on other attributes. See
            :func:`~sheraf.attributes.base.BaseAttribute.index`.
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
                        "{} has no attribute {}".format(self.model.__name__, attribute)
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
                    "Parameter id has an invalid order value {}".format(identifier)
                )

            if self.model.primary_key() in qs.orders:
                raise InvalidOrderException("Id order has been set twice")

            qs.orders[self.model.primary_key()] = identifier

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
        sheraf.exceptions.QuerySetUnpackException: Trying to unpack more than 1 value from a QuerySet
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
            raise sheraf.exceptions.EmptyQuerySetUnpackException(
                "Trying to unpack an empty QuerySet"
            )

        try:
            next(self)
        except StopIteration:
            return element
        else:
            raise sheraf.exceptions.QuerySetUnpackException(
                "Trying to unpack more than 1 value from a QuerySet"
            )

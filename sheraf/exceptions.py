class SherafException(Exception):
    """Main sheraf exception."""

    pass


class ObjectNotFoundException(SherafException):
    """Raised when trying to read an unexisting object."""

    pass


class ModelObjectNotFoundException(ObjectNotFoundException):
    """Raised when trying to read an unexisting :class:`ModelObject`.

    :param model_class: Model class of the unfound object
    :type model_class: sheraf.models.BaseModelMetaclass
    :param object_id: Id of the unfound object
    :type object_id: str
    """

    MESSAGE_TPL = "Id {id} not found in {model_name}"

    def __init__(self, model_class, object_id):
        self.model_class = model_class
        self.object_id = object_id

        model_name = self.model_class.__name__
        message = self.MESSAGE_TPL.format(
            id=repr(self.object_id), model_name=model_name
        )

        super(ModelObjectNotFoundException, self).__init__(message)


class IndexObjectNotFoundException(ObjectNotFoundException):
    """Raised when trying to read an unexisting :class:`IndexObject`.

    :param index: Model Index of the unfound key
    :type index: sheraf.indexes.Index
    :param key: Unfound key
    :type key: str
    :param model_class: Model class of the indexed object
    :type model_class: sheraf.models.BaseModelMetaclass
    """

    MESSAGE_TPL = "Key {key} not found on index {index_name} (model {model_name})"

    def __init__(self, index, key, model_class):
        self.index = index
        self.model_class = model_class
        self.key = key

        model_name = self.model_class.__name__

        _message = self.MESSAGE_TPL.format(
            key=self.key,
            model_name=model_name,
            index_name=self.index.__class__.__name__,
        )
        super(IndexObjectNotFoundException, self).__init__(_message)


class SameNameForTableException(SherafException):
    """Raised when two models have the same "table" attribute.

    >>> class FirstModel(sheraf.Model):
    ...     table = "first_model"
    ...
    >>> class SecondModel(sheraf.Model):
    ...     table = "first_model"
    Traceback (most recent call last):
        ...
    sheraf.exceptions.SameNameForTableException: Table named 'first_model' used twice (FirstModel and SecondModel)
    """


class ConnectionAlreadyOpened(SherafException):
    """Raised when user tries to open an connection when a connection is
    already opened.

    >>> with sheraf.connection():
    ...     with sheraf.connection():
    ...         do_amazing_stuff()
    Traceback (most recent call last):
        ...
    sheraf.exceptions.ConnectionAlreadyOpened: First connection was <Connection at ...> on ... at line ...
    """


class NotConnectedException(SherafException):
    """Raised when trying to handle things in the database while not being
    connected.

    >>> with sheraf.connection():
    ...     sheraf.attempt(do_amazing_stuff)  # produces amazing stuff
    ...
    >>> sheraf.attempt(do_amazing_stuff)
    Traceback (most recent call last):
        ...
    sheraf.exceptions.NotConnectedException
    """


class InvalidFilterException(SherafException):
    """Raised when an invalid :class:`~sheraf.queryset.QuerySet` filter has been
    called.

    >>> class MyModel(sheraf.Model):
    ...    my_attribute = sheraf.SimpleAttribute()
    ...
    >>> with sheraf.connection():
    ...    MyModel.filter(foobar=True)
    Traceback (most recent call last):
        ...
    sheraf.exceptions.InvalidFilterException: MyModel has no attribute foobar
    """


class InvalidOrderException(SherafException):
    """Raised when an invalid :class:`~sheraf.queryset.QuerySet` order has been
    called.

    >>> class MyModel(sheraf.Model):
    ...    table = "my_model"
    ...    my_attribute = sheraf.SimpleAttribute()
    ...
    >>> with sheraf.connection():
    ...    MyModel.all().order(foobar=True)
    Traceback (most recent call last):
        ...
    sheraf.exceptions.InvalidOrderException: MyModel has no attribute foobar
    >>> with sheraf.connection():
    ...    MyModel.all().order(my_attribute=sheraf.ASC) \\
    ...                 .order(my_attribute=sheraf.DESC)  # Raises an InvalidOrderException
    Traceback (most recent call last):
        ...
    sheraf.exceptions.InvalidOrderException: Some order parameters appeared twice
    """


class QuerySetUnpackException(SherafException):
    """Raised when calling :func:`~sheraf.queryset.QuerySet.get` on
    :class:`~sheraf.queryset.QuerySet` containing invalid number of elements.

    >>> class Cowboy(sheraf.Model):
    ...     table = "people"
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> with sheraf.connection():
    ...     peter = Cowboy.create(name="Peter")
    ...
    ...     assert peter == Cowboy.filter(name="Peter").get()
    ...
    >>> # Fails with too many values
    ... with sheraf.connection():
    ...     Cowboy.create(name="Peter")
    ...     Cowboy.create(name="Steven")
    ...     Cowboy.all().get()
    Traceback (most recent call last):
        ...
    sheraf.exceptions.QuerySetUnpackException: Trying to unpack more than 1 value from a QuerySet
    """


class EmptyQuerySetUnpackException(QuerySetUnpackException):
    """Raised when calling :func:`~sheraf.queryset.QuerySet.get` on
    :class:`~sheraf.queryset.QuerySet` containing 0 element.

    >>> # Fails with zero value
    ... with sheraf.connection():
    ...     Cowboy.filter(name="unknown cowboy").get()
    Traceback (most recent call last):
    ...
    sheraf.exceptions.EmptyQuerySetUnpackException: Trying to unpack an empty QuerySet
    """

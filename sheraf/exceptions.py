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

    MESSAGE_TPL = "Key {identifier} not found in {model_name}, '{index_name}' index"

    def __init__(self, model_class, identifier, index_name=None):
        self.model_class = model_class
        self.identifier = identifier
        index_name = index_name or model_class.primary_key()

        message = self.MESSAGE_TPL.format(
            identifier=repr(identifier),
            model_name=self.model_class.__name__,
            index_name=index_name,
        )

        super().__init__(message)


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
    >>> sheraf.commit()
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
    def __init__(self, message=None, queryset=None):
        self.queryset = queryset
        super().__init__(message)


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

    def __init__(self, message=None, queryset=None):
        if not message:
            message = "Trying to unpack an empty QuerySet"
            if queryset:
                message += " " + repr(queryset)

        super().__init__(message, queryset)


class TooManyValuesSetUnpackException(QuerySetUnpackException):
    """Raised when calling :func:`~sheraf.queryset.QuerySet.get` on
    :class:`~sheraf.queryset.QuerySet` containing more than one element.

    >>> # Fails with zero value
    ... with sheraf.connection():
    ...     Cowboy.filter(name="unknown cowboy").get()
    Traceback (most recent call last):
    ...
    sheraf.exceptions.EmptyQuerySetUnpackException: Trying to unpack a QuerySet with multiple elements
    """

    def __init__(self, message=None, queryset=None):
        if not message:
            message = "Trying to unpack a QuerySet with multiple elements"
            if queryset:
                message += " " + repr(queryset)

        super().__init__(message, queryset)


class InvalidIndexException(SherafException):
    """
    This exception is raised by :func:`~sheraf.models.BaseModel.read` and
    :func:`~sheraf.models.BaseModel.read_these` when a parameter is passed
    and is not a valid index.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     age = sheraf.IntegerAttribute().index()
    ...
    >>> with sheraf.connection():
    ...     Cowboy.read(size=4)
    Traceback (most recent call last):
    ...
    sheraf.exceptions.InvalidIndexException: 'size' is not a valid index
    """


class UniqueIndexException(InvalidIndexException):
    """
    This exception is raised when a value is set twice in an unique index.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute().index(unique=True)
    ...
    >>> with sheraf.connection():
    ...     Cowboy.create(name="George Abitbol")
    ...     Cowboy.create(name="George Abitbol")
    Traceback (most recent call last):
    ...
    sheraf.exceptions.UniqueIndexException: The key 'George Abitbol' is already present in the index 'name'
    """


class MultipleIndexException(InvalidIndexException):
    """
    This exception is raised by :func:`~sheraf.models.BaseModel.read` when a
    multiple index is passed as a positionnal argument.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     hobby = sheraf.StringAttribute().index()
    ...
    >>> with sheraf.connection():
    ...     Cowboy.create(name="George", hobby="nice hats")
    ...     Cowboy.create(name="Peter", hobby="nice hats")
    ...     Cowboy.read(hobby="nice hats")
    Traceback (most recent call last):
    ...
    sheraf.exceptions.MultipleIndexException: 'hobby' is a multiple index and cannot be used with 'read'
    """


class IndexationWarning(UserWarning):
    """
    This warning is emitted when you edit or create a model instance which has an outdated
    indexation table.
    """


class PrimaryKeyException(SherafException):
    """
    This exception is raised when issues happens with index primary keys.

    When creating a model with zero, or several primary indexes.

    >>> class Horse(sheraf.AttributeModel):
    ...     name = sheraf.StringAttribute().index(primary=True)
    ...     breed = sheraf.StringAttribute().index(primary=True)
    ...
    >>> class Cowboy(sheraf.Model):
    ...     name = sheraf.StringAttribute()
    ...     horses = sheraf.IndexedModelAttribute(Horse)
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(name="George Abitbol")
    ...     george.horses.create(name="Jolly Jumper", breed="shetland")
    Traceback (most recent call last):
    ...
    sheraf.exceptions.PrimaryKeyException: "A model can have only one primary key. 'Horse' has 'name' and 'breed'"
    """


class NoDatabaseConnectionException(SherafException):
    """
    Raised when calling :func:`~sheraf.Model.read` and there is no connection to the database specified by the attribute `database_name`.
    """

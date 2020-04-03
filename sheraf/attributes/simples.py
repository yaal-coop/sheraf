import datetime
import uuid
from numbers import Integral
from BTrees.LOBTree import LOBTree

from sheraf.attributes.base import BaseAttribute


class SimpleAttribute(BaseAttribute):
    """Store a primitive data.

    The value can be a :class:`bool`, :class:`str`, :class:`int`,
    :class:`float`.
    """


class TypedAttribute(BaseAttribute):
    """Store a persistent dict of primitive data.

    Keys and values can be :class:`str`, :class:`int`, :class:`float`.
    """

    type = object

    def __init__(self, **kwargs):
        kwargs.setdefault("default", self.type)
        super().__init__(**kwargs)

    def serialize(self, value):
        return self.type(value)


class BooleanAttribute(TypedAttribute):
    """Store a :class:`bool` object."""

    type = bool


class IntegerAttribute(TypedAttribute):
    """Stores an :class:`int` object."""

    type = int
    default_index_mapping = LOBTree


class FloatAttribute(TypedAttribute):
    """Stores a :class:`float` object."""

    type = float


class StringAttribute(TypedAttribute):
    """Stores a :class:`str` object."""

    type = "".__class__


class UUIDAttribute(BaseAttribute):
    """Stores an :class:`uuid.UUID`."""

    def serialize(self, value):
        if value is None:
            return None

        if isinstance(value, Integral):
            return uuid.UUID(int=value).int

        if isinstance(value, (bytes, str, "".__class__)):
            return uuid.UUID(value).int

        return value.int

    def deserialize(self, value):
        if value:
            return uuid.UUID(int=value)
        return None


class StringUUIDAttribute(UUIDAttribute):
    """Stores an :class:`uuid.UUID` but data is handled as a string."""

    def deserialize(self, value):
        uuid = super().deserialize(value)
        if uuid is None:
            return None
        return str(uuid)


class DateTimeAttribute(BaseAttribute):
    """Store a :class:`datetime.datetime` object."""

    def deserialize(self, value):
        if value is None:
            return None

        return datetime.datetime.utcfromtimestamp(value)

    def datetime_to_timestamp(self, date):
        return (date - datetime.datetime(1970, 1, 1)).total_seconds()

    def serialize(self, value):
        if value is None:
            db_value = None

        else:
            value = value.replace(tzinfo=None)
            db_value = self.datetime_to_timestamp(value)

        return db_value


class TimeAttribute(IntegerAttribute):
    """Stores a :class:`datetime.time` object."""

    def __init__(self, default=None, **kwargs):
        super().__init__(default=default, **kwargs)

    def deserialize(self, value):
        if value == -1:
            return None

        seconds = value // 1000000
        microseconds = value % 1000000
        dt = datetime.datetime(1970, 1, 1) + datetime.timedelta(
            seconds=seconds, microseconds=microseconds
        )
        return dt.time()

    def serialize(self, value):
        if value is None:
            return -1

        dt = datetime.datetime(
            1970, 1, 1, value.hour, value.minute, value.second, value.microsecond
        )
        epoch = datetime.datetime(1970, 1, 1)
        delta = dt - epoch
        intvalue = delta.seconds * 1000000 + delta.microseconds
        return intvalue


class DateAttribute(IntegerAttribute):
    """Stores a :class:`datetime.date` object."""

    def __init__(self, default=None, **kwargs):
        super().__init__(default=default, **kwargs)

    def deserialize(self, value):
        if value == -1:
            return None

        return datetime.date(1970, 1, 1) + datetime.timedelta(days=value)

    def serialize(self, value):
        if value is None:
            return -1

        intvalue = (value - datetime.date(1970, 1, 1)).days
        return intvalue

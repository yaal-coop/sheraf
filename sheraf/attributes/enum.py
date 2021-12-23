import sheraf


class EnumAccessor:
    def __init__(self, enum):
        self.enum = enum

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            if (
                name.startswith("is_")
                and name.upper()[3:] in self.enum.__class__.__members__
            ):
                return self.value == self.enum.__class__.__members__[name.upper()[3:]]
            return getattr(self.enum, name)

    def __eq__(self, other):
        return self.enum.value == other

    def __lt__(self, other):
        if isinstance(other, EnumAccessor):
            return self.enum.value < other.value
        return self.enum.value < other

    def __le__(self, other):
        if isinstance(other, EnumAccessor):
            return self.enum.value <= other.value
        return self.enum.value <= other

    def __gt__(self, other):
        if isinstance(other, EnumAccessor):
            return self.enum.value > other.value
        return self.enum.value > other

    def __ge__(self, other):
        if isinstance(other, EnumAccessor):
            return self.enum.value >= other.value
        return self.enum.value >= other

    def __hash__(self):
        return hash(self.enum)

    def __str__(self):
        return str(self.enum.value)

    def __repr__(self):
        return repr(self.enum)


class EnumAttribute(sheraf.Attribute):
    """
    Takes an :class:`~enum.Enum` and an optional :class:`~sheraf.attributes.Attribute`, filters the data with the :class:`~enum.Enum` and serialize it with the methods of the :class:`~sheraf.attributes.Attribute`.

    >>> import enum
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "enum_cowboys"
    ...
    ...     class Status(enum.IntEnum):
    ...         FARMER = 0
    ...         COWBOY = 1
    ...         SHERIF = 2
    ...
    ...     status = sheraf.EnumAttribute(Status, sheraf.IntegerAttribute())
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(status=Cowboy.Status.SHERIF)
    ...
    ...     assert george.status == 2
    ...     assert george.status == Cowboy.Status.SHERIF

    .. note :: For every value ``FOOBAR`` defined in the enum, the attributes
               defines an accessor ``is_foobar``.

    >>> with sheraf.connection(commit=True):
    ...     assert george.status.is_sherif
    ...     assert not george.status.is_farmer
    """

    def __init__(self, enum, attribute=None, **kwargs):
        self.attribute = attribute or sheraf.Attribute
        self.enum = enum
        super().__init__(**kwargs)

    def serialize(self, value):
        if value is None:
            return None

        if not isinstance(value, EnumAccessor):
            value = self.attribute.serialize(value)

        enum_value = self.enum(value).value
        return self.attribute.serialize(enum_value)

    def deserialize(self, value):
        if value is None:
            return None

        data = self.attribute.deserialize(value)
        return EnumAccessor(self.enum(data))

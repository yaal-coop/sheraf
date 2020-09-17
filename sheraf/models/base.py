import sheraf.types


class BaseModelMetaclass(type):
    """
    Internal metaclass.
    Contains the mapping of attribute names with their corresponding data (of type :class:`~sheraf.attributes.BaseAttribute`)
    """

    def __new__(cls, name, bases, attrs):
        klass = super().__new__(cls, name, bases, attrs)
        klass.attributes = {}

        for name, attr in attrs.items():
            if not isinstance(attr, sheraf.attributes.base.BaseAttribute):
                continue

            try:
                attr.set_default_key(klass.attribute_id(name, attr))
            except NotImplementedError:
                continue

            klass.attributes[name] = attr

        for _base in bases:
            base_attributes = {}
            base_attributes.update(_base.__dict__.get("attributes", {}))
            base_attributes.update(_base.__dict__)
            for name, attr in base_attributes.items():
                if not isinstance(attr, sheraf.attributes.base.BaseAttribute):
                    continue

                if name in klass.attributes:
                    continue

                try:
                    attr.set_default_key(klass.attribute_id(name, attr))
                except NotImplementedError:
                    continue

                klass.attributes[name] = attr

        return klass


class BaseModel(object, metaclass=BaseModelMetaclass):
    """
    :class:`~sheraf.models.base.BaseModel` is the base class for every other model classes.
    This is where the attribute reading and writing are handled.

    Models can be used as dictionaries:

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> with sheraf.connection(): # doctest: +SKIP
    ...     dict(Cowboy.create(name="George Abitbol"))
    {'name': 'George Abitbol', '_creation': ...}
    """

    attributes = {}
    mapping = None
    default_mapping = sheraf.types.SmallDict

    @classmethod
    def create(cls, default=None, *args, **kwargs):
        """Create a model instance.

        :param default: The data structure that will be used to store the instance state.
        :param \\*\\*kwargs: Any model attribute can be initialized with the matching keyword.

        :return: The newly created instance.

        >>> class Cowboy(sheraf.Model):
        ...    table = "cowboy"
        ...    name = sheraf.SimpleAttribute(default="John Doe")
        ...
        >>> with sheraf.connection(commit=True):
        ...    cowboy = Cowboy.create()
        ...    assert "John Doe" == cowboy.name
        ...
        ...    cowboy = Cowboy.create(name="George Abitbol")
        ...    assert "George Abitbol" == cowboy.name
        ...
        ...    Cowboy.create(this_attribute_does_not_exist="something") #  raises a TypeError
        Traceback (most recent call last):
            ...
        TypeError: TypeError: create() got an unexpected keyword argument 'this_attribute_does_not_exist'

        The function can also create sub-instances recursively:

        >>> class Horse(sheraf.InlineModel):
        ...     name = sheraf.SimpleAttribute()
        ...
        >>> class Cowboy(sheraf.Model):
        ...     table = "cowboy"
        ...     name = sheraf.SimpleAttribute(default="John Doe")
        ...     horse = sheraf.InlineModelAttribute(Horse)
        ...
        >>> with sheraf.connection():
        ...     cowboy = Cowboy.create(name="George Abitbol", horse={"name": "Jolly Jumper"})
        ...     cowboy.horse.name
        'Jolly Jumper'
        """
        mapping = (default or cls.default_mapping)()
        instance = cls._decorate(mapping)
        instance.initialize(*args, **kwargs)
        return instance

    def initialize(self, *args, **kwargs):
        for attribute, value in kwargs.items():
            if attribute not in self.attributes:
                raise TypeError(
                    "TypeError: create() got an unexpected keyword argument '{}'".format(
                        attribute
                    )
                )
            self.__setattr__(attribute, value)

        for name, attribute in self.attributes.items():
            if not attribute.lazy and name not in kwargs:
                self.__setattr__(name, attribute.create(self))

    @classmethod
    def _decorate(cls, mapping):
        instance = cls()
        instance.mapping = mapping
        return instance

    @classmethod
    def attribute_id(cls, name, attribute):
        raise NotImplementedError

    def __setattr__(self, name, value):
        if name not in self.attributes:
            super().__setattr__(name, value)
            return

        value = self.attributes[name].write(self, value)
        if self.attributes[name].write_memoization:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if name in self.attributes:
            self.attributes[name].delattr(self)
            try:
                super().__delattr__(name)
            except AttributeError:
                return
        else:
            super().__delattr__(name)

    def __getattribute__(self, name):
        # TODO: Find a way to check that self.name exists or not without
        # using try/except AttributeError.
        # Because if a @property of this class, called `name` also raises
        # an AttributeError, actually we cannot say from where the AttributeError
        # was emitted.

        try:
            attribute = super().__getattribute__(name)
            if not isinstance(attribute, sheraf.attributes.base.BaseAttribute):
                return attribute

        except AttributeError as exc:
            if "object has no attribute '{}'".format(name) not in str(exc):
                raise

        try:
            attribute = self.attributes[name]
        except KeyError:
            raise AttributeError(name)

        value = attribute.read(self)

        if self.attributes[name].read_memoization:
            super().__setattr__(name, value)

        return value

    def copy(self, **kwargs):
        r"""
        :param \*\*kwargs: Keywords arguments will be passed to
                           :func:`~sheraf.models.BaseModel.create` and thus
                           wont be copied.

        :return: a copy of this instance.
        """
        copy = self.__class__.create(**kwargs)
        for name, attr in self.attributes.items():
            if attr.is_created(self) and name not in kwargs:
                setattr(copy, name, getattr(self, name))
        return copy

    def keys(self):
        """
        :return: The instance attribute names.
        """
        return self.attributes.keys()

    def items(self):
        return (
            (key, self.attributes[key].read(self)) for key in self.attributes.keys()
        )

    def update(self, **kwargs):
        """Takes an arbitrary number of keywords arguments, and updates the
        instance attributes matching the arguments.

        This functions recursively calls :func:`sheraf.attributes.base.BaseAttribute.edit` with `addition` and `edition` to `True`.

        >>> class Horse(sheraf.InlineModel):
        ...     name = sheraf.SimpleAttribute()
        ...
        >>> class Cowboy(sheraf.Model):
        ...     table = "people"
        ...     name = sheraf.SimpleAttribute()
        ...     horse = sheraf.InlineModelAttribute(Horse)
        ...
        >>> with sheraf.connection(commit=True):
        ...     george = Cowboy.create(name="George", horse={"name": "Centaurus"})
        ...     george.update(name="*incognito*", horse={"name": "Jolly Jumper"})
        ...     george.name
        '*incognito*'
        >>> with sheraf.connection():
        ...     george.horse.name
        'Jolly Jumper'

        Note that sub-instances are also edited.
        """
        self.edit(
            kwargs, addition=True, edition=True, deletion=False, replacement=False
        )

    def assign(self, **kwargs):
        """Takes an arbitrary number of keywords arguments, and updates the
        instance attributes matching the arguments.

        This functions recursively calls :func:`sheraf.attributes.base.BaseAttribute.edit` with `addition`, `edition` and `deletion` to `True`.

        >>> class Arm(sheraf.InlineModel):
        ...     name = sheraf.SimpleAttribute()
        ...
        >>> class Cowboy(sheraf.Model):
        ...     table = "people"
        ...     name = sheraf.SimpleAttribute()
        ...     arms = sheraf.SmallListAttribute(sheraf.InlineModelAttribute(Arm))
        ...
        >>> with sheraf.connection(commit=True):
        ...     george = Cowboy.create(name="Three arms cowboy", arms=[
        ...         {"name": "Arm 1"}, {"name": "Arm 2"}, {"name": "Arm 3"},
        ...     ])
        ...     len(george.arms)
        3
        >>> with sheraf.connection(commit=True):
        ...     george.assign(name="George Abitbol", arms=[
        ...         {"name": "Superarm 1"}, {"name": "Superarm 2"},
        ...     ])
        ...     len(george.arms)
        2
        >>> with sheraf.connection():
        ...     george.arms[0].name
        'Superarm 1'

        George passed from 3 arms to only 2 because *assign* does remove sub instances. If we had called :func:`~sheraf.models.base.BaseModel.update` instead,
        George would have his two first arms be renamed *superarms* but, the third one would not have been removed.
        """
        self.edit(kwargs, addition=True, edition=True, deletion=True, replacement=False)

    def edit(
        self, value, addition=True, edition=True, deletion=False, replacement=False
    ):
        """Take a dictionary and a set of options, and try to applies the
        dictionary values to the instance structure.

        :param value: The dictionary containing the values. The dictionary elements that
                      do not match the instance attributes will be ignored.
        :param addition: If *True*, elements present in *value* and absent from the instance attributes will be added.
        :param edition: If *True*, elements present in both *value* and the instance will be updated.
        :param deletion: If *True*, elements present in the instance and absent from *value* will be deleted.
        :param replacement: Like *edition*, but create a new element instead of updating one.
        """
        try:
            for attr, new_value in value.items():
                old_value = self.attributes[attr].read(self)
                updated = self.attributes[attr].update(
                    old_value, new_value, addition, edition, deletion, replacement
                )
                self.__setattr__(attr, updated)
        except KeyError:
            raise TypeError(
                "TypeError: edit() got an unexpected keyword argument '{}'".format(attr)
            )
        return self

    def save(self):
        for attr in self.attributes.values():
            attr.save(self)
        return self

    def reset(self, attribute):
        """
        Resets an attribute to its default value.
        """
        self.__setattr__(attribute, self.attributes[attribute].create(self))

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return (
            hasattr(self, "mapping")
            and hasattr(other, "mapping")
            and self.mapping == other.mapping
        )

    def __getitem__(self, key):
        return self.attributes[key].read(self)

    def __setitem__(self, key, value):
        value = self.attributes[key].write(self, value)
        super().__setattr__(key, value)

    def __contains__(self, key):
        return key in self.attributes

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)

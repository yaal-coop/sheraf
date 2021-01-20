"""Collection attributes are attributes that behave like native python
collections such as :class:`dict`, :class:`list` or :class:`set`. They usually
combine different objects:

- A ``persistent_type`` that is the persistent data structure that will store
  the data in ZODB. For instance
  :class:`~sheraf.attributes.collections.ListAttribute` usually uses
  :class:`sheraf.types.SmallList` or :class:`~sheraf.types.largelist.LargeList`.

- An ``accessor_type`` that helps handling the ``persistent_type`` with an
  interface similar to the native type it refers. For instance
  :class:`~sheraf.attributes.collections.ListAttribute` uses
  :class:`~sheraf.attributes.collections.ListAccessor` that behaves like the
  python :class:`list`.

- An optional ``attribute`` that helps the ``accessor_type`` serialize and
  deserialize the data stored in the ``persistent_type``. This allows pairing
  collections with other kinds of attributes. For example you can easilly
  handle :class:`~sheraf.attribute.blobs.Blob` lists or dictionaries of
  :class:`~sheraf.attributes.models.InlineModelAttributes`.

>>> class Horse(sheraf.InlineModel):
...     table = "horse"
...     name = sheraf.SimpleAttribute()
...
>>> class Cowboy(sheraf.Model):
...     table = "cowboy"
...     name = sheraf.SimpleAttribute()
...     favorite_numbers = sheraf.SmallListAttribute(
...         sheraf.IntegerAttribute(),
...     )
...     horses = sheraf.LargeDictAttribute(
...         sheraf.InlineModelAttribute(Horse),
...     )
...
>>> with sheraf.connection(commit=True):
...     george = Cowboy.create(
...         name="George Abitbol",
...         favorite_numbers=[1, 13, 21, 34],
...         horses = {
...             "first": {"name": "Jolly Jumper"},
...             "second": {"name": "Polly Pumper"},
...         },
...     )
...
...     assert 21 in george.favorite_numbers
...     assert "Jolly Jumper" == george.horses["first"].name

You can also nest collections as you like, and play for instance with
:class:`~sheraf.attributes.collections.DictAttribute` or
:class:`~sheraf.attributes.collections.ListAttribute`.

>>> class Cowboy(sheraf.Model):
...     table = "cowboy"
...     name = sheraf.SimpleAttribute()
...     dice_results = sheraf.LargeDictAttribute(
...         sheraf.SmallListAttribute(
...             sheraf.IntegerAttribute()
...         )
...     )
...
>>> with sheraf.connection(commit=True):
...     george = Cowboy.create(
...         name="George Abitbol",
...         dice_results={
...             "monday": [2, 6, 4],
...             "tuesday": [1, 1, 3],
...         }
...     )
...     assert 6 == george.dice_results["monday"][1]
"""


import sheraf
import sheraf.types


class ListAttributeAccessor:
    def __init__(self, attribute, persistent):
        self._attribute = attribute
        self.mapping = persistent

    def __iter__(self):
        return (self._attribute.deserialize(item) for item in self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __bool__(self):
        return bool(self.mapping)

    def __setitem__(self, key, value):
        if key >= len(self.mapping) or key < 0:
            raise IndexError("list index out of range")

        self.mapping[key] = self._attribute.serialize(value)

    def __getitem__(self, key):
        if not isinstance(key, slice):
            return self._attribute.deserialize(self.mapping[key])

        return (
            self._attribute.deserialize(item) for item in self.mapping.__getitem__(key)
        )

    def append(self, item):
        self.mapping.append(self._attribute.serialize(item))

    def clear(self):
        self.mapping.clear()

    def extend(self, iterable):
        self.mapping.extend(self._attribute.serialize(item) for item in iterable)

    def pop(self):
        return self._attribute.deserialize(self.mapping.pop())

    def remove(self, item):
        self.mapping.remove(self._attribute.serialize(item))


class ListAttribute(sheraf.attributes.base.BaseAttribute):
    """Attribute mimicking the behavior of :class:`list`.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     faxes = sheraf.LargeListAttribute(
    ...         sheraf.BlobAttribute()
    ...     )
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(
    ...         name="George Abitbol",
    ...         faxes=[
    ...             sheraf.Blob.create(filename="peter1.txt", data=b"Can you give me my pin's back please?"),
    ...         ],
    ...     )
    ...
    ...     george.faxes.append(sheraf.Blob.create(filename="peter2.txt", data=b"Hey! Did you receive my last fax?"))
    ...     assert "peter1.txt" == george.faxes[0].original_name
    ...     assert b"fax" in george.faxes[1].data
    ...
    """

    def __init__(
        self,
        attribute=None,
        persistent_type=None,
        accessor_type=ListAttributeAccessor,
        **kwargs
    ):
        assert persistent_type is not None

        self.attribute = attribute
        self.persistent_type = persistent_type
        self.accessor_type = accessor_type
        kwargs.setdefault("default", self.persistent_type)
        super().__init__(**kwargs)

    def values(self, list_):
        """
        By default, every items in a :class:`~sheraf.attributes.collections.ListAttribute` is indexed.

        >>> class Cowboy(sheraf.Model):
        ...     table = "cowboy"
        ...     favorite_colors = sheraf.LargeListAttribute(
        ...         sheraf.StringAttribute()
        ...     ).index()
        ...
        >>> with sheraf.connection():
        ...     george = Cowboy.create(favorite_colors=[
        ...         "red", "green", "blue",
        ...     ])
        ...     assert george in Cowboy.search(favorite_colors="red")
        ...     assert george in Cowboy.search(favorite_colors="blue")
        ...     assert george not in Cowboy.search(favorite_colors="yellow")

        .. warning :: A current limitation is that indexed lists won't update their
                      indexes if they are edited through their accessor. For the indexes
                      to be updated, the whole list must be re-assigned.

        >>> with sheraf.connection():
        ...     george.favorite_colors.append("purple")
        ...     george in Cowboy.search(favorite_colors="purple")
        False
        >>> with sheraf.connection():
        ...     george.favorite_colors = list(george.favorite_colors) + ["purple"]
        ...     george in Cowboy.search(favorite_colors="purple")
        True
        """

        if not self.attribute:
            return set(list_)

        return set(y for v in list_ for y in self.attribute.values(v))

    def search(self, value):
        if not self.attribute:
            return {value}

        return {v for v in self.attribute.search(value)}

    def deserialize(self, value):
        if not self.attribute:
            return value

        return self.accessor_type(attribute=self.attribute, persistent=value)

    def serialize(self, value):
        if not self.attribute:
            return self.persistent_type(value or [])

        if value is None:
            return self.persistent_type()

        write = self.persistent_type()

        for v in value:
            write.append(self.attribute.serialize(v))

        return write

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        if addition and len(new_value) > len(old_value):
            for item in new_value[len(old_value) :]:
                if self.attribute:
                    old_value.append(self.attribute.serialize(item))
                else:
                    old_value.append(item)

        if edition or replacement:
            for i, (_, item) in enumerate(zip(old_value, new_value)):
                if self.attribute:
                    old_value[i] = self.attribute.update(
                        old_value[i], item, addition, edition, deletion, replacement
                    )

                else:
                    old_value[i] = item

        if deletion and len(old_value) > len(new_value):
            while len(old_value) > len(new_value):
                old_value.pop()

        return old_value


class SmallListAttribute(ListAttribute):
    """Shortcut for ``ListAttribute(persistent_type=SmallList)``."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, persistent_type=sheraf.types.SmallList, **kwargs)


class LargeListAttribute(ListAttribute):
    """Shortcut for ``ListAttribute(persistent_type=LargeList)``."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, persistent_type=sheraf.types.LargeList, **kwargs)


class DictAttributeAccessor:
    def __init__(self, attribute, persistent, **kwargs):
        self._attribute = attribute
        self.mapping = persistent

    def __setitem__(self, key, value):
        self.mapping[key] = self._attribute.serialize(value)

    def __getitem__(self, key):
        return self._attribute.deserialize(self.mapping[key])

    def __delitem__(self, key):
        del self.mapping[key]

    def __iter__(self):
        return (k for k in self.mapping.keys())

    def __bool__(self):
        return bool(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __contains__(self, key):
        return key in self.mapping

    def clear(self):
        self.mapping.clear()

    def keys(self, *args, **kwargs):
        return self.mapping.keys(*args, **kwargs)

    def items(self, *args, **kwargs):
        if not hasattr(self.mapping, "iteritems"):
            return (
                (k, self._attribute.deserialize(v))
                for k, v in iter(self.mapping.items())
            )

        return (
            (k, self._attribute.deserialize(v))
            for k, v in self.mapping.iteritems(*args, **kwargs)
        )

    def values(self, *args, **kwargs):
        if not hasattr(self.mapping, "iteritems"):
            return (
                self._attribute.deserialize(v) for k, v in iter(self.mapping.items())
            )

        return (
            self._attribute.deserialize(v)
            for k, v in self.mapping.iteritems(*args, **kwargs)
        )

    def get(self, value, default=None):
        value = self.mapping.get(value)
        if value is None:
            return default
        return self._attribute.deserialize(value)

    def maxKey(self):
        try:
            return self.mapping.maxKey()
        except AttributeError:
            return max(self.mapping.keys())

    def minKey(self):
        try:
            return self.mapping.minKey()
        except AttributeError:
            return min(self.mapping.keys())

    def update(self, other):
        for k, v in other.items():
            self[k] = v


class DictAttribute(sheraf.attributes.base.BaseAttribute):
    """Attribute mimicking the behavior of :class:`dict`.

    >>> class Gun(sheraf.InlineModel):
    ...     nb_amno = sheraf.IntegerAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     guns = sheraf.LargeDictAttribute(
    ...         sheraf.InlineModelAttribute(Gun)
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...    george = Cowboy.create(
    ...        name="George Abitbol",
    ...        guns={
    ...            "rita": {"nb_amno": 6},
    ...            "carlotta": {"nb_amno": 5},
    ...        }
    ...    )
    ...
    ...    assert george.guns["rita"].nb_amno == 6
    ...    for gun in george.guns.values():
    ...        assert gun.nb_amno >= 5
    """

    def __init__(
        self,
        attribute=None,
        persistent_type=None,
        accessor_type=DictAttributeAccessor,
        **kwargs
    ):
        assert persistent_type is not None
        self.attribute = attribute
        self.persistent_type = persistent_type
        self.accessor_type = accessor_type
        kwargs.setdefault("default", self.persistent_type)
        super().__init__(**kwargs)

    def deserialize(self, value):
        if not self.attribute:
            return value

        return self.accessor_type(attribute=self.attribute, persistent=value)

    def serialize(self, value):
        if not self.attribute:
            return self.persistent_type(value or {})

        if value is None:
            return self.persistent_type()

        return self.persistent_type(
            {k: self.attribute.serialize(m) for k, m in value.items()}
        )

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        if addition:
            for k in new_value.keys() - old_value.keys():
                if self.attribute:
                    old_value[k] = self.attribute.serialize(new_value[k])
                else:
                    old_value[k] = new_value[k]

        if edition or replacement:
            for k in old_value.keys() & new_value.keys():
                if self.attribute:
                    old_value[k] = self.attribute.update(
                        old_value[k],
                        new_value[k],
                        addition,
                        edition,
                        deletion,
                        replacement,
                    )

                else:
                    old_value[k] = new_value[k]

        if deletion:
            for k in old_value.keys() - new_value.keys():
                del old_value[k]

        return old_value


class LargeDictAttribute(DictAttribute):
    """Shortcut for ``DictAttribute(persistent_type=LargeDict)``"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, persistent_type=sheraf.types.LargeDict, **kwargs)


class SmallDictAttribute(DictAttribute):
    """Shortcut for ``DictAttribute(persistent_type=SmallDict)``"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, persistent_type=sheraf.types.SmallDict, **kwargs)


class SetAttributeAccessor:
    def __init__(self, attribute, persistent, **kwargs):
        self._attribute = attribute
        self.mapping = persistent

    def add(self, item):
        self.mapping.add(self._attribute.serialize(item))

    def remove(self, item):
        self.mapping.remove(self._attribute.serialize(item))

    def __and__(self, item):
        return set(item) & set(self)

    def __or__(self, item):
        return set(item) | set(self)

    def __xor__(self, item):
        return set(item) ^ set(self)

    def __rand__(self, item):
        return set(item) & set(self)

    def __ror__(self, item):
        return set(item) | set(self)

    def __rxor__(self, item):
        return set(item) ^ set(self)

    def __iter__(self):
        return (self._attribute.deserialize(item) for item in self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __contains__(self, item):
        return item in iter(self)

    def clear(self):
        self.mapping.clear()


class SetAttribute(sheraf.attributes.simples.TypedAttribute):
    """Attribute mimicking the behavior of :class:`set`.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     favorite_numbers = sheraf.SetAttribute(
    ...         sheraf.IntegerAttribute()
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...    george = Cowboy.create(
    ...        name="George Abitbol",
    ...        favorite_numbers={1, 8, 13}
    ...    )
    ...
    ...    assert 13 in george.favorite_numbers
    ...    george.favorite_numbers.add(8)
    ...    assert {1, 8, 13} == set(george.favorite_numbers)
    """

    def __init__(
        self,
        attribute=None,
        persistent_type=sheraf.types.Set,
        accessor_type=SetAttributeAccessor,
        **kwargs
    ):
        assert persistent_type is not None
        self.attribute = attribute
        self.persistent_type = persistent_type
        self.accessor_type = accessor_type
        kwargs.setdefault("default", self.persistent_type)
        super().__init__(**kwargs)

    def values(self, set_):
        """
        By default, every items in a :class:`~sheraf.attributes.collections.SetAttribute` is indexed.

        >>> class Cowboy(sheraf.Model):
        ...     table = "cowboy"
        ...     favorite_colors = sheraf.SetAttribute(
        ...         sheraf.StringAttribute()
        ...     ).index()
        ...
        >>> with sheraf.connection():
        ...     george = Cowboy.create(favorite_colors={
        ...         "red", "green", "blue",
        ...     })
        ...     assert george in Cowboy.search(favorite_colors="red")
        ...     assert george in Cowboy.search(favorite_colors="blue")
        ...     assert george not in Cowboy.search(favorite_colors="yellow")

        .. warning :: A current limitation is that indexed sets won't update their
                      indexes if they are edited through their accessor. For the indexes
                      to be updated, the whole set must be re-assigned.

        >>> with sheraf.connection():
        ...     george.favorite_colors.add("purple")
        ...     george in Cowboy.search(favorite_colors="purple")
        False
        >>> with sheraf.connection():
        ...     george.favorite_colors = set(george.favorite_colors) | {"purple"}
        ...     george in Cowboy.search(favorite_colors="purple")
        True
        """

        if not self.attribute:
            return set(set_)

        return set(y for v in set_ for y in self.attribute.values(v))

    def search(self, value):
        if not self.attribute:
            return {value}

        return {v for v in self.attribute.search(value)}

    def deserialize(self, value):
        if not self.attribute:
            return value

        return self.accessor_type(attribute=self.attribute, persistent=value)

    def serialize(self, value):
        if not self.attribute:
            return self.persistent_type(value or {})

        if value is None:
            return self.persistent_type()

        return self.persistent_type(self.attribute.serialize(item) for item in value)

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        if addition:
            for item in new_value & (new_value ^ old_value):
                old_value.add(item)

        if deletion:
            for item in old_value & (old_value ^ new_value):
                old_value.remove(item)

        return old_value

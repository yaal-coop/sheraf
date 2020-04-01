import BTrees.Length

import sheraf.types.counter
from sheraf.attributes.simples import IntegerAttribute


class CounterAttribute(IntegerAttribute):
    """CounterAttribute is very like
    :class:`~sheraf.attributes.simples.SimpleAttribute` with concurrency-proof
    operations.

    It acts as a drop-in replacement for
    :class:`~sheraf.attributes.simples.SimpleAttribute` with ``increment`` and
    ``decrement`` methods that automatically solve conflicts. It supports all
    mathematical operations, but only solves conflicts using ``increment`` and
    ``decrement``. Every other destructive operation are sensible to conflicts.

    >>> class MyModel(sheraf.Model):
    ...     table = "mymodel"
    ...     # You can just replace SimpleAttribute or IntegerAttribute with CounterAttribute
    ...     counter = sheraf.CounterAttribute() # initialized with 0
    ...
    >>> with sheraf.connection(commit=True):
    ...     m = MyModel.create()
    ...     m.counter.increment(1)
    ...     m.counter.decrement(1)

    Here is how to produce a conflict case, and how CounterAttributes behaves
    to solve it:

    >>> with sheraf.connection(commit=True):
    ...     sheraf.Database.get().nestable = True
    ...     m1 = MyModel.read(m.id)
    ...
    ...     with sheraf.connection(commit=True):
    ...         m2 = MyModel.read(m.id)
    ...         m2.counter.decrement(10)
    ...
    ...     m1.counter.increment(100)
    ...
    >>> with sheraf.connection():
    ...     m3 = MyModel.read(m.id)
    ...     assert 90 == m3.counter

    The conflict resolution understands that a transaction is adding `100` and
    another transaction is substracting `10` to the counter at the same time,
    and finally adds `90`. The formula used is:
    `new_state_a + new_state_b - old_state` where old_state is `0` as it was
    the previous value registered in the database, and `new_state_a` and
    `new_state_b` are the conflicting new values (here `-10` and `100`).

    Using ``+=`` and ``-=`` operators would have raised a conflicts.
    ``increment`` or ``decrement`` must be called explicitely.

    >>> with sheraf.connection(commit=True):
    ...     sheraf.Database.get().nestable = True
    ...     m1 = MyModel.read(m.id)
    ...
    ...     with sheraf.connection(commit=True):
    ...         m2 = MyModel.read(m.id)
    ...         m2.counter -= 10
    ...
    ...     m1.counter += 100
    Traceback (most recent call last):
        ...
    ZODB.POSException.ConflictError: database conflict error ...

    Regular assignments and operations on the counter also raise conflicts
    for automatic conflict resolution.

    >>> with sheraf.connection(commit=True):
    ...     sheraf.Database.get().nestable = True
    ...     m1 = MyModel.read(m.id)
    ...
    ...     with sheraf.connection(commit=True):
    ...         m2 = MyModel.read(m.id)
    ...         m2.counter = 10
    ...
    ...     m1.counter.increment(100)
    Traceback (most recent call last):
        ...
    ZODB.POSException.ConflictError: database conflict error ...
    """

    def __init__(self, default=0, **kwargs):
        """
        :param default: The counter default value. 0 if unset.
        """
        kwargs["lazy"] = False
        super().__init__(
            default=lambda: sheraf.types.counter.Counter(default), **kwargs
        )

    def write(self, parent, value):
        counter = self.read_raw(parent)
        deserialized = self.deserialize(counter)

        if not isinstance(counter, sheraf.types.counter.Counter):
            self.write_raw(parent, deserialized)

        deserialized.set(self.serialize(value))
        return deserialized

    def read(self, parent):
        value = self.read_raw(parent)
        deserialized = self.deserialize(value)

        if not isinstance(value, sheraf.types.counter.Counter):
            self.write_raw(parent, deserialized)

        return deserialized

    def serialize(self, value):
        if isinstance(value, sheraf.types.counter.Counter):
            return value.value

        return value

    def deserialize(self, value):
        if isinstance(value, BTrees.Length.Length):
            return sheraf.types.counter.Counter(value.value)

        if not isinstance(value, sheraf.types.counter.Counter):
            return sheraf.types.counter.Counter(value)

        return value

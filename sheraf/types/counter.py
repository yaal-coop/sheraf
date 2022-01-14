import persistent


class CounterMetaclass(type):
    def __new__(cls, name, bases, attrs):
        klass = super().__new__(cls, name, bases, attrs)

        unary_methods = [
            "__abs__",
            "__neg__",
            "__abs__",
            "__invert__",
            "__complex__",
            "__int__",
            "__float__",
            "__str__",
            "__hash__",
        ]

        comparison_methods = [
            "__add__",
            "__and__",
            "__floordiv__",
            "__index__",
            "__invert__",
            "__lshift__",
            "__mod__",
            "__mul__",
            "__matmul__",
            "__or__",
            "__pos__",
            "__pow__",
            "__rshift__",
            "__sub__",
            "__truediv__",
            "__xor__",
            "__div__",
            "__radd__",
            "__rsub__",
            "__rmul__",
            "__rmatmul__",
            "__rtruediv__",
            "__rfloordiv__",
            "__rmod__",
            "__rdivmod__",
            "__rpow__",
            "__rlshift__",
            "__rrshift__",
            "__rand__",
            "__ror__",
            "__rxor__",
            "__rdiv__",
            "__lt__",
            "__le__",
            "__eq__",
            "__ne__",
            "__gt__",
            "__ge__",
        ]

        destructive_methods = [
            "__iadd__",
            "__isub__",
            "__imul__",
            "__imatmul__",
            "__itruediv__",
            "__ifloordiv__",
            "__imod__",
            "__ipow__",
            "__ilshift__",
            "__irshift__",
            "__iand__",
            "__ixor__",
            "__ior__",
        ]

        def comparison_implementation(m):
            def _implementation(self, other):
                if isinstance(other, Counter):
                    return getattr(self.value, m)(other.value)
                return getattr(self.value, m)(other)

            return _implementation

        def unary_implementation(m):
            def _implementation(self):
                return getattr(self.value, m)()

            return _implementation

        def destructive_implementation(m):
            def _implementation(self, other):
                operation_value = other.value if isinstance(other, Counter) else other
                method = m.replace("__i", "__")
                new_value = getattr(self.value, method)(operation_value)

                if new_value == NotImplemented:
                    new_value = getattr(operation_value, method)(self.value)
                if new_value == NotImplemented:
                    raise AttributeError()

                self.value = new_value
                self.nb_editions += 1
                return self

            return _implementation

        for m in unary_methods:
            setattr(klass, m, unary_implementation(m))

        for m in comparison_methods:
            setattr(klass, m, comparison_implementation(m))

        for m in destructive_methods:
            setattr(klass, m, destructive_implementation(m))

        return klass


class Counter(persistent.Persistent, metaclass=CounterMetaclass):
    """Counter is a simple numeric persistent type with conflict proof
    increment and decrement functions."""

    value = 0
    nb_editions = 0

    def __init__(self, value=0):
        if isinstance(value, Counter):
            value = value.value

        self.value = value

    def set(self, v):
        self.value = v
        self.nb_editions += 1

    def increment(self, value):
        self.value += value

    def decrement(self, value):
        self.value -= value

    def _p_resolveConflict(self, old_state, saved_state, new_state):
        import ZODB.POSException

        old_value, old_nb_editions = old_state
        saved_value, saved_nb_editions = saved_state
        new_value, new_nb_editions = new_state

        if saved_nb_editions != old_nb_editions or new_nb_editions != old_nb_editions:
            raise ZODB.POSException.ConflictError()

        value = saved_value + new_value - old_value
        return (value, old_nb_editions)

    def __getstate__(self):
        return (self.value, self.nb_editions)

    def __setstate__(self, v):
        value, nb_editions = v
        self.value = value
        self.nb_editions = nb_editions

    def __repr__(self):
        return "<Counter value=%s>" % self.value

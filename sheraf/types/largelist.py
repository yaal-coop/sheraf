from BTrees.IOBTree import IOBTree


class LargeList(IOBTree):
    """Large List."""

    LENGTH_KEY = -1

    def __init__(self, items=None):
        items = items if items is not None else []
        self.extend(items)

    def append(self, item, unique=False):
        if unique and item in self:
            return

        new_index = len(self)
        self._set_length(len(self) + 1)
        self[new_index] = item

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        return all(mine == their for mine, their in zip(self, other))

    def __len__(self):
        return IOBTree.get(self, self.LENGTH_KEY, self.LENGTH_KEY + 1)

    def __add__(self, other):
        return LargeList(list(self) + other)

    def _set_length(self, length):
        IOBTree.__setitem__(self, self.LENGTH_KEY, length)

    def extend(self, items, unique=False):
        for _item in items:
            self.append(_item, unique)

    def insert(self, indice, element):
        self._set_length(len(self) + 1)
        for i in range(len(self) - 1, indice, -1):
            self[i] = self[i - 1]
        self[indice] = element

    def remove(self, item, all=False):
        found = False
        for key, value in self.items():
            if key == self.LENGTH_KEY:
                continue

            if item != value:
                continue

            found = True
            del self[key]

            if not all:
                return

        if not all or not found:
            raise ValueError(f"{item} not in {self}")

    def pop(self):
        length = len(self)
        self._set_length(length - 1)
        return super().pop(length - 1)

    def __iter__(self):
        _values = IOBTree.itervalues(self)
        try:
            next(_values)
            return _values
        except StopIteration:
            return iter({})

    def __contains__(self, item):
        return item in iter(self)

    def __getitem__(self, item):
        if isinstance(item, slice):
            _slice = self._reslice(item)
            return (
                IOBTree.__getitem__(self, index)
                for index in range(
                    _slice.start, min(len(self), _slice.stop), _slice.step
                )
            )

        elif isinstance(item, int):
            if item >= len(self):
                raise IndexError

            try:
                if not item:
                    return IOBTree.__getitem__(self, 0)
                return IOBTree.__getitem__(self, item > 0 and item or len(self) + item)
            except KeyError as ex:
                raise IndexError(ex)

        else:
            raise TypeError(
                f"Invalid LargeList key '{item}'. It must be an integer or a slice."
            )

    def __setitem__(self, key, value):
        if not isinstance(key, slice) and key >= len(self):
            raise IndexError
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        IOBTree.__delitem__(self, key)
        for i in range(key + 1, len(self)):
            item = IOBTree.__getitem__(self, i)
            IOBTree.__setitem__(self, i - 1, item)
            IOBTree.__delitem__(self, i)
        self._set_length(len(self) - 1)

    def _reslice(self, item):
        if item.step is None or item.step > 0:
            return slice(self._start(item), self._stop(item), self._step(item))
        else:
            return slice(self._start_down(item), self._stop_down(item), item.step)

    def _start(self, item):
        if item.start is None:
            return 0
        elif item.start < 0:
            return len(self) + item.start
        else:
            return item.start

    def _stop(self, item):
        if item.stop is None:
            return len(self)
        elif item.stop < 0:
            return len(self) + item.stop
        else:
            return item.stop

    def _step(self, item):
        return item.step or 1

    def _start_down(self, item):
        if item.start is None:
            return len(self) - 1
        elif item.start < 0:
            return len(self) + item.start
        else:
            return item.start

    def _stop_down(self, item):
        if item.stop is None:
            return -1
        elif item.stop < 0:
            return len(self) + item.stop
        else:
            return item.stop

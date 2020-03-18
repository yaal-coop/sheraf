from BTrees.OOBTree import OOBTree


class LargeDict(OOBTree):
    """A Large Dictionnary based on a Object-Object-BTree.

    LargeDicts keys are ordered and thus they can be iterated:

    >>> mydict = sheraf.types.LargeDict({
    ...     "D": "four",
    ...     "C": "three",
    ...     "B": "two",
    ...     "A": "one",
    ... }) # declaration is unordered
    ...
    >>> list(v for v in mydict.values())
    ... # iteration is ordered
    ['one', 'two', 'three', 'four']

    LargeDicts can also be sliced. Slices return a generator over the values:

    >>> list(mydict["B":"D"])
    ['two', 'three', 'four']
    >>> list(mydict[::-1])
    ['four', 'three', 'two', 'one']

    When using integers as dictionnary keys, be careful that slices behave a
    bit different than they would do for a list, as we use **keys** and not
    indexes.

    >>> mydict = sheraf.types.LargeDict({1:"one", 2:"two", 3:"three"})
    >>> mylist = ["one", "two", "three"]
    >>>
    >>> list(mydict[1:2]) # 1 and 2 are keys
    ['one', 'two']
    >>>
    >>> mylist[1:2] # 1 and 2 are indices
    ['two']
    """

    def __getitem__(self, item):
        if not isinstance(item, slice):
            return OOBTree.__getitem__(self, item)

        # Performance shortcuts
        if item.start is None and item.stop is None:
            if item.step == -1:
                return reversed(OOBTree.values(self))
            if item.step == 1 or item.step is None:
                return OOBTree.values(self)

        keys = OOBTree.keys(self, min=item.start, max=item.stop)
        if item.step and item.step < 0:
            return (
                OOBTree.__getitem__(self, keys[i - 1])
                for i in range(len(keys), 0, item.step)
            )

        return (
            OOBTree.__getitem__(self, keys[i])
            for i in range(0, len(keys), item.step or 1)
        )

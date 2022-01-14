"""Types are used to define the internal storage in ZODB.

There are no need to setup specific types in basic usage of sheraf
because `Model` uses `xAttribute`, not `Type`.
"""
import BTrees.OOBTree
import persistent
import sheraf.tools.dicttools

from .largedict import LargeDict
from .largelist import LargeList

assert LargeDict
assert LargeList


SmallList = persistent.list.PersistentList
List = SmallList
Set = BTrees.OOBTree.OOTreeSet


class SmallDict(persistent.mapping.PersistentMapping):
    """SmallDict is a :class:`PersistentMapping` implementation with a simple
    conflict resolution implementation.

    When two different keys of the mapping are edited in concurrency, no
    conflict is raised.
    """

    def _p_resolveConflict(self, old, saved, commited):
        import ZODB

        try:
            return sheraf.tools.dicttools.merge(old, saved, commited)
        except sheraf.tools.dicttools.DictConflictException:
            raise ZODB.POSException.ConflictError()

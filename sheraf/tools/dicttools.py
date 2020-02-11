"""Maybe those functions do consume a lot of memory, what about editing
existing dicts instead of creating new ones?"""

# pickle is needed until this is fixed https://github.com/zopefoundation/ZODB/pull/278
import zodbpickle.pickle as pickle


class DictConflictException(BaseException):
    pass


def merge(c, a, b):
    # From: https://stackoverflow.com/questions/52755140/three-way-dictionary-deep-merge-in-python

    # recursively merge sub-dicts that are common to a, b and c
    for k in set(a.keys()) & set(b.keys()) & set(c.keys()):
        if all(isinstance(d.get(k), dict) for d in (a, b, c)):
            a[k] = b[k] = c[k] = merge(c[k], a[k], b[k])

    # convert sub-dicts into tuples of item pairs to allow them to be hashable
    for d in a, b, c:
        for k, v in d.items():
            if isinstance(v, dict):
                d[k] = tuple(v.items())

    # convert all the dict items into sets
    set_a, set_b, set_c = (
        set((k, pickle.dumps(v)) for k, v in d.items()) for d in (a, b, c)
    )

    # intersect keys from the symmetric set differences to c to find conflicts
    for k in set(k for k, _ in set_a ^ set_c) & set(k for k, _ in set_b ^ set_c):
        # it isn't really a conflict if the new values of a and b are the same
        if a.get(k) != b.get(k) or (k in a) ^ (k in b):
            raise DictConflictException("Conflict found in key %s" % k)

    # merge the dicts by union'ing the differences to c with the common items
    d = dict(set_a & set_b & set_c | set_a - set_c | set_b - set_c)

    # convert the tuple of items back to dicts for output
    for k, v in d.items():
        v = pickle.loads(v)
        if isinstance(v, tuple):
            d[k] = dict(v)
        else:
            d[k] = v

    return d

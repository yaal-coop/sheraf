"""Maybe those functions do consume a lot of memory, what about editing
existing dicts instead of creating new ones?"""


class DictConflictException(BaseException):
    pass


def pr_eq(a, b):
    try:
        return a == b
    except ValueError:
        return False


def merge(old, a, b):
    res = {}
    for k in set(a.keys()) | set(b.keys()) | set(old.keys()):
        # value has been deleted in a and b --> ignore
        if k not in a and k not in b:
            continue

        # value not in old
        if k not in old:
            if k not in a:
                # PR is new in b --> keep b
                res[k] = b[k]
                continue

            if k not in b:
                # PR is new in a --> keep a
                res[k] = a[k]
                continue

        # value in old
        else:
            # a unchanged, b changed --> keep b
            if pr_eq(a.get(k), old.get(k)):
                res[k] = b[k]
                continue

            # b unchanged, a changed --> keep a
            if pr_eq(b.get(k), old.get(k)):
                res[k] = a[k]
                continue

        # value equal in a and b --> keep
        if pr_eq(a.get(k), b.get(k)):
            res[k] = a[k]
            continue

        # values are dict --> merge
        if isinstance(a[k], dict) and isinstance(b[k], dict):
            res[k] = merge(old[k], a[k], b[k])
            continue

        raise DictConflictException("Conflict found in key %s" % k)

    return res

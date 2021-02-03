import ZODB

import sheraf


def check_conflict_resolution():
    """A simple utility functions that checks that sheraf objects conflict
    resolution is active.

    :return: ``True`` if sheraf objects conflicts can be solved, else ``False``.

    >>> from sheraf.batches.checks import check_conflict_resolution
    >>> with sheraf.connection():
    ...    assert check_conflict_resolution()
    """
    table_name = "__conflict_resolution_test_model__"
    nestable = sheraf.Database.get().nestable
    sheraf.Database.get().nestable = True

    class TestModel(sheraf.Model):
        table = table_name
        counter = sheraf.CounterAttribute(default=0)

    with sheraf.connection(commit=True):
        m = TestModel.create()

    try:
        with sheraf.connection(commit=True):
            TestModel.read(m.identifier).counter.increment(1)

            with sheraf.connection(commit=True):
                TestModel.read(m.identifier).counter.increment(15)

    except ZODB.POSException.ConflictError:  # pragma: no cover
        return False

    else:
        return True

    finally:
        with sheraf.connection(commit=True) as conn:
            del conn.root()[table_name]

        sheraf.Database.get().nestable = nestable


def check_attributes_index(model_instance):
    """
    For a given model instance compute all the values for all
    the indexes, then checks the index table if the values
    match the model instance.
    """
    root = sheraf.Database.current_connection().root()
    result = {}
    index_table = root.get(model_instance.table)

    if not index_table:
        return result

    for index_name, index in model_instance.indexes().items():
        if index.details.primary:
            continue

        values = index.details.get_values(model_instance)

        if values and index_name not in index_table:
            result[index_name] = False
            continue

        if index.details.unique:
            result[index_name] = all(
                value in index_table[index_name]
                and index_table[index_name][value] == model_instance.mapping
                for value in values
            )
        else:
            result[index_name] = all(
                value in index_table[index_name]
                and model_instance.mapping in index_table[index_name][value]
                for value in values
            )
    return result


def check_model_index(model):
    """
    Browse an index_table, and checks that every indexed persistent can be read.

    For a given attribute:
    - If MULTIPLE: an attribute index is ok if all model instances for an attribute value are present
    - If UNIQUE: an attribute index is ok if the model instances for this attribute value is present
    :param model: a model (class)
    :return: a health report dictionary for each model for each attribute.
    """
    root = sheraf.Database.current_connection().root()
    index_table = root.get(model.table)
    result = {}

    if not index_table:
        return result

    for attribute_index_key, attribute_index_table in index_table.items():
        index = model.indexes()[attribute_index_key]

        if index.details.primary:
            continue

        for mmapping in attribute_index_table.values():
            try:
                if index.details.unique:
                    model.read(model._decorate(mmapping).identifier)
                else:
                    [
                        model.read(model._decorate(persistent).identifier)
                        for persistent in mmapping
                    ]
                result.setdefault(attribute_index_key, {"ok": 0, "ko": 0})["ok"] += 1

            except sheraf.exceptions.ModelObjectNotFoundException:
                result.setdefault(attribute_index_key, {"ok": 0, "ko": 0})["ko"] += 1

    return result

import sheraf


def check_conflict_resolution():
    """
    Checks wether sheraf object conflicts resolutions are possible.
    When this is KO, it is generally because sheraf is not installed in the ZEO
    environnement, so ZEO cannot solve sheraf object conflicts.
    """
    import ZODB

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
    Given a model instance, computes all the values for all the indexes,
    then checks the index table if the values match the model instance.

    This finds instances that are not synchronized with theirs indexes.
    """
    root = sheraf.Database.current_connection().root()
    result = {}
    index_table = root.get(model_instance.table)

    if not index_table:
        return result

    for index_name, index in model_instance.indexes.items():
        if index.details.primary:
            continue

        values = index.details.get_model_index_keys(model_instance)

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
                and model_instance.raw_identifier in index_table[index_name][value]
                and model_instance.mapping
                == index_table[index_name][value][model_instance.raw_identifier]
                for value in values
            )
    return result


def check_model_index(model):
    """
    Given a model, for every index table, reads every mapping in the table
    and checks that the mappin belongs a model.

    This finds orphans models.
    """
    root = sheraf.Database.current_connection().root()
    index_table = root.get(model.table)
    result = {}

    if not index_table:
        return result

    for attribute_index_key, attribute_index_table in index_table.items():
        index = model.indexes[attribute_index_key]

        if index.details.primary:
            continue

        for mmapping in attribute_index_table.values():
            try:
                if index.details.unique:
                    model.read(model._decorate(mmapping).identifier)
                else:
                    [
                        model.read(model._decorate(persistent).identifier)
                        for persistent in mmapping.values()
                    ]
                result.setdefault(attribute_index_key, {"ok": 0, "ko": 0})["ok"] += 1

            except sheraf.exceptions.ModelObjectNotFoundException:
                result.setdefault(attribute_index_key, {"ok": 0, "ko": 0})["ko"] += 1

    return result

import ZODB

import sheraf
from sheraf.batches.utils import discover_models

try:  # pragma: no cover
    import colored

    HAS_COLORED = True
except ImportError:  # pragma: no cover
    HAS_COLORED = False

try:  # pragma: no cover
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:  # pragma: no cover
    HAS_TQDM = False


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


# Set the list of check functions to be run
INSTANCE_CHECK_FUNCS = {}
ATTRIBUTE_CHECK_FUNCS = {
    "index": check_attributes_index,
}
MODEL_CHECK_FUNCS = {"index": check_model_index}
OTHER_CHECK_FUNCS = {"check_conflict_resolution": check_conflict_resolution}


def check_health(
    *args,
    model_checks=None,
    instance_checks=None,
    attribute_checks=None,
    other_checks=None
):
    """
    Takes some modules in parameters.
    :param model_checks: If None, check also model consistency (see constant model_check_funcs)
    :param instance_checks: If None, check all instance consistency rules. Else, give the list of wanted
    checking rules (see constant instance_check_funcs)
    :param attribute_checks: If None, check all attribute consistency rules. Else, give the list of wanted
    checking rules (see constant instance_check_funcs)
    The function will discover models in the modules, analyze every
    model instance, and return a health report in JSON. Depending on the
    result, you may need to apply some migrations.
    """
    models = discover_models(*args)
    health_report = {}

    instance_checks = instance_checks or []
    attribute_checks = attribute_checks or []
    model_checks = model_checks or []
    other_checks = other_checks or []
    if not instance_checks and not attribute_checks and not model_checks:
        instance_checks = INSTANCE_CHECK_FUNCS.keys()
        attribute_checks = ATTRIBUTE_CHECK_FUNCS.keys()
        model_checks = MODEL_CHECK_FUNCS.keys()
        other_checks = OTHER_CHECK_FUNCS.keys()

    for check_key in other_checks:
        health_report[check_key] = OTHER_CHECK_FUNCS[check_key]()

    for model_path, model in models:

        for check_key in instance_checks:
            health_report.setdefault(
                INSTANCE_CHECK_FUNCS[check_key].__name__, {}
            ).setdefault(model_path, {"ok": 0, "ko": 0})

        for check_key in model_checks:
            model_check_func = MODEL_CHECK_FUNCS[check_key]
            health_report.setdefault(model_check_func.__name__, {})[
                model_path
            ] = model_check_func(model)

        # Iterate on instances
        if HAS_TQDM:  # pragma: no cover
            iterator = tqdm(model.all(), total=model.count(), desc=model.__name__)
        else:
            iterator = model.all()
        for m in iterator:
            for check_key in instance_checks:
                check_func = INSTANCE_CHECK_FUNCS[check_key]
                model_instance_result = health_report[check_func.__name__][model_path]
                if check_func(m):
                    model_instance_result["ok"] += 1
                else:
                    model_instance_result["ko"] += 1

            for check_key in attribute_checks:
                check_func = ATTRIBUTE_CHECK_FUNCS[check_key]
                health_report.setdefault(check_func.__name__, {})
                for attribute_name, bool_value in check_func(m).items():
                    attribute_result = (
                        health_report[check_func.__name__]
                        .setdefault(model_path, {})
                        .setdefault(attribute_name, {"ok": 0, "ko": 0})
                    )
                    if bool_value:
                        attribute_result["ok"] += 1
                    else:
                        attribute_result["ko"] += 1
    return health_report


def _print(string, padding, color):
    if not HAS_COLORED:
        return str(string).ljust(padding, "_")

    if padding:  # pragma: no cover
        return (
            colored.stylize(string, colored.fg("blue"))
            + (padding - len(str(string))) * "_"
        )
    return colored.stylize(string, colored.fg("blue"))  # pragma: no cover


def print_neutral(string, padding=0):
    return _print(string, padding, "blue")


def print_success(string, padding=0):
    return _print(string, padding, "green")


def print_failure(string, padding=0):
    return _print(string, padding, "red")


def _print_check_other_health_result(check_reason, health_table):
    print(
        "- {:_<86} ".format(print_neutral(check_reason))
        + " "
        + (print_success("OK") if health_table[check_reason] else print_failure("KO"))
    )


def _print_check_model_health_result(check_reason, health_table):

    print(80 * "=" + "\n" + print_neutral(check_reason) + 39 * " " + """OK       KO""")
    table_key = "check_model_" + check_reason
    for model_path, attributes in health_table[table_key].items():
        print(
            "- {:_<52} TOTAL: ".format(model_path)
            + print_success(sum(values["ok"] for values in attributes.values()), 8)
            + " "
            + print_failure(sum(values["ko"] for values in attributes.values()), 8)
        )

        for attribute_name, values in attributes.items():
            print(
                "  - {:_<57} ".format(attribute_name)
                + print_success(values["ok"], 8)
                + " "
                + print_failure(values["ko"], 8)
            )

    if not health_table[table_key]:
        print("  No model to visit.")


def _print_check_instance_health_result(check_reason, health_table):
    """
    :param check_reason: one among model_checks keys
    :param health_table: result of a check function
    """
    print(80 * "=" + "\n" + print_neutral(check_reason) + 39 * " " + """OK       KO""")
    for model_path, values in health_table["check_instance_" + check_reason].items():
        print(
            "- {:_<59} ".format(model_path)
            + print_success(values["ok"], 8)
            + " "
            + print_failure(values["ko"], 8)
        )


def _print_check_attribute_health_result(check_reason, health_table):
    print(80 * "=" + "\n{:<62}".format(print_neutral(check_reason)) + """OK       KO""")
    table_key = "check_attributes_" + check_reason
    for model_path, attributes in health_table[table_key].items():
        print(
            "- {:_<52} TOTAL: ".format(model_path)
            + print_success(sum(values["ok"] for values in attributes.values()), 8)
            + " "
            + print_failure(sum(values["ko"] for values in attributes.values()), 8)
        )

        for attribute_name, values in attributes.items():
            print(
                "  - {:_<57} ".format(attribute_name)
                + print_success(values["ok"], 8)
                + " "
                + print_failure(values["ko"], 8)
            )

    if not health_table[table_key]:
        print("  No model to visit.")


def print_health(
    *args,
    model_checks=None,
    instance_checks=None,
    attribute_checks=None,
    other_checks=None
):
    """Takes some modules in parameters (e.g. "american._class.cowboy_module").

    The function will discover models in the modules, analyze every model instance, and return
    a health report in a human readable format. Depending on the result, you may need to apply some migrations.

    This function does not edit any data and is safe to be executed in a production shell.
    """
    print(
        "             _                     __        _               _\n"
        "=========== | | ================= / _| ==== | | =========== | | ===============\n"
        "         ___| |__   ___ _ __ __ _| |_    ___| |__   ___  ___| | _____\n"
        "        / __| '_ \\ / _ \\ '__/ _` |  _|  / __| '_ \\ / _ \\/ __| |/ / __|\n"
        "        \\__ \\ | | |  __/ | | (_| | |   | (__| | | |  __/ (__|   <\\__ \\\n"
        "        |___/_| |_|\\___|_|  \\__,_|_|    \\___|_| |_|\\___|\\___|_|\\_\\___/\n"
        "==============================================================================="
    )
    print("Analyzing your models, this operation can be very long...")

    instance_checks = instance_checks or []
    attribute_checks = attribute_checks or []
    model_checks = model_checks or []
    other_checks = other_checks or []
    if not instance_checks and not attribute_checks and not model_checks:
        instance_checks = INSTANCE_CHECK_FUNCS.keys()
        attribute_checks = ATTRIBUTE_CHECK_FUNCS.keys()
        model_checks = MODEL_CHECK_FUNCS.keys()
        other_checks = OTHER_CHECK_FUNCS.keys()

    health = check_health(
        *args,
        model_checks=model_checks,
        instance_checks=instance_checks,
        attribute_checks=attribute_checks,
        other_checks=other_checks,
    )

    for other_check_type in other_checks:
        _print_check_other_health_result(other_check_type, health)

    for model_check_type in model_checks:
        _print_check_model_health_result(model_check_type, health)

    for instance_check_type in instance_checks:
        _print_check_instance_health_result(instance_check_type, health)

    for attribute_check_type in attribute_checks:
        _print_check_attribute_health_result(attribute_check_type, health)

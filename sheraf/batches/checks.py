import ZODB

import sheraf
from sheraf.batches.utils import discover_models

try:  # pragma: no cover
    import colored

    HAS_COLORED = True
except ImportError:
    HAS_COLORED = False

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
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
            TestModel.read(m.id).counter.increment(1)

            with sheraf.connection(commit=True):
                TestModel.read(m.id).counter.increment(15)

    except ZODB.POSException.ConflictError:  # pragma: no cover
        return False

    else:
        return True

    finally:
        with sheraf.connection(commit=True) as conn:
            del conn.root()[table_name]

        sheraf.Database.get().nestable = nestable


# Set the list of check functions to be run
INSTANCE_CHECK_FUNCS = {}
ATTRIBUTE_CHECK_FUNCS = {}
MODEL_CHECK_FUNCS = {}


def check_health(*args, model_checks=None, instance_checks=None, attribute_checks=None):
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

    if instance_checks is None:
        instance_checks = INSTANCE_CHECK_FUNCS.keys()
    if attribute_checks is None:
        attribute_checks = ATTRIBUTE_CHECK_FUNCS.keys()
    if model_checks is None:
        model_checks = MODEL_CHECK_FUNCS.keys()

    health_report["check_conflict_resolution"] = check_conflict_resolution()

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
    print(80 * "=" + "\n" + print_neutral(check_reason) + 39 * " " + """OK       KO""")
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


def print_health(*args, model_checks=None, instance_checks=None, attribute_checks=None):
    """Takes some modules in parameters (e.g. "american.class.cowboy_module").

    The function will discover models in the modules, analyze every model instance, and return
    a health report in a human readable format. Depending on the result, you may need to apply some migrations.

    This function does not edit any data and is safe to be executed in a production shell.
    """
    print(
        """                         _ _                     _               _
======================= | | | ================= | | =========== | | ===========
      _   _ _______   __| | |__              ___| |__   ___  ___| | _____
     | | | |_  / _ \\ / _` | '_ \\            / __| '_ \\ / _ \\/ __| |/ / __|
     | |_| |/ / (_) | (_| | |_) |          | (__| | | |  __/ (__|   <\\__ \\
      \\__, /___\\___/ \\__,_|_.__/            \\___|_| |_|\\___|\\___|_|\\_\\___/
       __/ |
===== |___/ ===================================================================
"""
    )
    print("Analyzing your models, this operation can be very long...")

    if instance_checks is None:
        instance_checks = INSTANCE_CHECK_FUNCS.keys()
    if attribute_checks is None:
        attribute_checks = ATTRIBUTE_CHECK_FUNCS.keys()
    if model_checks is None:
        model_checks = MODEL_CHECK_FUNCS.keys()

    health = check_health(
        *args,
        model_checks=model_checks,
        instance_checks=instance_checks,
        attribute_checks=attribute_checks
    )

    print(
        "  "
        + print_neutral("Custom conflict resolution enabled")
        + """                                         {conflict_resolution}""".format(
            conflict_resolution=print_success("OK")
            if health["check_conflict_resolution"]
            else print_failure("KO")
        )
    )

    for model_check_type in model_checks:
        _print_check_model_health_result(model_check_type, health)

    for instance_check_type in instance_checks:
        _print_check_instance_health_result(instance_check_type, health)

    for attribute_check_type in attribute_checks:
        _print_check_attribute_health_result(attribute_check_type, health)

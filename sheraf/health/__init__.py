from rich.console import Console
from rich.markdown import Markdown
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import TextColumn
from rich.progress import TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from sheraf.health.utils import discover_models

from .checks import check_attributes_index
from .checks import check_conflict_resolution
from .checks import check_model_index


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
    other_checks=None,
    console=None,
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
        result, you may need to apply some fixes.
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

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("{task.completed}", justify="right"),
        TextColumn("/"),
        TextColumn("{task.total}"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        tasks = {}
        for model_path, model in models:
            tasks[model] = progress.add_task(model.__name__)

        for model_path, model in models:
            progress.update(tasks[model], total=model.count())

        for model_path, model in models:
            progress.start_task(tasks[model])

            for check_key in instance_checks:
                instance_check_func = INSTANCE_CHECK_FUNCS[check_key]
                health_report.setdefault(instance_check_func.__name__, {}).setdefault(
                    model_path, {"ok": 0, "ko": 0}
                )

            for check_key in model_checks:
                model_check_func = MODEL_CHECK_FUNCS[check_key]
                health_report.setdefault(model_check_func.__name__, {})[
                    model_path
                ] = model_check_func(model)

            # Iterate on instances
            for m in model.all():
                progress.update(tasks[model], advance=1)
                for check_key in instance_checks:
                    check_func = INSTANCE_CHECK_FUNCS[check_key]
                    model_instance_result = health_report[check_func.__name__][
                        model_path
                    ]
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


def _print_check_other_health_result(console, check_reason, health_table, help):
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=check_reason,
        expand=True,
        caption=help,
    )
    table.add_column("Check")
    table.add_column("State")

    table.add_row(check_reason, "OK" if health_table[check_reason] else "KO")
    console.print(table)


def _print_check_model_health_result(console, check_reason, health_table, help):
    table_key = "check_model_" + check_reason
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=table_key,
        expand=True,
        caption=help,
    )
    table.add_column("Model")
    table.add_column("KO")
    table.add_column("OK")

    for model_path, attributes in health_table.get(table_key, {}).items():
        table.add_row(
            model_path,
            str(sum(values["ko"] for values in attributes.values())),
            str(sum(values["ok"] for values in attributes.values())),
        )

        for attribute_name, values in attributes.items():
            table.add_row(f"  - {attribute_name}", str(values["ko"]), str(values["ok"]))

    if health_table.get(table_key):
        console.print(table)
    else:
        console.print("  No model to visit.")


def _print_check_instance_health_result(console, check_reason, health_table, help):
    """
    :param check_reason: one among model_checks keys
    :param health_table: result of a check function
    """
    table_key = "check_instance_" + check_reason
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=table_key,
        expand=True,
        caption=help,
    )
    table.add_column("Model")
    table.add_column("KO")
    table.add_column("OK")
    for model_path, values in health_table.get(table_key, {}).items():
        table.add_row(model_path, str(values["ko"]), str(values["ok"]))
    console.print(table)


def _print_check_attribute_health_result(console, check_reason, health_table, help):
    table_key = "check_attributes_" + check_reason
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=table_key,
        expand=True,
        caption=help,
    )
    table.add_column("Model")
    table.add_column("KO")
    table.add_column("OK")

    for model_path, attributes in health_table.get(table_key, {}).items():
        table.add_row(
            model_path,
            str(sum(values["ko"] for values in attributes.values())),
            str(sum(values["ko"] for values in attributes.values())),
        )

        for attribute_name, values in attributes.items():
            table.add_row(f"  - {attribute_name}", str(values["ko"]), str(values["ok"]))

    if health_table.get(table_key):
        console.print(table)
    else:
        console.print("  No model to visit.")


def print_health(
    *args,
    model_checks=None,
    instance_checks=None,
    attribute_checks=None,
    other_checks=None,
):
    console = Console(width=100)
    """Takes some modules in parameters (e.g. "american.cowboy_module").

    The function will discover models in the modules, analyze every model instance, and return
    a health report in a human readable format. Depending on the result, you may need to apply some fixes.

    This function does not edit any data and is safe to be executed in a production shell.
    """
    console.print(
        Text(
            "====== _ ==================  __ ==\n"
            "=     | |                   / _| =\n"
            "=  ___| |__   ___ _ __ __ _| |_  =\n"
            "= / __| '_ \\ / _ \\ '__/ _` |  _| =\n"
            "= \\__ \\ | | |  __/ | | (_| | |   =\n"
            "= |___/_| |_|\\___|_|  \\__,_|_|   =\n"
            "==================================",
            justify="center",
        )
    )

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
        console=console,
    )

    for other_check_type in other_checks:
        console.print()
        _print_check_other_health_result(
            console,
            other_check_type,
            health,
            Markdown(OTHER_CHECK_FUNCS[other_check_type].__doc__),
        )
        console.print()

    for model_check_type in model_checks:
        console.print()
        _print_check_model_health_result(
            console,
            model_check_type,
            health,
            Markdown(MODEL_CHECK_FUNCS[model_check_type].__doc__),
        )
        console.print()

    for instance_check_type in instance_checks:
        console.print()
        _print_check_instance_health_result(
            console,
            instance_check_type,
            health,
            Markdown(INSTANCE_CHECK_FUNCS[instance_check_type].__doc__),
        )
        console.print()

    for attribute_check_type in attribute_checks:
        console.print()
        _print_check_attribute_health_result(
            console,
            attribute_check_type,
            health,
            Markdown(ATTRIBUTE_CHECK_FUNCS[attribute_check_type].__doc__),
        )
        console.print()

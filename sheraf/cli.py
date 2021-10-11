import click
import math
import sheraf
import sys
from rich.traceback import install
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from sheraf.health.utils import discover_models


install(show_locals=True)


@click.group()
@click.argument("uri")
@click.pass_context
def cli(ctx, uri):
    sys.path.append(".")
    ctx.db = sheraf.Database(uri)


@cli.result_callback()
@click.pass_context
def after_cli(ctx, result, **kwargs):
    ctx.db.close()


@cli.command()
@click.argument("models", nargs=-1)
def check(models):
    with sheraf.connection():
        sheraf.print_health(*models)


@cli.command()
@click.argument("models")
@click.option(
    "--index",
    help="The name of the indexes to rebuild. If not provided all the indexes will be rebuilt.",
    multiple=True,
)
@click.option(
    "--batch-size",
    help="The number of elements to iterate between two transactions savepoints or commits.",
    default=1000,
    type=int,
)
@click.option(
    "--commit/--no-commit",
    help="Make a real commit for each batch. Defaults to False.",
    default=False,
    is_flag=True,
)
@click.option(
    "--reset/--no-reset",
    help="Delete the whole index before rebuilding it. Defaults to True.",
    default=True,
    is_flag=True,
)
@click.option(
    "--start",
    help="The indice of the first element to reset.",
    default=None,
    type=int,
)
@click.option(
    "--end",
    help="The indice of the last element to reset.",
    default=None,
    type=int,
)
def rebuild(models, index, batch_size, commit, reset, start, end):
    with sheraf.connection(commit=True) as conn:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("{task.completed}", justify="right"),
            TextColumn("/"),
            TextColumn("{task.total}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=True,
        ) as progress:
            models = discover_models(models)

            for _, model in models:
                total = min(end or math.inf, model.count()) - (start or 0)
                task = progress.add_task(model.table, total=total)

                def callback(i, m):
                    if i and i % batch_size == 0:
                        if commit:
                            conn.transaction_manager.commit()
                            conn.cacheGC()
                        else:
                            conn.transaction_manager.savepoint(True)
                    progress.update(task, advance=1)

                model.index_table_rebuild(
                    *index, callback=callback, reset=reset, start=start, end=end
                )

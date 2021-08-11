import click
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
    "--commit", help="Make a real commit for each batch", default=False, is_flag=True
)
def rebuild(models, index, batch_size, commit):
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
                task = progress.add_task(model.table, total=model.count())

                def callback(i, m):
                    if i and i % batch_size == 0:
                        if commit:
                            conn.transaction_manager.commit()
                            conn.cacheGC()
                        else:
                            conn.transaction_manager.savepoint(True)
                    progress.update(task, advance=1)

                model.index_table_rebuild(*index, callback=callback)

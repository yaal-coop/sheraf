import click
import sheraf
import sys
from rich.traceback import install
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
    "--indexes",
    help="The name of the indexes to rebuild. If not provided all the indexes will be rebuilt.",
    multiple=True,
)
def rebuild(models, indexes):
    with sheraf.connection(commit=True):
        models = discover_models(models)
        for _, model in models:
            model.index_table_rebuild(*indexes)

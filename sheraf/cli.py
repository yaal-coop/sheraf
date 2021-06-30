import click
import sheraf
import sys
from rich.traceback import install
from sheraf.health.utils import discover_models


install(show_locals=True)


@click.group()
@click.argument("uri")
def cli(uri):
    sys.path.append(".")
    db = sheraf.Database(uri)


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
    default=None,
)
def rebuild(models, indexes):
    with sheraf.connection(commit=True):
        models = discover_models(models)
        for _, model in models:
            model.index_table_rebuild(indexes)

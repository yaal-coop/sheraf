import click
import sheraf
import sys
from rich.traceback import install


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

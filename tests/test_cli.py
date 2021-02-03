import re
import sheraf
from click.testing import CliRunner
from sheraf.cli import cli


class CliModel(sheraf.Model):
    table = "climymodel"
    foo = sheraf.StringAttribute().index()


def test_healthcheck_conflict_resolution(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        CliModel.create(foo="bar")

    runner = CliRunner()
    result = runner.invoke(
        cli, [f"{sheraf_zeo_database.uri}&database_name=cli", "check", "tests.test_cli"]
    )
    assert result.exit_code == 0, result.output

    assert "check_model_index" in result.output
    assert "check_attributes_index" in result.output
    assert re.search(r"tests.test_cli.CliModel[^\n]*0[^\n]*1", result.output)
    sheraf.Database.get("cli").close()

import re
import sheraf
from click.testing import CliRunner
from sheraf.cli import cli


class CliModel(sheraf.Model):
    table = "climymodel"
    foo = sheraf.StringAttribute().index()
    boo = sheraf.StringAttribute().index()


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


def test_rebuild_all_models_all_indexes(sheraf_zeo_database):
    with sheraf.connection(commit=True) as conn:
        bar = CliModel.create(foo="bar", boo="bar")
        baz = CliModel.create(foo="baz", boo="baz")
        del conn.root()[CliModel.table]["foo"]
        del conn.root()[CliModel.table]["boo"]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [f"{sheraf_zeo_database.uri}&database_name=cli", "rebuild", "tests.test_cli"],
    )
    assert result.exit_code == 0, result.output
    assert result.output == "", result.output

    with sheraf.connection() as conn:
        assert "foo" in conn.root()[CliModel.table]
        assert "boo" in conn.root()[CliModel.table]
        assert bar in CliModel.search(foo="bar")
        assert baz in CliModel.search(foo="baz")


def test_rebuild_all_models_one_index(sheraf_zeo_database):
    with sheraf.connection(commit=True) as conn:
        bar = CliModel.create(foo="bar", boo="bar")
        baz = CliModel.create(foo="baz", boo="baz")
        del conn.root()[CliModel.table]["foo"]
        del conn.root()[CliModel.table]["boo"]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            f"{sheraf_zeo_database.uri}&database_name=cli",
            "rebuild",
            "tests.test_cli",
            "--indexes",
            "foo",
        ],
    )
    assert result.exit_code == 0, result.output
    assert result.output == "", result.output

    with sheraf.connection() as conn:
        assert "foo" in conn.root()[CliModel.table]
        assert "boo" not in conn.root()[CliModel.table]
        assert bar in CliModel.search(foo="bar")
        assert baz in CliModel.search(foo="baz")


def test_rebuild_one_model_all_index(sheraf_zeo_database):
    with sheraf.connection(commit=True) as conn:
        bar = CliModel.create(foo="bar", boo="bar")
        baz = CliModel.create(foo="baz", boo="baz")
        del conn.root()[CliModel.table]["foo"]
        del conn.root()[CliModel.table]["boo"]

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            f"{sheraf_zeo_database.uri}&database_name=cli",
            "rebuild",
            "tests.test_cli.CliModel",
        ],
    )
    assert result.exit_code == 0, result.output

    with sheraf.connection() as conn:
        assert "foo" in conn.root()[CliModel.table]
        assert "boo" in conn.root()[CliModel.table]
        assert bar in CliModel.search(foo="bar")
        assert baz in CliModel.search(foo="baz")

import sheraf
from sheraf.batches.checks import check_health

from . import fixture1


def test_healthcheck_conflict_resolution(sheraf_database):
    with sheraf.connection():
        assert check_health(fixture1)["check_conflict_resolution"] is True

import pytest

import sheraf
from tests.utils import close_database


def test_close_database():
    db = sheraf.Database()
    assert db == sheraf.Database.get()
    close_database(db)

    with pytest.raises(KeyError):
        assert sheraf.Database.get() is None

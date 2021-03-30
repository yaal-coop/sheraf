import datetime

import libfaketime
import pytest
import pytz
import sheraf
import tests


def test_datetime_timestamp(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        date = sheraf.DateTimeAttribute()

    m = Model.create()
    assert m.date is None

    m = Model.read(m.id)
    test_date = datetime.datetime(2014, 8, 16, 10, 10, 1, 1)
    m.date = test_date
    assert test_date == m.date
    assert (test_date - datetime.datetime(1970, 1, 1)).total_seconds() == m.mapping[
        "date"
    ]

    test_date2 = datetime.datetime(2032, 8, 16, 10, 10, 1, 1)
    m.toto = test_date2
    assert test_date2 == m.toto

    m = Model.read(m.id)
    with pytest.raises(AttributeError):
        m.toto
    assert test_date == m.date

    m.date = None
    m = Model.read(m.id)
    assert m.date is None


def test_datetime_timezoned_timestamp(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        date = sheraf.DateTimeAttribute()

    m = Model.create()
    test_date = datetime.datetime(
        2014, 8, 16, 10, 10, 1, 1, tzinfo=pytz.timezone("US/Eastern")
    )
    m.date = test_date

    sanitized_test_date = test_date.replace(tzinfo=None)
    assert sanitized_test_date == m.date
    m = Model.read(m.id)
    assert sanitized_test_date == m.date
    assert (
        sanitized_test_date - datetime.datetime(1970, 1, 1)
    ).total_seconds() == m.mapping["date"]


def test_datetime_default(sheraf_connection):
    _default_test_date = datetime.datetime(2016, 8, 16, 10, 10, 1, 1)

    class Model(tests.UUIDAutoModel):
        _date = sheraf.DateTimeAttribute(default=_default_test_date)

    m = Model.create()
    assert _default_test_date == m._date

    m = Model.read(m.id)
    _test_date = datetime.datetime(2014, 8, 16, 10, 10, 1, 1)
    m._date = _test_date
    assert _test_date == m._date

    _test_date2 = datetime.datetime(2032, 8, 16, 10, 10, 1, 1)
    m.toto = _test_date2
    assert _test_date2 == m.toto

    m = Model.read(m.id)
    with pytest.raises(AttributeError):
        m.toto
    assert _test_date == m._date


@libfaketime.fake_time("2014-08-04 01:01:01")
def test_datetime_creation_datetime(sheraf_database):
    sheraf_database.reset()

    class Model(tests.UUIDAutoModel):
        something = sheraf.SimpleAttribute()

    with libfaketime.fake_time("2014-08-04 02:00:00") as fk:
        with sheraf.connection() as conn:
            m = Model.create()
            fk.tick()
            assert m.creation_datetime() is None
            conn.transaction_manager.commit()
            # TODO: The creation datetime should have the transaction commit datetime and not the object creation one
            assert datetime.datetime(2014, 8, 4, 2, 0, 0) == m.creation_datetime()

    with libfaketime.fake_time("2014-08-04 03:00:00"):
        with sheraf.connection():
            m = Model.read(m.id)
            assert datetime.datetime(2014, 8, 4, 2, 0, 0) == m.creation_datetime()


@libfaketime.fake_time("2014-08-04 01:01:01")
def test_datetime_creation_datetime_deprecated_format(sheraf_database):
    """Pour les vieux models avec l'ancien format de meta dates."""
    sheraf_database.reset()

    class Model(tests.UUIDAutoModel):
        pass

    with sheraf.connection() as conn:
        _datetime = datetime.datetime(2014, 8, 4, 1, 1)
        m = Model.create()
        conn.transaction_manager.commit()

        for date_format in ("%d/%m/%Y %H:%M:%S:%f", "%d/%m/%Y %H:%M"):
            m._creation = _datetime.strftime(date_format)
            assert _datetime == m.creation_datetime()


@libfaketime.fake_time("2014-08-04 01:01:01")
def test_datetime_lastupdate_datetime(sheraf_database):
    sheraf_database.reset()

    class Model(tests.UUIDAutoModel):
        pass

    with libfaketime.fake_time("2014-08-04 02:00:00") as fk:
        with sheraf.connection(commit=True) as conn:
            m = Model.create()
            fk.tick()
            assert m.last_update_datetime() is None
            conn.transaction_manager.commit()
            assert datetime.datetime(2014, 8, 4, 2, 0, 1) == m.last_update_datetime()

    with sheraf.connection():
        m = Model.read(m.id)
        assert datetime.datetime(2014, 8, 4, 2, 0, 1) == m.last_update_datetime()

    with libfaketime.fake_time("2014-08-04 08:00:00") as fk:
        with sheraf.connection(commit=True) as conn:
            m = Model.read(m.id)
            m.save()
            fk.tick()
            assert datetime.datetime(2014, 8, 4, 2, 0, 1) == m.last_update_datetime()
            conn.transaction_manager.commit()
            assert datetime.datetime(2014, 8, 4, 8, 0, 1) == m.last_update_datetime()


@libfaketime.fake_time("2014-08-04 01:01:01")
def test_datetime_lastupdate_datetime_setattr(sheraf_database):
    sheraf_database.reset()

    class Model(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute()

    with libfaketime.fake_time("2014-08-04 02:00:00"):
        with sheraf.connection(commit=True):
            m = Model.create()

    with libfaketime.fake_time("2014-08-04 06:00:00"):
        with sheraf.connection() as conn:
            m = Model.read(m.id)
            m.attr = 42
            assert datetime.datetime(2014, 8, 4, 2) == m.last_update_datetime()
            conn.transaction_manager.commit()
            assert datetime.datetime(2014, 8, 4, 6) == m.last_update_datetime()

    with sheraf.connection():
        m = Model.read(m.id)
        assert datetime.datetime(2014, 8, 4, 6) == m.last_update_datetime()


@libfaketime.fake_time("2014-08-04 01:01:01")
def test_datetime_default_meta_datetimes(sheraf_database):
    sheraf_database.reset()
    """ Pour les vieux models ne possèdant pas de meta dates (création et dernière mise à jour) """

    class Model(tests.UUIDAutoModel):
        pass

    with sheraf.connection():
        m = Model.create()
        assert m.creation_datetime() is None
        assert m.last_update_datetime() is None


@libfaketime.fake_time("2014-08-04 01:01:01")
def test_datetime_auto_initialization(sheraf_database):
    sheraf_database.reset()

    class Model(tests.UUIDAutoModel):
        dta = sheraf.DateTimeAttribute(lazy=False, default=datetime.datetime.now)

    with sheraf.connection():
        assert datetime.datetime(2014, 8, 4, 1, 1, 1) == Model.create().dta


def test_time_attribute(sheraf_database):
    class Model(tests.UUIDAutoModel):
        time = sheraf.TimeAttribute()

    with sheraf.connection(commit=True):
        m = Model.create()
        assert m.time is None

        m.time = datetime.time(12, 13, 14)
        assert m.mapping["time"] == 43994000000
        assert m.time == datetime.time(12, 13, 14)

    with sheraf.connection():
        m = Model.read(m.id)

        m.time = datetime.time(12, 13, 14)
        assert m.mapping["time"] == 43994000000
        assert m.time == datetime.time(12, 13, 14)

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        m.time = None

        assert m.time is None
        assert m.mapping["time"] == -1

    with sheraf.connection():
        m = Model.read(m.id)

        assert m.time is None
        assert m.mapping["time"] == -1


def test_date_attribute(sheraf_database):
    class Model(tests.UUIDAutoModel):
        date = sheraf.DateAttribute()

    with sheraf.connection(commit=True):
        m = Model.create()
        assert m.date is None

        m.date = datetime.date(1971, 1, 1)
        assert m.mapping["date"] == 365
        assert m.date == datetime.date(1971, 1, 1)

    with sheraf.connection():
        m = Model.read(m.id)

        m.date = datetime.date(1971, 1, 1)
        assert m.mapping["date"] == 365
        assert m.date == datetime.date(1971, 1, 1)

    with sheraf.connection(commit=True):
        m = Model.read(m.id)
        m.date = None

        assert m.date is None
        assert m.mapping["date"] == -1

    with sheraf.connection():
        m = Model.read(m.id)

        assert m.date is None
        assert m.mapping["date"] == -1

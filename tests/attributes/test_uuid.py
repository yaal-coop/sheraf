import numbers
import uuid

import pytest

import sheraf


def test_uuid_is_not_autocreated(sheraf_database):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.UUIDAttribute()

    with sheraf.connection():
        m = UUIDModel.create()
        assert m.my_uuid is None


def test_reset_uuid_to_none(sheraf_connection):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.UUIDAttribute()

    m = UUIDModel.create()
    m.my_uuid = uuid.uuid4()

    m = UUIDModel.read(m.id)
    assert isinstance(m.my_uuid, uuid.UUID)
    m.my_uuid = None

    m = UUIDModel.read(m.id)
    assert m.my_uuid is None


def test_bad_uuid(sheraf_connection):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.UUIDAttribute()

    m = UUIDModel.create()
    with pytest.raises(ValueError):
        m.my_uuid = "yolo"


def test_create_with_an_existing_uuid(sheraf_database):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.UUIDAttribute()

    with sheraf.connection():
        m = UUIDModel.create(my_uuid=uuid.uuid4())
        assert isinstance(m.mapping["my_uuid"], numbers.Number)
        assert isinstance(m.my_uuid, uuid.UUID)


def test_create_with_an_existing_uuid_str(sheraf_database):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.UUIDAttribute()

    with sheraf.connection():
        m = UUIDModel.create(my_uuid=str(uuid.uuid4()))
        assert isinstance(m.mapping["my_uuid"], numbers.Number)
        assert isinstance(m.my_uuid, uuid.UUID)


def test_create_with_an_existing_uuid_int(sheraf_database):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.UUIDAttribute()

    with sheraf.connection():
        m = UUIDModel.create(my_uuid=uuid.uuid4().int)
        assert isinstance(m.mapping["my_uuid"], numbers.Number)
        assert isinstance(m.my_uuid, uuid.UUID)


def test_string_uuid_attribute(sheraf_database):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.StringUUIDAttribute()

    with sheraf.connection():
        m = UUIDModel.create(my_uuid=uuid.uuid4().int)
        assert isinstance(m.mapping["my_uuid"], numbers.Number)
        assert isinstance(m.my_uuid, str)


def test_reset_str_uuid_to_none(sheraf_connection):
    class UUIDModel(sheraf.AutoModel):
        my_uuid = sheraf.StringUUIDAttribute()

    m = UUIDModel.create()
    m.my_uuid = uuid.uuid4()

    m = UUIDModel.read(m.id)
    assert isinstance(m.my_uuid, str)
    m.my_uuid = None

    m = UUIDModel.read(m.id)
    assert m.my_uuid is None

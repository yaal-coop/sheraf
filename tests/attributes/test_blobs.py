import io
import tests

import sheraf


class ModelWithBlob(tests.UUIDAutoModel):
    attr = sheraf.SimpleAttribute()
    blob = sheraf.BlobAttribute()
    blobs = sheraf.SmallListAttribute(sheraf.BlobAttribute())


def check_blob(model, database, check_path):
    assert bool(model.blob) and model.blob

    f = model.blob.open()
    assert b"ABCDEF" == f.read()
    if check_path:
        assert database.storage.blob_dir in f.name

    assert model.blob.data == b"ABCDEF"
    assert model.blob["data"] == b"ABCDEF"
    assert model.blob.original_name == "image.png"
    assert model.blob["original_name"] == "image.png"
    assert model.blob.filename == f.name
    assert model.blob["filename"] == f.name
    assert model.blob.file_extension == "png"
    assert model.blob["file_extension"] == "png"
    assert str(model.blob) == "image.png"
    assert 1 == len(model.blob)

    f.close()


def check_blobs(model, database, check_path, nb_expected):
    assert len(model.blobs) == nb_expected
    for blob in model.blobs:
        assert bool(blob) and blob

        f = blob.open()
        assert b"ABCDEF" == f.read()
        if check_path:
            assert database.storage.blob_dir in f.name

        assert blob.data == b"ABCDEF"
        assert blob["data"] == b"ABCDEF"
        assert blob.original_name == "image.png"
        assert blob["original_name"] == "image.png"
        assert blob.filename == f.name
        assert blob["filename"] == f.name
        assert blob.file_extension == "png"
        assert blob["file_extension"] == "png"
        assert str(blob) == "image.png"
        assert 1 == len(blob)

        f.close()


def test_crud(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create()
        assert not m.blob and not bool(m.blob)
        m.blob = sheraf.Blob.create(b"ABCDEF", "image.png")
        check_blob(m, sheraf_zeo_database, False)

    with sheraf.connection():
        check_blob(m, sheraf_zeo_database, True)
        assert '<Blob filename="image.png">' == repr(m.blob)

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        check_blob(m, sheraf_zeo_database, True)

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        m.blob.delete()

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert not m.blob
        assert not bool(m.blob)


def test_write_none(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create(blob=sheraf.Blob.create(b"ABCDEF", "image.png"))

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        m.blob = None
        assert m.blob is None

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert m.blob is None


def test_create_dict(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        d = dict(data=b"ABCDEF", filename="image.png")
        m = ModelWithBlob.create(blob=d)
        check_blob(m, sheraf_zeo_database, False)

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        check_blob(m, sheraf_zeo_database, True)


def test_blob_stream(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        blob = sheraf.Blob.create(stream=io.BytesIO(b"ABCDEF"), filename="image.png")
        m = ModelWithBlob.create(blob=blob)
        check_blob(m, sheraf_zeo_database, False)

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        check_blob(m, sheraf_zeo_database, True)


def test_update_blob(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create()
        m.edit({"blob": sheraf.Blob.create(b"ABCDEF", "image.png")})
        check_blob(m, sheraf_zeo_database, False)

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        check_blob(m, sheraf_zeo_database, True)
        m.edit({"blob": sheraf.Blob.create(b"ABCDEFG", "image2.png")})

        assert m.blob.original_name == "image2.png"

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert m.blob.original_name == "image2.png"


def test_overwrite_with_empty_blob(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create(blob=sheraf.Blob.create(b"ABCDEF", "image.png"))

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        m.blob = sheraf.Blob.create(b"", None)
        assert m.blob is None

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert m.blob is None


def test_blob_list_crud(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create()
        assert not m.blobs and not bool(m.blobs)
        m.blobs.append(sheraf.Blob.create(b"ABCDEF", "image.png"))
        check_blobs(m, sheraf_zeo_database, False, 1)

    with sheraf.connection():
        check_blobs(m, sheraf_zeo_database, True, 1)
        assert '<Blob filename="image.png">' == repr(m.blobs[0])

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        check_blobs(m, sheraf_zeo_database, True, 1)

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        m.blobs[0].delete()

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert not m.blobs[0]
        assert not bool(m.blobs[0])


def test_update_blob_list(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create()
        m.edit({"blobs": [sheraf.Blob.create(b"ABCDEF", "image.png")]})
        check_blobs(m, sheraf_zeo_database, False, 1)

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        check_blobs(m, sheraf_zeo_database, True, 1)
        m.edit({"blobs": [sheraf.Blob.create(b"ABCDEFG", "image2.png")]})
        assert m.blobs[0].original_name == "image2.png"

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert m.blobs[0].original_name == "image2.png"


def test_overwrite_with_empty_blob_list(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create(blobs=[sheraf.Blob.create(b"ABCDEF", "image.png")])

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        m.blobs[0] = sheraf.Blob.create(b"", None)
        assert m.blobs[0] is None

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        assert m.blobs[0] is None


def test_create_blob_list_dict(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        d = dict(data=b"ABCDEF", filename="image.png")
        m = ModelWithBlob.create(blobs=[d])
        check_blobs(m, sheraf_zeo_database, False, 1)

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        check_blobs(m, sheraf_zeo_database, True, 1)


def test_remove_all_blobs(sheraf_zeo_database):
    with sheraf.connection(commit=True):
        m = ModelWithBlob.create(
            blobs=[
                sheraf.Blob.create(b"ABCDEF", "image.png"),
                sheraf.Blob.create(b"ABCDEF", "image.png"),
            ]
        )
        check_blobs(m, sheraf_zeo_database, False, 2)

    with sheraf.connection(commit=True):
        m = ModelWithBlob.read(m.id)
        m.blobs = None

    with sheraf.connection():
        m = ModelWithBlob.read(m.id)
        check_blobs(m, sheraf_zeo_database, True, 0)

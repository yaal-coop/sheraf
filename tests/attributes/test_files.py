import os
import shutil

import BTrees.OOBTree
import pytest
from mock import sentinel

import sheraf
import sheraf.attributes.files
import tests


def get_file_storable(file_attribute):
    class FileStorable(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute()
        file = file_attribute

    return FileStorable


def test_default_values(sheraf_temp_dir, sheraf_connection):
    # TODO déplacer ce test ?
    class FileStorable(tests.UUIDAutoModel):
        a = sheraf.SimpleAttribute()
        b = sheraf.SimpleAttribute()
        c = sheraf.SmallListAttribute()
        d = sheraf.LargeDictAttribute()

    s = FileStorable.create()
    s.a = sentinel.A
    s.save()

    _s = FileStorable.read(s.id)
    assert _s.a == sentinel.A
    assert _s.b is None
    assert _s.c == []
    assert isinstance(_s.d, BTrees.OOBTree.OOBTree)
    assert 0 == len(_s.d)


def test_repr(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    s = FileStorable.create()
    s.logo = {"extension": "EXT", "stream": b"STREAM"}
    s.save()
    assert "<FileObject model='FileStorable' attribute_name='logo'>" == str(s.logo)


def test_dict(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    s = FileStorable.create()
    s.logo = {"extension": "EXT", "stream": b"STREAM"}
    s.save()
    assert {"extension": "EXT", "stream": b"STREAM"} == dict(s.logo)


def test_attr_dir_not_exists(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    s = FileStorable.create()
    s.logo = {"extension": "EXT", "stream": b"STREAM"}
    s.save()
    shutil.rmtree(
        sheraf.attributes.files.FILES_ROOT_DIR + FileStorable.table + "/logo/"
    )
    FileStorable.read(s.id)


def test_model_dir_not_exists(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        attr = sheraf.FileAttribute()

    s = FileStorable.create()
    s.save()

    FileStorable.read(s.id)


def test_files_saved_if_file_exists(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    _files_dir = sheraf.attributes.files.FILES_ROOT_DIR + FileStorable.table + "/logo/"
    _first_content = {"extension": "1", "stream": b"STREAM"}

    s = FileStorable.create()
    s.logo = _first_content
    s.save()

    _second_content = {"extension": "2", "stream": b"SECOND"}
    s.logo = _second_content
    s.save()

    _s = FileStorable.read(s.id)
    assert _s.logo.extension == "2"
    assert _s.logo.stream == b"SECOND"
    assert _s.logo.exists()
    first_path = _files_dir + s.id + ".1"
    second_path = _files_dir + s.id + ".2"
    assert os.path.exists(first_path)
    assert os.path.exists(second_path)
    with open(second_path, "rb") as f:
        _content = f.read()
        assert b"SECOND" == _content
    rel_path_1 = os.path.relpath(first_path, sheraf.attributes.files.FILES_ROOT_DIR)
    assert (
        rel_path_1
        in sheraf.Database.current_connection().root()[
            "__sheraf_collected_files_to_remove"
        ]
    )
    rel_path_2 = os.path.relpath(second_path, sheraf.attributes.files.FILES_ROOT_DIR)
    assert (
        rel_path_2
        not in sheraf.Database.current_connection().root()[
            "__sheraf_collected_files_to_remove"
        ]
    )


def test_optional_files(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    _files_dir = sheraf.attributes.files.FILES_ROOT_DIR + FileStorable.table + "/logo/"
    s = FileStorable.create()
    s.logo = {"extension": "EXT", "stream": b"OPT_STREAM"}

    s.save()

    _s = FileStorable.read(s.id)
    assert _s.logo == sheraf.FileObject(extension="EXT", stream=b"OPT_STREAM")
    logo_path = _files_dir + s.id + ".EXT"
    assert os.path.exists(logo_path)
    with open(logo_path, "rb") as f:
        _content = f.read()
        assert b"OPT_STREAM" == _content


def test_optional_files_not_filled(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    _files_dir = sheraf.attributes.files.FILES_ROOT_DIR + FileStorable.table + "/logo/"
    s = FileStorable.create()

    s.save()

    _s = FileStorable.read(s.id)
    assert _s.logo is None
    assert not os.path.exists(_files_dir)


def test_delete_model_with_file_attribute(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()
        other = sheraf.FileAttribute()

    s = FileStorable.create()
    s.logo = {"extension": "EXT", "stream": b"STREAM"}
    s.save()
    s.delete()

    assert FileStorable.count() == 0
    rel_path = os.path.join(FileStorable.table, "logo", s.id + ".EXT")
    abs_path = os.path.join(sheraf.attributes.files.FILES_ROOT_DIR, rel_path)
    assert os.path.exists(abs_path)
    assert rel_path in sheraf.FilesGarbageCollector.instance()
    assert abs_path in sheraf.FilesGarbageCollector.instance()
    assert (
        rel_path
        in sheraf.Database.current_connection().root()[
            "__sheraf_collected_files_to_remove"
        ]
    )


def test_delete_model_with_file_attribute_and_relative_root_file_dir(
    sheraf_temp_dir, sheraf_connection
):
    class FileStorable(tests.UUIDAutoModel):
        my_file = sheraf.FileAttribute()

    s = FileStorable.create()
    s.my_file = sheraf.FileObject(stream=b"yolo", extension="txt")
    s.save()
    s.delete()

    rel_path = os.path.join(FileStorable.table, "my_file", s.id + ".txt")
    abs_path = os.path.join(sheraf.attributes.files.FILES_ROOT_DIR, rel_path)
    assert os.path.exists(abs_path)
    assert rel_path in sheraf.FilesGarbageCollector.instance()
    assert abs_path in sheraf.FilesGarbageCollector.instance()
    assert (
        rel_path
        in sheraf.Database.current_connection().root()[
            "__sheraf_collected_files_to_remove"
        ]
    )
    shutil.rmtree(sheraf.attributes.files.FILES_ROOT_DIR)


def test_delete_a_previously_saved_file(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()
        other = sheraf.FileAttribute()

    _files_dir = sheraf.attributes.files.FILES_ROOT_DIR + FileStorable.table + "/logo/"
    s = FileStorable.create()
    s.logo = {"extension": "EXT", "stream": b"STREAM"}
    s.other = {"extension": "OTH", "stream": b"OTHER"}
    s.save()
    _file_path = _files_dir + s.id + ".EXT"

    s.logo = None
    s.save()

    _s = FileStorable.read(s.id)
    assert _s.logo is None
    assert _s.other == s.other
    assert os.path.exists(_file_path)
    rel_path = os.path.relpath(_file_path, sheraf.attributes.files.FILES_ROOT_DIR)
    assert (
        rel_path
        in sheraf.Database.current_connection().root()[
            "__sheraf_collected_files_to_remove"
        ]
    )
    assert rel_path in sheraf.FilesGarbageCollector.instance()


def test_copy(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        logo = sheraf.FileAttribute()

    s1 = FileStorable.create()
    s1.logo = sheraf.FileObject(extension="EXT", stream=b"STREAM")
    s1.save()
    s2 = FileStorable.create()
    s2.logo = s1.logo
    s2.save()

    assert s1.logo.stream == s2.logo.stream
    assert s1.logo.relative_path() != s2.logo.relative_path()


def test_recursion(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        my_file = sheraf.FileAttribute()

    m = FileStorable.create()
    m.my_file = sheraf.FileObject(stream=b"", extension="txt")
    m.save()
    m = FileStorable.read(m.id)
    m.delete()  # il ne faut pas de recursion


def test_savemapping_mapping(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())
    s = FileStorable.create()
    s.file = sheraf.FileObject(stream=b"content", extension="txt")
    s.save()
    assert s.mapping["file"] == s.file.relative_path()


def test_readmapping_mapping(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())
    s = FileStorable.create()
    directory = os.path.join(
        sheraf.attributes.files.FILES_ROOT_DIR, FileStorable.table, "file"
    )
    os.makedirs(directory)
    file_path = os.path.join(directory, "file.txt")
    with open(file_path, "wb") as f:
        f.write(b"content")
    s.mapping["file"] = os.path.relpath(
        file_path, sheraf.attributes.files.FILES_ROOT_DIR
    )
    assert s.file.stream == b"content"
    assert s.file.extension == "txt"


def test_path_in_db_but_file_not_exists(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())
    s = FileStorable.create()
    file_path = os.path.join(FileStorable.table, "file", "file.txt")
    s.mapping["file"] = file_path
    assert s.file.relative_path() == file_path
    assert s.file.extension == "txt"
    assert not s.file.exists()
    with pytest.raises(IOError):
        assert s.file.stream
    s2 = FileStorable.create()
    with pytest.raises(IOError):
        s2.file = s.file


# ----------------------------------------------------------------------------------------------------------------------
def test_attributes(sheraf_temp_dir, sheraf_connection):
    _file = sheraf.FileObject(stream=b"STREAM", extension="txt")

    assert b"STREAM" == _file.stream
    assert "txt" == _file.extension


def test_save_file(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())

    _model = FileStorable.create()
    _model.file = sheraf.FileObject(stream=b"STREAM", extension="txt")

    _model.save()

    _model_from_base = FileStorable.read(_model.id)
    assert _model.file == _model_from_base.file


def test_retrocompatibility(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())

    _model = FileStorable.create()
    _model.file = {"stream": b"STREAM", "extension": "txt"}

    _model.save()

    assert sheraf.FileObject(stream=b"STREAM", extension="txt") == _model.file
    _model.file["extension"] = "png"
    _model.file["stream"] = b"STREAM2"
    assert "png" == _model.file["extension"]
    assert b"STREAM2" == _model.file["stream"]


# ----------------------------------------------------------------------------------------------------------------------
def test_save(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())

    _model = FileStorable.create()
    _model.file = {"stream": b"STREAM", "extension": "txt"}
    _model.save()

    _path = _model.file.relative_path()

    assert "file_storable_{}/file/{}.txt".format(
        sheraf.FileAttribute(), _model.id == _path,
    )


def test_read(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())

    _model = FileStorable.create()
    _model.file = {"stream": b"STREAM", "extension": "txt"}
    _model.save()
    _model = FileStorable.read(_model.id)

    _path = _model.file.relative_path()

    assert "file_storable_{}/file/{}.txt".format(
        sheraf.FileAttribute(), _model.id == _path,
    )


def test_not_model(sheraf_temp_dir, sheraf_connection):
    file = sheraf.FileObject(stream=b"STREAM", extension="txt")

    assert file.relative_path() is None


# ----------------------------------------------------------------------------------------------------------------------
def test_cler_files_garbage_collector_mixin(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())

    model = FileStorable.create()
    model.file = sheraf.FileObject(stream=b"hello", extension="txt")
    model.save()
    model.file.delete()
    other = FileStorable.create()
    other.file = sheraf.FileObject(stream=b"world", extension="txt")
    other.save()

    sheraf.FilesGarbageCollector.instance().clear()

    assert not os.path.exists(model.file.absolute_path())
    assert os.path.exists(other.file.absolute_path())
    root = sheraf.Database.current_connection().root()
    assert not root["__sheraf_collected_files_to_remove"]
    assert not sheraf.FilesGarbageCollector.instance()


def test_already_removed(sheraf_temp_dir, sheraf_connection):
    FileStorable = get_file_storable(sheraf.FileAttribute())

    model = FileStorable.create()
    model.file = sheraf.FileObject(stream=b"hello", extension="txt")
    model.save()
    model.file.delete()
    os.remove(model.file.absolute_path())

    sheraf.FilesGarbageCollector.instance().clear()


def test_directory_removed(sheraf_temp_dir, sheraf_connection):
    class FileStorable(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute()
        file = sheraf.FileAttribute()

    model = FileStorable.create()
    model.file = sheraf.FileObject(stream=b"hello", extension="txt")
    model.save()
    os.remove(model.file.absolute_path())
    os.rmdir(os.path.dirname(model.file.absolute_path()))

    sheraf.FilesGarbageCollector.instance().clear()

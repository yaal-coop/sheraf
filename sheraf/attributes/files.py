import io
import os

import sheraf
import sheraf.types
from sheraf.attributes.base import BaseAttribute
from sheraf.models.base import BaseModel

FILES_ROOT_DIR = "files/"


def set_files_root_dir(path):
    global FILES_ROOT_DIR
    FILES_ROOT_DIR = path


class FileObjectV1(object):
    def __init__(self, stream="", extension=""):
        # TODO rename stream to content
        self.model = None
        self.attribute_name = None
        self.stream = stream
        self.extension = extension

    def __repr__(self):
        return "<FileObjectV1 model='{}' attribute_name='{}'>".format(
            self.model.__class__.__name__, self.attribute_name
        )

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __eq__(self, other):
        return (
            isinstance(other, FileObjectV1)
            and self.stream == other.stream
            and self.extension == other.extension
        )

    def keys(self):
        return ["stream", "extension"]

    def associate(self, model, attribute_name):
        self.model = model
        self.attribute_name = attribute_name

    def relative_path(self):
        path = self.absolute_path()
        if not path:
            return None

        return self.relative_path_of(path)

    @staticmethod
    def relative_path_of(path):
        return os.path.relpath(path, FILES_ROOT_DIR)

    def absolute_path(self):
        if not self.model or not self.model.id:
            return None

        _dir = self.directory()
        _file_name = "%s.%s" % (self.model.id, self.extension)
        return os.path.join(_dir, _file_name)

    def directory(self):
        return self._directory_of(self.model, self.attribute_name)

    @classmethod
    def _directory_of(cls, model, attribute_name):
        return os.path.join(FILES_ROOT_DIR, model.table, attribute_name)

    def exists(self):
        try:
            next(
                self._iter_match_file_paths(
                    self.model, self.attribute_name, ignore_collected_to_remove=True
                )
            )
            return True
        except StopIteration:
            return False

    @classmethod
    def read(cls, model, attribute_name):
        try:
            file_path = next(
                cls._iter_match_file_paths(
                    model, attribute_name, ignore_collected_to_remove=True
                )
            )
            extension = os.path.splitext(file_path)[1].lstrip(".")
            with io.open(file_path, "rb") as f:
                file_instance = cls(extension=extension, stream=f.read())
                file_instance.associate(model, attribute_name)
                return file_instance
        except (StopIteration, OSError):
            pass

    @classmethod
    def _iter_match_file_paths(
        cls, model, attribute_name, ignore_collected_to_remove=False
    ):
        directory = cls._directory_of(model, attribute_name)
        if not os.path.isdir(directory):
            return

        for file_name in os.listdir(directory):
            root = os.path.splitext(file_name)[0]
            if root != model.id:
                continue

            path = os.path.join(directory, file_name)
            if ignore_collected_to_remove and path in FilesGarbageCollector.instance():
                continue

            yield path

    def write(self):
        self.delete()
        _path = self.absolute_path()
        _dir = os.path.dirname(_path)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        with io.open(_path, "wb") as f:
            f.write(self.stream)
            try:
                FilesGarbageCollector.instance().remove(self.relative_path())
            except KeyError:
                pass

    def delete(self):
        for path in self._iter_match_file_paths(self.model, self.attribute_name):
            FilesGarbageCollector.instance().add(path)


class FileObjectV2(FileObjectV1):
    def __init__(self, stream=None, extension=""):
        self.model = None
        self.attribute_name = None
        self.extension = extension
        self._content = stream

    def exists(self):
        if not self._is_new_model():
            return super(FileObjectV2, self).exists()

        return os.path.exists(self.absolute_path())

    @property
    def stream(self):
        if self._content is None:
            path = self.absolute_path()
            if path not in FilesGarbageCollector.instance():
                with io.open(self.absolute_path(), "rb") as f:
                    self._content = f.read()

        return self._content

    @stream.setter
    def stream(self, stream):
        self._content = stream

    @classmethod
    def read(cls, model, attribute_name):
        persisted_file_path = model._persistent.get(attribute_name)
        if not persisted_file_path:
            return super(FileObjectV2, cls).read(model, attribute_name)

        extension = os.path.splitext(persisted_file_path)[1].lstrip(".")
        file_instance = cls(extension=extension)
        file_instance.associate(model, attribute_name)
        return file_instance

    def _is_new_model(self):
        return self.model is not None and self.attribute_name in self.model._persistent

    def relative_path(self):
        if not self._is_new_model():
            return super(FileObjectV2, self).relative_path()

        return self.model._persistent[self.attribute_name]

    def absolute_path(self):
        if not self._is_new_model():
            return super(FileObjectV2, self).absolute_path()

        return os.path.join(FILES_ROOT_DIR, self.relative_path())

    def write(self):
        super(FileObjectV2, self).write()
        self.model._persistent[self.attribute_name] = self.relative_path()

    def delete(self):
        if not self._is_new_model():
            super(FileObjectV2, self).delete()
        else:
            FilesGarbageCollector.instance().add(
                self.model._persistent[self.attribute_name]
            )
            del self.model._persistent[self.attribute_name]

    def __repr__(self):
        return "<FileObjectV2 model='{}' attribute_name='{}'>".format(
            self.model.__class__.__name__, self.attribute_name
        )


FileObject = FileObjectV2


class FileAttribute(BaseAttribute):
    """FileAttribute stores a file on disk.

    prefer the use of :class:`~sheraf.attributes.blobs.BlobAttribute`
    instead.
    """

    def __init__(self, file_object_class=FileObject, **kwargs):
        self.FileObjectClass = file_object_class
        kwargs.setdefault("read_memoization", True)
        super(FileAttribute, self).__init__(**kwargs)

    def read(self, parent):
        # TODO: Implement deserialize instead of read
        return self.FileObjectClass.read(parent, self.key(parent))

    def write(self, parent, value):
        # TODO: Implement serialize instead of write

        if not value:
            return value

        if isinstance(value, dict):
            value = self.FileObjectClass(**value)

        elif isinstance(value.model, BaseModel) and not BaseModel.__eq__(
            value.model, parent
        ):
            value = self.FileObjectClass(stream=value.stream, extension=value.extension)
        value.associate(parent, self.key(parent))

        return value

    def save(self, parent):
        _file = getattr(parent, self.key(parent))
        if _file:
            _file.write()
        else:
            _file = self.FileObjectClass.read(parent, self.key(parent))
            if _file:
                _file.delete()

    def delete(self, parent):
        _file = getattr(parent, self.key(parent))
        if not _file:
            _file = self.FileObjectClass()
            _file.associate(parent, self.key(parent))
        _file.delete()


class FilesGarbageCollector(object):
    DEFAULT_TABLE = "__sheraf_collected_files_to_remove"
    _instance = None

    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self, table=DEFAULT_TABLE):
        self.table = table

    def _collected_paths(self):
        root = sheraf.Database.current_connection().root()
        if self.table not in root:
            root[self.table] = sheraf.types.Set()
        return root[self.table]

    @staticmethod
    def _relpath(path):
        if path.startswith(FILES_ROOT_DIR):
            return os.path.relpath(path, FILES_ROOT_DIR)
        return path

    def add(self, path):
        self._collected_paths().add(self._relpath(path))

    def remove(self, path):
        self._collected_paths().remove(self._relpath(path))

    def __contains__(self, path):
        return self._relpath(path) in self._collected_paths()

    def __bool__(self):
        return bool(self._collected_paths())

    def clear(self):
        for path in self._collected_paths():
            try:
                os.remove(os.path.join(FILES_ROOT_DIR, path))
            except OSError:
                pass
        self._collected_paths().clear()

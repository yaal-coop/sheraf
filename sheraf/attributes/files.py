import os
import sheraf
import sheraf.types
from sheraf.attributes.base import BaseAttribute
from sheraf.models.base import BaseModel

FILES_ROOT_DIR = "files/"


def set_files_root_dir(path):
    global FILES_ROOT_DIR
    FILES_ROOT_DIR = path  # pragma: no cover


class FileObject:
    def __init__(self, stream=None, extension=""):
        self.model = None
        self.attribute_name = None
        self.extension = extension
        self._content = stream

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __eq__(self, other):
        return (
            isinstance(other, FileObject)
            and self.stream == other.stream
            and self.extension == other.extension
        )

    def __repr__(self):
        return "<FileObject model='{}' attribute_name='{}'>".format(
            self.model.__class__.__name__, self.attribute_name
        )

    def exists(self):
        return os.path.exists(self.absolute_path())

    @property
    def stream(self):
        if self._content is None:
            path = self.absolute_path()
            if path not in FilesGarbageCollector.instance():
                with open(self.absolute_path(), "rb") as f:
                    self._content = f.read()

        return self._content

    @stream.setter
    def stream(self, stream):
        self._content = stream

    @classmethod
    def read(cls, model, attribute_name):
        persisted_file_path = model.mapping.get(attribute_name)
        if not persisted_file_path:
            return None

        extension = os.path.splitext(persisted_file_path)[1].lstrip(".")
        file_instance = cls(extension=extension)
        file_instance.associate(model, attribute_name)
        return file_instance

    def relative_path(self):
        if not self.model:
            return None

        if self.attribute_name in self.model.mapping:
            return self.model.mapping[self.attribute_name]

        file_name = "{}.{}".format(self.model.identifier, self.extension)
        path = os.path.join(self.directory(), file_name)

        return os.path.relpath(path, FILES_ROOT_DIR)

    def absolute_path(self):
        return os.path.join(FILES_ROOT_DIR, self.relative_path())

    def keys(self):
        return ["stream", "extension"]

    def associate(self, model, attribute_name):
        self.model = model
        self.attribute_name = attribute_name

    def directory(self):
        return os.path.join(FILES_ROOT_DIR, self.model.table, self.attribute_name)

    def write(self):
        if self.attribute_name in self.model.mapping:
            self.delete()

        path = self.absolute_path()
        directory = os.path.dirname(path)

        try:
            os.makedirs(directory)
        except OSError:
            pass

        with open(path, "wb") as f:
            f.write(self.stream)
            try:
                FilesGarbageCollector.instance().remove(self.relative_path())
            except KeyError:
                pass

        self.model.mapping[self.attribute_name] = self.relative_path()

    def delete(self):
        if not self.model or not self.attribute_name in self.model.mapping:
            return

        FilesGarbageCollector.instance().add(self.model.mapping[self.attribute_name])
        del self.model.mapping[self.attribute_name]


class FileAttribute(BaseAttribute):
    """
    This attribute stores a file on disk.
    """

    def __init__(self, file_object_class=FileObject, **kwargs):
        self.FileObjectClass = file_object_class
        kwargs.setdefault("read_memoization", True)
        super().__init__(**kwargs)

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

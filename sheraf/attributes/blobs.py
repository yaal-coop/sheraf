import ZODB

import sheraf.attributes.inlines
import sheraf.models
import sheraf.models.inline
import sheraf.types


class Blob(sheraf.models.inline.InlineModel):
    """Blob objects wrap the raw data from regular files.

    A :class:`ZODB.blob.Blob` is used to store the data.
    """

    @classmethod
    def create(cls, data=None, filename=None, stream=None, **kwargs):
        """
        :param data: the data to store in the blob
        :param filename: the name of the original file
        :param stream: If ``data`` is not set, data will be read from the ``stream`` stream.
        :param kwargs: optional attributes to set
        :return: A sheraf object wrapping a :class:`ZODB.blob.Blob` object, or ``None`` if this is an empty and unnamed file.
        """
        m = super(Blob, cls).create(**kwargs)

        stream_data = stream.read() if stream else None
        if data or filename or stream_data:
            m._persistent["blob"] = ZODB.blob.Blob(data or stream_data)
            m._persistent["original_name"] = filename

        return m

    def open(self):
        """Opens the stored blob file."""
        return self._persistent["blob"].open()

    @property
    def data(self):
        """The data contained in the blob."""
        f = self._persistent["blob"].open()
        try:
            return f.read()
        finally:
            f.close()

    @property
    def original_name(self):
        """The original filename."""
        return self._persistent["original_name"]

    @property
    def file_extension(self):
        """The original filename extension."""
        return self.original_name.split(".")[-1]

    @property
    def filename(self):
        """The name of the blob file."""
        f = self._persistent["blob"].open()
        try:
            return f.name
        finally:
            f.close()

    def delete(self):
        """Delete the object from the base."""
        self._persistent.clear()

    def __len__(self):
        return 1 if self._persistent else 0

    def __str__(self):
        return self._persistent.get("original_name")

    def __repr__(self):
        return '<Blob filename="{}">'.format(self._persistent.get("original_name"))

    def __bool__(self):
        return bool(self._persistent)

    def __getitem__(self, key):
        return getattr(self, key)

    def edit(
        self, value, addition=True, edition=True, deletion=False, replacement=False
    ):
        return value


class BlobAttribute(sheraf.attributes.inlines.InlineModelAttribute):
    """Stores a file on disk.

    This attribute is compatible with commits and rollbacks.
    """

    def __init__(self, model=Blob, **kwargs):
        super(BlobAttribute, self).__init__(model=model, **kwargs)

    def deserialize(self, value):
        if not value:
            return None

        return self.model._decorate(value)

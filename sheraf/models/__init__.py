"""Models are important.

Several models are availables.
"""

import uuid
import random
import sys

import BTrees

from .attributes import (
    DatedNamedAttributesModel,
    IntAttributesModel,
    NamedAttributesModel,
)
from .indexation import IndexedModel, IndexedModelMetaclass
from sheraf.attributes.simples import (
    IntegerAttribute,
    StringUUIDAttribute,
)


class UUIDIndexedModel:
    """Model using uuid4 as ids. Ids are stored as strings.

    >>> class MyUUIDModel(sheraf.IntIndexedModel):
    ...     table = "my_uuid_model"
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     MyIntModel.create().id
    "e4bb714e-b5a8-40d6-bb69-ab3b932fbfe0"
    """

    def make_unique_id(self):
        identifier = str(uuid.uuid4())
        while self.index_contains(identifier):
            identifier = str(uuid.uuid4())

        return identifier

    id = StringUUIDAttribute(default=lambda m: m.make_unique_id())


class IntIndexedModel:
    """Model using integers as ids.

    By default ids are 64bits integers.

    >>> class MyIntModel(sheraf.IntIndexedModel):
    ...     table = "my_int_model"
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     MyIntModel.create().id
    383428472384721983
    """

    MAX_INT = sys.maxsize

    def make_unique_id(self):
        identifier = random.randint(0, self.MAX_INT)
        while self.index_contains(identifier):
            identifier = random.randint(0, self.MAX_INT)

        return identifier

    id = IntegerAttribute(default=lambda m: m.make_unique_id())

    @classmethod
    def index_table_default(cls):
        return BTrees.LOBTree.LOBTree()


class BaseAutoModelMetaclass(IndexedModelMetaclass):
    @property
    def table(self):
        return self.__name__.lower()


class BaseAutoModel(metaclass=BaseAutoModelMetaclass):
    """
    :class:`~sheraf.models.indexation.BaseAutoModel` are regular
    models which 'table' parameter automatically takes the
    lowercase class name.
    It should only be used with unit tests.

    >>> class MyWonderfulClass(sheraf.AutoModel):
    ...    pass
    ...
    >>> assert MyWonderfulClass.table == "mywonderfulclass"
    >>> with sheraf.connection():
    ...     m = MyWonderfulClass.create()
    ...     assert m.table == "mywonderfulclass"
    """

    @property
    def table(self):
        return self.__class__.__name__.lower()


class IntIndexedNamedAttributesModel(
    NamedAttributesModel, IntIndexedModel, IndexedModel
):
    """The ids of this model are integers, and attributes are named."""


class IntOrderedNamedAttributesModel(
    NamedAttributesModel, IntIndexedModel, IndexedModel
):
    """The ids are 64bits integers, distributed ascendently starting at 0."""

    id = IntegerAttribute(default=lambda m: m.count())


class UUIDIndexedNamedAttributesModel(
    NamedAttributesModel, UUIDIndexedModel, IndexedModel
):
    """The ids of this model are UUID4, and attributes are named."""


class UUIDIndexedDatedNamedAttributesModel(
    DatedNamedAttributesModel, UUIDIndexedModel, IndexedModel
):
    """The ids of this model are UUID4, the attributes are named, and any
    modification on the model will update its modification datetime."""


class IntIndexedIntAttributesModel(IntAttributesModel, IntIndexedModel, IndexedModel):
    """The ids of this models are integers, and the ids of its attributes are
    also integers."""


class UUIDAutoModel(BaseAutoModel, UUIDIndexedDatedNamedAttributesModel):
    pass


class IntAutoModel(BaseAutoModel, IntOrderedNamedAttributesModel):
    pass


AutoModel = UUIDAutoModel
Model = UUIDIndexedDatedNamedAttributesModel

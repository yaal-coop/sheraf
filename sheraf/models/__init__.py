import random
import sys
import uuid

from sheraf.attributes.simples import IntegerAttribute
from sheraf.attributes.simples import StringUUIDAttribute

from .attributes import DatedNamedAttributesModel
from .attributes import IntAttributesModel
from .attributes import NamedAttributesModel
from .indexation import IndexedModel
from .indexation import SimpleIndexedModel


class UUIDIndexedModel:
    """Model using uuid4 as ids. Ids are stored as strings.

    >>> class MyUUIDModel(sheraf.IntIndexedModel):
    ...     table = "my_uuid_model"
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     MyIntModel.create().id
    "e4bb714e-b5a8-40d6-bb69-ab3b932fbfe0"
    """

    id = StringUUIDAttribute(default=lambda: str(uuid.uuid4())).index(primary=True)


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

    id = IntegerAttribute(default=lambda m: random.randint(0, m.MAX_INT)).index(
        primary=True
    )


class IntOrderedIndexedModel:
    """Model using increasing integers as ids.


    >>> class MyIntModel(sheraf.IntOrderedIndexedModel):
    ...     table = "my_int_model"
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     MyIntModel.create().id
    ...     MyIntModel.create().id
    0
    1
    """

    id = IntegerAttribute(default=lambda m: m.count()).index(primary=True)


class IntIndexedNamedAttributesModel(
    NamedAttributesModel, IntIndexedModel, IndexedModel
):
    """The ids of this model are integers, and attributes are named."""


class IntOrderedNamedAttributesModel(
    NamedAttributesModel, IntOrderedIndexedModel, IndexedModel
):
    """The ids are 64bits integers, distributed ascendently starting at 0."""


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


class AttributeModel(NamedAttributesModel, SimpleIndexedModel):
    """
    This model is expected to be used with :class:`~sheraf.attributes.models.IndexedModelAttribute`.
    Its usage is mainly the same as any :class:`~sheraf.models.indexation.BaseIndexedModel`.
    """


Model = UUIDIndexedDatedNamedAttributesModel

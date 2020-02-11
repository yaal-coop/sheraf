"""Models are important.

Several models are availables.
"""

from .attributes import (
    DatedNamedAttributesModel,
    IntAttributesModel,
    NamedAttributesModel,
)
from sheraf.attributes.simples import IntegerAttribute
from .indexation import BaseAutoModel, IndexedModel, IntIndexedModel, UUIDIndexedModel


class IntIndexedNamedAttributesModel(
    NamedAttributesModel, IntIndexedModel, IndexedModel
):
    """The ids of this model are integers, and attributes are named."""


class IntOrderedNamedAttributesModel(
    NamedAttributesModel, IntIndexedModel, IndexedModel
):
    """The ids are 64bits integers, distributed ascendently starting at 0."""

    id = IntegerAttribute(default=lambda m: len(m._table()))


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

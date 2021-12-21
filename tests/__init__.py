from sheraf.models import IntOrderedNamedAttributesModel
from sheraf.models import UUIDIndexedDatedNamedAttributesModel
from sheraf.models.indexation import IndexedModelMetaclass


class BaseAutoModelMetaclass(IndexedModelMetaclass):
    @property
    def table(self):
        return self.__name__.lower()


class BaseAutoModel(metaclass=BaseAutoModelMetaclass):
    """
    :class:`~sheraf.models.indexation.BaseAutoModel` are regular
    models which 'table' parameter automatically takes the
    lowercase class name.
    """

    @property
    def table(self):
        return self.__class__.__name__.lower()


class UUIDAutoModel(BaseAutoModel, UUIDIndexedDatedNamedAttributesModel):
    pass


class IntAutoModel(BaseAutoModel, IntOrderedNamedAttributesModel):
    pass

import datetime
import time

import sheraf.attributes.simples
from sheraf.models.base import BaseModel

DEPRECATED_META_DATETIME_FORMATS = ("%d/%m/%Y %H:%M:%S:%f", "%d/%m/%Y %H:%M")
DEPRECATED_DATE_TIME_FORMAT = "%d/%m/%Y %H:%M:%S:%f"


class IntAttributesModel(BaseModel):
    @classmethod
    def attribute_id(cls, name, attribute):
        return len(cls.attributes)


class NamedAttributesModel(BaseModel):
    @classmethod
    def attribute_id(cls, name, attribute):
        return name


class DatedNamedAttributesModel(NamedAttributesModel):
    """Model with creation and modification datetimes.

    Creation date is automatically saved. It will not change during
    object life. Date of modification is automatically saved when an
    attribute is modified and refers to the moment the transaction is
    committed. At creation time, date of modification and date of
    creation are equal.
    """

    _creation = sheraf.attributes.simples.SimpleAttribute(
        default=time.time,
        lazy=False,
    )

    def creation_datetime(self):
        """The date the object has been created. By now it refers to the date
        the method :func:`~sheraf.models.BaseModel.create` has been called, and
        not the date the transaction has been committed.

        :return: :class:`datetime.datetime` or None if the object has not been committed yet.
        """
        # TODO: The creation datetime should have the transaction commit datetime and not the object creation one

        if not self.mapping._p_oid:
            return None

        return self._deserialize_date(self._creation)

    def last_update_datetime(self):
        """The date of the last transaction commit involving a modification in
        this object.

        :return: :class:`datetime.datetime` or None if the object has not been committed yet.
        """
        return (
            self._deserialize_date(self.mapping._p_mtime)
            if self.mapping._p_mtime
            else None
        )

    @classmethod
    def _deserialize_date(cls, serialized_date):
        if isinstance(serialized_date, float):
            return datetime.datetime.fromtimestamp(serialized_date)

        for date_format in DEPRECATED_META_DATETIME_FORMATS:
            try:
                return datetime.datetime.strptime(serialized_date, date_format)
            except ValueError:
                pass

    def save(self):
        """Updates
        :func:`~sheraf.models.DatedNamedAttributesModel.last_update_datetime`
        value and saves all the model attributes."""

        self.mapping._p_changed = True
        return super().save()

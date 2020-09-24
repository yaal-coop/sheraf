[0.2.1] - 2020-09-24
====================

Changed
*******

- Fixed a bug when setting an indexed value after the object creation. :pr:`9`
- Fixed :class:`~sheraf.types.SmallDict` conflict resolution.

Removed
*******

- Python 3.5 support


Deprecated
**********

- :class:`~sheraf.attributes.files.FileObjectV1` is deprecated and will be removed in sheraf ``0.3.0``.
- :class:`~sheraf.models.AutoModel` are deprecated and will not be shipped with sheraf ``0.3.0``.
  However, they will still be available for development with sheraf tests.

[0.2.0] - 2020-04-03
====================

Added
*****
A whole indexation mechanism. :pr:`1`
  - A new :class:`~sheraf.attributes.models.IndexedModelAttribute` attribute, that holds a whole model indexation table.
  - A new :class:`~shera.models.AttributeMode`l class, to be used with :class:`~sheraf.attributes.models.IndexedModelAttribute`.
  - Method :meth:`~sheraf.attributes.base.BaseAttribute.index` method on :class:`~sheraf.attributes.base.BaseAttribute` to describe indexes.
  - Two check methods :func:`sheraf.batches.checks.check_attributes_index` and :func:`sheraf.batches.checks.check_model_index` to check the index tables integrity.
  - Method :meth:`~sheraf.models.indexation.BaseIndexedModel.index_table_rebuild` to rebuild an index table.
  - filter and order methods on QuerySet are faster on indexed attributes.

Removed
*******
- :func:`sheraf.models.BaseIndexedAttribute.make_id`
- :class:`~sheraf.indexes.Index`
- :class:`~sheral.attributes.base.BaseIndexedAttribute` *lazy_creation* parameter has been renamed *lazy*.

[0.1.2] - 2020-09-24
====================

Changed
*******

- Fixed a bug when setting an indexed value after the object creation. :pr:`9`

[0.1.1] - 2020-04-01
====================

Deprecated
**********

- :func:`sheraf.models.BaseIndexedAttribute.make_id`. Please use the 'default' parameter of your id :class:`~sheraf.attributes.base.BaseAttribute` instead.
- :class:`~sheraf.indexes.Index`
- :class:`~sheral.attributes.base.BaseIndexedAttribute` *lazy_creation* parameter has been deprecated, and has been renamed *lazy*.

Added
*****

- :class:`sheraf.attributes.collections.SmallDictAttribute`.

[0.1.0] - 2020-02-11
====================
- First version.

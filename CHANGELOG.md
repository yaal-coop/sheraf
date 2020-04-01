[Unreleased]
============

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

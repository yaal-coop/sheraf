[0.5.21] - 2021-12-15
=====================

Fixed
*****
- :meth:`~sheraf.models.base.BaseModel.assign` calls with
  :class:`~sheraf.attributes.models.ModelAttribute` that have
  several model class types.

[0.5.20] - 2021-11-17
=====================

Added
*****
- `__repr__` for :mod:`~sheraf.attributes.collections` attributes.

[0.5.19] - 2021-10-11
=====================

Added
*****
- :meth:`sheraf.cli.rebuild` have a `--fork` option to compute each batch in a separate
  process.

[0.5.18] - 2021-08-26
=====================

Fixed
*****
- Another :meth:`~sheraf.attributes.collections.SetAttribute.update` error with models.

[0.5.17] - 2021-08-26
=====================

Fixed
*****
- Another :meth:`~sheraf.attributes.collections.SetAttribute.update` error with models.

[0.5.16] - 2021-08-25
=====================

Fixed
*****
- :meth:`~sheraf.attributes.collections.SetAttribute.update` error with models.

[0.5.15] - 2021-08-25
=====================

Fixed
*****
- An error when several indexes exists on several common attributes,
  and one of them is unique, and a :class:`~sheraf.exceptions.UniqueIndexException`
  is raised.

[0.5.14] - 2021-08-25
=====================

Fixed
*****
- :meth:`~sheraf.attributes.collections.SetAttribute.update` error.

[0.5.13] - 2021-08-11
=====================

Added
*****
- :meth:`sheraf.cli.rebuild` have two options `--batch-size` that sets the number
  of elements to iterate between two savepoints, and `--commit` that replaces
  savepoints by real transaction commits.
- :class:`~sheraf.attributes.index.Index` has a `auto` parameter, that can
  disable the automatic use of the index.

[0.5.12] - 2021-08-10
=====================

Changed
*******
- :meth:`sheraf.cli.rebuild` now have a progress bar.
- Bugfix on :meth:`sheraf.models.indexation.BaseIndexedModel.index_table_rebuild`
  arguments are passed with `*args`.

[0.5.11] - 2021-08-04
=====================

Fixed
*****
- Bugfix on :meth:`sheraf.models.indexation.BaseIndexedModel.all`.

[0.5.10] - 2021-08-04
=====================

Added
******
- :meth:`sheraf.models.indexation.BaseIndexedModel.all` can take an index as argument.

[0.5.9] - 2021-07-27
====================

Added
*****
- Implemented :meth:`~sheraf.attributes.Attribute.on_change`
  as a shortcut for
  :meth:`~sheraf.attributes.Attribute.on_creation`,
  :meth:`~sheraf.attributes.Attribute.on_edition`, and
  :meth:`~sheraf.attributes.Attribute.on_deletion`.

[0.5.8] - 2021-07-26
====================

Changed
*******
- :func:`~sheraf.transactions.attempt` opens a connection if needed.

[0.5.7] - 2021-07-15
====================

Changed
*******
- Index related 'values' methods and parameters have been renamed 'index_keys'
- Index related 'search' methods and parameters have been renamed 'search_keys'
- Implemented Attribute :meth:`~sheraf.attributes.Attribute.index_keys_func` and
  :meth:`~sheraf.attributes.Attribute.search_keys_func`.

[0.5.6] - 2021-07-09
====================

Added
*****
- :meth:`sheraf.models.indexation.BaseIndexedModel.search_keys`,
  :meth:`sheraf.models.indexation.BaseIndexedModel.index_keys` and
  :meth:`sheraf.models.indexation.BaseIndexedModel.is_indexed_with`.

Changed
*******
- :class:`~sheraf.databases.Database` use :class:`contextvars.ContextVar`
  instead of :class:`threading.local`.

[0.5.5] - 2021-07-05
====================

Fixed
*****
- Fixed :class:`sheraf.queryset.QuerySet` concatenation when QuerySet
  is copied.

[0.5.4] - 2021-07-05
====================

Added
*****

- :func:`sheraf.health.utils.import_models` can take a model path.
- Implemented :meth:`~sheraf.attributes.Attribute.default` decorator.
- :class:`sheraf.queryset.QuerySet` supports concatenation

[0.5.3] - 2021-07-02
====================

Added
*****

- A :func:`~sheraf.cli.rebuild` that allows to rebuild an
  index from the command line.
- :class:`~sheraf.attributes.enum.EnumAttribute` supports comparisons.

[0.5.2] - 2021-06-29
====================

Changed
*******

- :class:`~sheraf.models.indexmanager.IndexManager` uses
  :class:`~BTrees.OOBTree.OOBTree` to store multiple indexes.

[0.5.1] - 2021-06-23
====================

Changed
*******

- Primary indexes are not editable.

Fixed
*****

- :class:`~sheraf.attributes.collections.SetAttribute` update method now
  casts the input value.

Added
*****

- :class:`~sheraf.attributes.models.ReverseModelAttribute` can support
  :class:`~sheraf.attributes.collections.SetAttribute`.

[0.5.0] - 2021-05-27
====================

Added
*****

- :class:`~sheraf.attributes.models.ModelAttribute` can take a relative
  model path.
- :meth:`~sheraf.attributes.index.Index.values` can return unique object
  instead of collections. :issue:`33`
- Implemented :meth:`~sheraf.attributes.Attribute.on_creation`,
  :meth:`~sheraf.attributes.Attribute.on_edition`, and
  :meth:`~sheraf.attributes.Attribute.on_deletion` callbacks.
  :issue:`40`

Changed
*******
- :meth:`sheraf.queryset.QuerySet.__getitem__` does not return a list anymore
  when one single value is accessed.
- :meth:`sheraf.queryset.QuerySet.count` does not consume the QuerySet.

Removed
*******
- :class:`~sheraf.attributes.BaseAttribute`


[0.4.21] - 2021-04-30
=====================

Changed
*******
- :meth:`sheraf.queryset.QuerySet.__bool__` does not consume the QuerySet.

[0.4.20] - 2021-04-30
=====================

Added
*******
- Implemented :meth:`sheraf.queryset.QuerySet.__bool__` :issue:`41`
- Improved :meth:`sheraf.queryset.QuerySet.__repr__` :issue:`31`
- Implemented :meth:`sheraf.queryset.QuerySet.__len__`

[0.4.19] - 2021-04-23
=====================

Changed
*******
- :class:`~sheraf.attributes.password.PasswordAttribute` comparision
  and encryption functions can be overloaded. :issue:`39`

[0.4.18] - 2021-04-20
=====================

Changed
*******
- Better error message for invalid
  :meth:`sheraf.types.largelist.LargeList.__getattr__` keys.

[0.4.17] - 2021-04-16
=====================

Fixed
*****
- Fixed a bug with :meth:`~sheraf.models.base.BaseModel.assign` and
  :class:`~sheraf.attributes.models.ModelAttribute` when passed model ids.

[0.4.16] - 2021-04-16
=====================

Added
*****
- :class:`~sheraf.attributes.models.ReverseModelAttribute` can be assigned model ids.

[0.4.15] - 2021-04-16
=====================

Changed
*******
- Refactored :class:`~sheraf.queryset.QuerySet` and removed slicing on negative
  values.

[0.4.14] - 2021-04-15
=====================

Changed
*******
- Refactored :class:`~sheraf.queryset.QuerySet` and removed a bit of the last
  commit to allow QuerySets to stay lazy.

[0.4.13] - 2021-04-14
=====================

Changed
*******
- Refactored :class:`~sheraf.queryset.QuerySet` and improved performance for search
  calls based on several indexes.

[0.4.12] - 2021-04-13
=====================

Fixed
*****
- Fixed a bug with :class:`~sheraf.attributes.enum.EnumAttribute` string casting.

[0.4.11] - 2021-04-12
=====================

Fixed
*****
- Fixed a bug with :class:`~sheraf.attributes.enum.EnumAttribute` equality.

[0.4.10] - 2021-04-09
=====================

Fixed
*****
- Fixed :class:`~sheraf.attributes.enum.EnumAttribute` can handle :class:`None` values.

[0.4.9] - 2021-04-07
====================

Fixed
*****
- Fixed :class:`~sheraf.attributes.enum.EnumAttribute` hashability.

[0.4.8] - 2021-04-06
====================

Fixed
*****
- Fixed :class:`~sheraf.attributes.enum.EnumAttribute` casting.

[0.4.7] - 2021-04-06
====================

Added
*****
- Implemented :class:`~sheraf.attributes.enum.EnumAttribute`.

[0.4.6] - 2021-03-31
====================

Added
*****
- Implemented :class:`~sheraf.attributes.models.ReverseModelAttribute`. :issue:`35`


[0.4.5] - 2021-02-26
====================

Fixed
*****
- QuerySet :meth:`~sheraf.queryset.QuerySet.count` shortcuts do transform input values.


[0.4.4] - 2021-02-26
====================

Added
*****

- Model :meth:`~sheraf.models.indexation.IndexedModel.count` method can take an index name
  as a parameter.
- QuerySet :meth:`~sheraf.queryset.QuerySet.count` method is far more quicker when there is
  only one indexed filter.

[0.4.3] - 2021-02-23
====================

Added
*****

- Implemented :class:`~sheraf.attributes.password.PasswordAttribute`. :issue:`5`

[0.4.2] - 2021-02-21
====================

Added
*****

- :meth:`~sheraf.attributes.index.Index.values` is given the attributes
  values in positional argument if it is assigned to one or several
  attributes.

Changed
*******

- BaseAttribute renamed in :class:`~sheraf.attributes.Attribute`.

[0.4.1] - 2021-02-18
====================

Fixed
*****

- :class:`~sheraf.attributes.index.Index` inheritance is fixed.
- :class:`~sheraf.attributes.index.Index` update :class:`~sheraf.attributes.Attribute`
  on deletion.
- :meth:`~sheraf.databases.connection` can take a ``reuse`` parameter.


[0.4.0] - 2021-02-17
====================

Added
*****

- :class:`~sheraf.attributes.index.Index` can be used directly as
  :meth:`~sheraf.models.indexation.IndexedModel` parameters. :pr:`11`
- :meth:`sheraf.types.largelist.LargeList.remove` can take a `all` argument.
- :meth:`sheraf.types.largelist.LargeList.append` can take a `unique` argument.
- :class:`~sheraf.attributes.index.Index` can have several
  :class:`~sheraf.attributes.Attribute` :issue:`23`


[0.3.8] - 2021-02-05
====================

Changed
*******

- `batches` have been renamed `health`

Fixed
*****

- Fixed a bug happening when creating a :meth:`~sheraf.models.indexation.IndexedModel` with
  an indexed :class:`~sheraf.attributes.models.ModelAttribute` not initialized at creation.


[0.3.7] - 2021-02-03
====================

Added
*****

- :class:`~sheraf.attributes.index.Index` have a `nullok`
  parameter, `True` by default, that allows indexation of falseworthy values.
  :issue:`16`

[0.3.6] - 2021-02-03
====================

Changed
*******

- Checks and migrations now use rich. :issue:`12`


Fixed
*****

- Fixed a bug with indexed :class:`~sheraf.attributes.simples.IntegerAttribute`.

[0.3.5] - 2021-01-29
====================

Added
*****

- :func:`~sheraf.transactions.commit` can take no argument.
- :meth:`~sheraf.models.base.BaseModel.edit` has a `strict` parameter. :issue:`18`

-[0.3.4] - 2021-01-28
=====================

Added
*****

- :class:`~sheraf.attributes.blobs.BlobAttribute` shortcut for common web frameworks.


[0.3.3] - 2021-01-27
====================

Added
*****

- :class:`~sheraf.attributes.simples.TypeAttribute` can have `None` values.

[0.3.2] - 2021-01-27
====================

Added
*****

- :class:`~sheraf.attributes.index.Index` have a `noneok`
  parameter, `False` by default, that allows indexation of `None` values.
  :issue:`16`

[0.3.1] - 2021-01-21
====================

Changed
*******

- Fixed indexation of generic :class:`~sheraf.attributes.models.ModelAttribute`.

[0.3.0] - 2021-01-20
====================

Added
*****

- :class:`~sheraf.attributes.Attribute` can have custom
  :meth:`~sheraf.attributes.Attribute.values` and
  :meth:`~sheraf.attributes.Attribute.methods` that will
  be used by default if
  :meth:`~sheraf.attributes.Attribute.index` `values_func` and
  `search_func` are not provided.
- Indexation is possible by default with :class:`~sheraf.attributes.collections.ListAttribute`
  and :class:`~sheraf.attributes.collections.SetAttribute`. :issue:`11`
- Indexation is possible by default with :class:`~sheraf.attributes.models.ModelAttribute`.
  :issue:`10`
- :class:`~sheraf.attributes.models.ModelAttribute` can have several model classes. :issue:`13`

Changed
*******

- Use `~BTrees.OOBTree.OOTreeSet` instead of `~orderedset.OrderedSet`.
- :class:`~tests.AutoModel` has moved in the tests directory.

Removed
*******
- :class:`~sheraf.attributes.files.FileObjectV1` has been removed.

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
  - Method :meth:`~sheraf.attributes.Attribute.index` method on :class:`~sheraf.attributes.Attribute` to describe indexes.
  - Two check methods :func:`sheraf.batches.checks.check_attributes_index` and :func:`sheraf.batches.checks.check_model_index` to check the index tables integrity.
  - Method :meth:`~sheraf.models.indexation.BaseIndexedModel.index_table_rebuild` to rebuild an index table.
  - filter and order methods on QuerySet are faster on indexed attributes.

Removed
*******
- :func:`sheraf.models.BaseIndexedAttribute.make_id`
- :class:`~sheraf.indexes.Index`
- :class:`~sheral.attributes.BaseIndexedAttribute` *lazy_creation* parameter has been renamed *lazy*.

[0.1.2] - 2020-09-24
====================

Changed
*******

- Fixed a bug when setting an indexed value after the object creation. :pr:`9`

[0.1.1] - 2020-04-01
====================

Deprecated
**********

- :func:`sheraf.models.BaseIndexedAttribute.make_id`. Please use the 'default' parameter of your id :class:`~sheraf.attributes.Attribute` instead.
- :class:`~sheraf.indexes.Index`
- :class:`~sheral.attributes.BaseIndexedAttribute` *lazy_creation* parameter has been deprecated, and has been renamed *lazy*.

Added
*****

- :class:`sheraf.attributes.collections.SmallDictAttribute`.

[0.1.0] - 2020-02-11
====================
- First version.

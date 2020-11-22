Installation, upgrades
######################

.. note :: Until version `1.0.0`, sheraf is considered as beta, and while we do all we can
   to make upgrades as smooth as possible, bugs and breaking changes still have a chance
   to occur.

How to install?
===============

``pip install sheraf``

There are several variants of the sheraf package:

- ``sheraf[zeo]`` installs the dependencies to work with `ZEO`_.
- ``sheraf[relstorage]`` installs the dependencies to work with `relstorage`_.
- ``sheraf[all]`` installs all those dependencies.

.. _ZEO: https://zeo.readthedocs.io
.. _relstorage: https://relstorage.readthedocs.io

Versioning policy
=================

Bugfix versions
---------------

Bugfix versions are non-breaking. You can upgrade from a bugfix version to another directly (from ``X.Y.A`` to ``X.Y.B``). No checks, no code change, and no migration are required.

Minor versions
--------------

Minor versions deprecate and smoothly break the code compatibility, but they do not break the data compatibility. To migrate from a minor version to another (from ``X.A.*`` to ``X.B.*``) you need to:

- Make sur the version you target is consecutive to the version you have. For instance, if you have sheraf ``3.4`` and want to upgrade to ``3.7``, you first need to upgrade to ``3.5``, then you need to upgrade to ``3.6`` before you are able to upgrade to ``3.7``;
- Make sure that you are using the last bugfix version of your minor version. For instance, if you are using sheraf ``3.5.6`` and want to upgrade to ``3.6``, you need to upgrade to ``3.5.10`` before;
- Read the changelog for every intermediary version between you current version and the new one (i.e. everything from ``3.5.6`` to ``3.6.0``);
- Run your unit tests, and fix all the :class:`~DeprecationWarning` your test runner reports;
- Facultatively, check and fix your database in all your production environments with :func:`~sheraf.batches.checks.print_health`; This step is not required.
- Upgrade to the new minor version you target. It is recommended that you upgrade to the most recent bugfix version of the new minor version. For example, once you are at ``3.5.10``, upgrade directly to ``3.6.13``.

.. warning :: If you do not cover enough code with you unit tests, you may not trigger all the :class:`~DeprecationWarning` you need to fix to be able to upgrade. This is your responsability to have your code well covered.

Major versions
--------------

Major version break code and data compatibility. Migrations and manual interventions are needed to upgrade. To migrate from a major version to another (from ``A.*.*`` to ``B.*.*``) you need to:

- Upgrade consecutively to all the minor versions separating you from the major version you target;
- You NEED to check and fix your database in all your production environments with :func:`~sheraf.batches.checks.print_health`;
- Then upgrade to the major version. Read the Changelog with attention, it may have further recommendations.

How to contribute?
==================

- Use your brain and your keyboard to produce code.
- Use `black` to format your code.
- Use `docformatter` to format the documentation.
- Check that `tox` agrees with your modifications.

.. _black: https://black.readthedocs.io
.. _docformatter: https://github.com/myint/docformatter
.. _tox: https://tox.readthedocs.io

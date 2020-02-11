ZODB Model Layer

sheraf is an overlay over ZODB. It provides a high level interface to save and read your data.

[![Documentation Status](https://readthedocs.org/projects/sheraf/badge/?version=latest)](https://sheraf.readthedocs.io/en/latest/?badge=latest)

# Installation
sheraf is compatible with Python 3.5+

    poetry add sheraf
    # or
    pip install sheraf

If you need pytest fixtures for your project check out [pytest-sheraf](https://gitlab.com/yaal/sheraf).

    pip install pytest-sheraf

The documentation is [hosted here](https://sheraf.readthedocs.io/en/latest/).


# Contributing

Bug reports and pull requests are highly encouraged!

 - Test some code : `poetry run pytest` and `poetry run tox`
 - Format code : `black`
 - Generate documentation : `poetry run tox -e docs`

# Documentation

    poetry run tox -e doc
    open build/sphinx/html/index.html

# Development installation

    sheraf use poetry as its main build tool. Do not hesitate to check [the documentation](https://python-poetry.org/docs/).

    poetry install --extras all

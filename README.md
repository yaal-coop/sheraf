ZODB Model Layer

sheraf is an overlay over ZODB. It provides a high level interface to save and read your data.

# Installation
sheraf is compatible with Python 3.5+

    poetry add sheraf
    # or
    pip install sheraf

If you need pytest fixtures for your project check out pytest-sheraf

    pip install pytest-sheraf

The documentation is [hosted here](https://deploy.yaal.fr/doc/sheraf/default/).


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

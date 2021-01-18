# A versatile ZODB abstraction layer

sheraf is an overlay over ZODB. It provides a high level interface to save and read your data.

## Installation

sheraf is compatible with Python 3.6+

    poetry add sheraf
    # or
    pip install sheraf

If you need pytest fixtures for your project check out [pytest-sheraf](https://gitlab.com/yaal/pytest-sheraf). There are also [sheraf fixtures for unittest](https://gitlab.com/yaal/unittest-sheraf).

    pip install pytest-sheraf

The documentation is [hosted here](https://sheraf.readthedocs.io/en/latest/).

## Contributing

Bug reports and pull requests are highly encouraged!

 - Test some code : `poetry run pytest` and `poetry run tox`
 - Format code : `black`
 - Generate documentation : `poetry run tox -e doc`

## Documentation

    poetry run tox -e doc
    open build/sphinx/html/index.html

## Development installation

sheraf use poetry as its main build tool. Do not hesitate to check [the documentation](https://python-poetry.org/docs/).

    poetry install --extras all

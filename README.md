# A versatile ZODB abstraction layer

sheraf is a wrapper library around [ZODB](https://www.zodb.org) that provides models management and indexation. It aims to make the use of `ZODB` simple by providing ready-to-use tools and explicit tools. sheraf is currently compatible with `ZODB 5` and `python 3.7+`.

You can expect sheraf to:

- Do few things, but do them right;
- Be simple enough so beginners can do a lot with a few lines;
- Be powerful enough and tunable for python experts;
- Have a simple and expressive code, that allows you to hack it if needed.

## Installation

sheraf is compatible with Python 3.7+

    poetry add sheraf
    # or
    pip install sheraf

If you need pytest fixtures for your project check out [pytest-sheraf](https://gitlab.com/yaal/pytest-sheraf). There are also [sheraf fixtures for unittest](https://gitlab.com/yaal/unittest-sheraf).

    pip install pytest-sheraf

## Contributing

Bug reports and pull requests are highly encouraged!

 - Test some code : `poetry run pytest` and `poetry run tox`
 - Format code : `black`
 - Generate documentation : `poetry run tox -e doc`

## Documentation

You can build it with the following commands, or read it on [readthedocs](https://sheraf.readthedocs.io/en/latest/).

    poetry run tox -e doc
    open build/sphinx/html/index.html

## Development installation

sheraf use poetry as its main build tool. Do not hesitate to check [the documentation](https://python-poetry.org/docs/).

    poetry install --extras all

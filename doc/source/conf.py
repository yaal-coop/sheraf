#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../sheraf"))

import sheraf

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_issues",
    "recommonmark",
]

templates_path = ["_templates"]
source_suffix = [".rst", ".md"]
master_doc = "index"
project = "sheraf"
copyright = "2020, Yaal"
author = "Yaal"

version = "{}.{}".format(
    sheraf.version.__version_info__[0], sheraf.version.__version_info__[1]
)

release = sheraf.__version__
language = None
exclude_patterns = []
pygments_style = "sphinx"
todo_include_todos = False

intersphinx_mapping = {
    "btrees": ("https://btrees.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/3", None),
    "persistent": ("https://persistent.readthedocs.io/en/latest/", None),
    "relstorage": ("https://relstorage.readthedocs.io/en/latest/", None),
    "werkzeug": ("https://werkzeug.palletsprojects.com/en/master/", None),
    "wtforms": ("https://wtforms.readthedocs.io/en/stable/", None),
    "ZODB": ("https://zodb-docs.readthedocs.io/en/latest/", None),
    "zodburi": ("https://docs.pylonsproject.org/projects/zodburi/en/latest/", None),
}

issues_uri = "https://gitlab.com/yaal/sheraf/-/issues/{issue}"
issues_pr_uri = "https://gitlab.com/yaal/sheraf/-/merge_requests/{pr}"
issues_commit_uri = "https://gitlab.com/yaal/sheraf/-/commit/{commit}"

# -- Options for HTML output ----------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = []


# -- Options for HTMLHelp output ------------------------------------------

htmlhelp_basename = "sherafdoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}
latex_documents = [(master_doc, "sheraf.tex", "sheraf Documentation", "Yaal", "manual")]

# -- Options for manual page output ---------------------------------------

man_pages = [(master_doc, "sheraf", "sheraf Documentation", [author], 1)]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "sheraf",
        "sheraf Documentation",
        author,
        "sheraf",
        "One line description of project.",
        "Miscellaneous",
    )
]

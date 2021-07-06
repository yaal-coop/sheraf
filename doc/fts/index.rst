.. _fts:

=======================
Advanced string indexes
=======================

Let us see how to apply all the concepts we saw earlier to build a small full-text search engine with sheraf.

.. toctree::
    :glob:
    :maxdepth: 2

    **

Full-text search takes a query from a user, and tries to match documents containing the words in the query.
Generally we expect it to tolerate typos, and understand plural forms, conjugations and variants of the same
word (for instance *work* and *working* should be considered as very close). We also expect the result to be
ordered by pertinence. For instance, a document containing several times a search word should appear in a better
position than a document where it only appears once.

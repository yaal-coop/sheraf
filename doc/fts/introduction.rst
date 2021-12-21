General concepts
================

Those expectations leads to several treatments on the text we should index, and on the search queries. Here
are some steps that can appear:

Alphabet reduction
------------------

To deal with a lesser number of character, you can map your alphabet to a subset. You can ignore the case in
the indexation and queries, and consider everything is lowercase.

Another technique is the accent folding. This is about considering that the accented letters (for instance **e**, **é** and **è**) are
equivalent, and ignoring accents in indexation and querying. This can be done for instance with :func:`unidecode.unidecode`.

Stemming or lemmatization
-------------------------

Stemming is about deleting prefixes and suffixes, and reducing a word to
another word that represents its sense. For instance *translations* and *translated* can both be reduced to
*translat*. Both words refer to the same concept we call here *translat*, even if it is not a proper English word.
Thus, a query containing *translations* can return results containing *translated*.
With the proper tooling, this step is done automatically, but depends on the language. Indeed different languages have different
prefixes and suffixes. Stemming can be done with librarys like `pystemmer <https://github.com/snowballstem/pystemmer>`_
or `nltk <https://github.com/nltk/nltk>`_.

lemmatization is a variant of stemming that only reduce words to existing words. For instance *translations* and
*translated* could be reduced to *translate*. This is slower than stemming, but is more accurate. You can
lemmatize with libraries like nltk.

Typo correction
---------------
*errare humamun est*, this adage is still true with query search. Typo correction is about
allowing the users to make little mistakes in the information they index or query, and still match relevant results.
This is sometimes called *fuzzy searching*.

Levenshtein and variants
~~~~~~~~~~~~~~~~~~~~~~~~

Some algorithms like the `Levenshtein distance <https://en.wikipedia.org/wiki/Levenshtein_distance>`_ or the
`Damerau-Levenshtein <https://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance>`_ allow to estimate
the similarity between two words. The promiximity of the variant letters, their numbers etc. are taken in account.
The distance consist in the minimum number of operations needed to transform one word to the other (insertion,
deletion and substitution, for Levenshtein, and (insertion, deletion, substitution and transposition for
Damerau-Levenshtein).
Computing the Levenshtein distance between one query word and a set of reference words is tedious, since you have to
compute the distance between your query word and each word in the set. Some datastructures like the
`BK Trees <https://en.wikipedia.org/wiki/BK-tree>`_ allow you to organize your reference set so you just need
to compute the Levenshtein distance against a subset of words before you find your matches.

The Levenshtein distance is implemented in libraries like `fuzzywuzzy <https://github.com/seatgeek/fuzzywuzzy>`_ or
`python-levenshtein <https://github.com/ztane/python-Levenshtein/>`_. :mod:`difflib` also bring string similarity
methods.

SymSpell
~~~~~~~~

Other algorithms like Wolf Garbe's LinSpell or
`SymSpell <https://medium.com/@wolfgarbe/1000x-faster-spelling-correction-algorithm-2012-8701fcd87a5f>`_ take a
different approach but seem to be faster than BK/Damerau-Levenshtein. It indexes a word with
its deletion transformations to decrease the transformations to compute.
Thus Symspell especially trades query speed
against memory usage and pre-computation speed.

Another complementary approach is to check words against dictionnaries and then correct them. This for instance is what does
`pyenchant <https://pyenchant.github.io/pyenchant/>`_, based on tools like `aspell <http://aspell.net/>`_. Note
that pyenchant allows you to define your own dictionnary.

Restricting user input
~~~~~~~~~~~~~~~~~~~~~~

Sometimes the better solution to a problem is actually to not having to deal with it. When it is possible,
restricting the user inputs to a valid set of data prevent you to deal with data imprecisions.
This is generally implemented by user interface tricks, such as *suggestions as you type*. However, that
may be difficult to instore when the valid data set is very large or motley.

Pertinence matching
-------------------

Pertinence is about knowing if a word takes an important place in a document. For instance
a document where a searched word appears several time is more relevant than a document where it appears only
once. A document where a searched word appears in the title is more pertitent than a document where it appears
in the footer. You can do this with some algorithms family like `BM25 <https://en.wikipedia.org/wiki/Okapi_BM25>`_.
BM25 is implemented for instance in `rank_bm25 <https://github.com/dorianbrown/rank_bm25>`_.

Depending on the number of documents, the size of the document, the nature of your data (natural language, small sets
of terms you choosed, etc.), you might want to use and tune this or that technique. There is no magical formula to
give perfect results. You can also define strategies where you use some of those techniques only when exact matches
does not return good enough results.
Some libraries like `Whoosh <https://whoosh.readthedocs.io/>`_ implement almost all the previous concepts,
and it also manages the storing of indexes.

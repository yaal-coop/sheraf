.. _fts:

=======================
Advanced string indexes
=======================

Let us see how to apply all the concepts we saw earlier to build a small full-text search engine with sheraf.

.. toctree::

   General concepts
   Use cases

Full-text search takes a query from a user, and tries to match documents containing the words in the query.
Generally we expect it to tolerate typos, and understand plural forms, conjugations and variants of the same
word (for instance *work* and *working* should be considered as very close). We also expect the result to be
ordered by pertinence. For instance, a document containing several times a search word should appear in a better
position than a document where it only appears once.

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

Use cases
=========

Let us see what we can do with those concepts in sheraf. Wo do not pretend sheraf can replace tools like Whoosh,
but to experiment the flexibility sheraf offers.

Name completion
---------------

Imagine we have a cowboy database, and we would like to be able to find cowboys by their names. We have a
input field, and we would like to suggest valid cowboy names as the user is typing. Then we can enforce
the user to choose one of the valid names to the search. The idea is to find cowboy names that are prefixed
by the user input. For instance, if we have a cowboy name *George Abitbol*, then he would appear in the
suggestion box if we type *Geor* or *abit*.

.. note::

   This is just an example. In a real situation, querying the database each time an user
   presses a key does not seem to be a good idea. Periodically generating and caching the valid data
   you want to suggest sounds a better way to achieve this.

- We do not have to understand a whole natural language like English, because proper nouns won't appear in a dictionnary.
  Also each name stands for a unique person, and there is no name synonyms. In that case it seems useless to deal with
  **stemming or lemmatization**.
- We can consider our search queries will be indexed maximum once for each cowboy. Thus, we can avoid using **pertinence
  algorithms**.
- We just want to find approximate matches, so case and accents won't matter. Thus, we can use **alphabet reduction
  techniques**.
- We can provide useful data to users before they can make a typo, so **typo correction algorithms** are
  not needed here.

.. code-block:: python

    >>> import unidecode
    >>> import itertools
    >>> def cowboy_indexation(string):
    ...     lowercase = string.lower()
    ...     unaccented = unidecode.unidecode(lowercase)
    ...     names = unaccented.split(" ")
    ...     permutations = {
    ...         " ".join(perm)
    ...         for perm in itertools.permutations(names, len(names))
    ...     }
    ...     return {
    ...         name[:x]
    ...         for name in permutations
    ...         for x in range(len(name))
    ...         if name[:x]
    ...     }
    ...
    >>> def cowboy_query(string):
    ...     lowercase = string.lower()
    ...     return {unidecode.unidecode(lowercase)}
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboys_prefixes"
    ...     name = sheraf.StringAttribute().index(
    ...         values=cowboy_indexation,
    ...         search=cowboy_query,
    ...     )

The indexation method sets the names in lowercase, remove the accents, then build all the possible combinations
of words in the name (because we want the user to be able to type *George Abitbol* or *Abitbol George*), and then
build all the possible prefixes for those combinations.

.. code-block:: python

   >>> with sheraf.connection(commit=True):
   ...    george = Cowboy.create(name="George Abitbol")
   ...
   ...    assert [george] == Cowboy.search(name="George")
   ...    assert [george] == Cowboy.search(name="gEoRgE")
   ...    assert [george] == Cowboy.search(name="Abitbol")
   ...    assert [george] == Cowboy.search(name="geo")
   ...    assert [george] == Cowboy.search(name="abi")
   ...    assert [george] == Cowboy.search(name="George Abi")
   ...    assert [george] == Cowboy.search(name="Abitbol Geo")
   ...
   ...    assert [] == Cowboy.search(name="Peter")
   ...    assert [] == Cowboy.search(name="eorge")

We can see that any prefix of any words in the name is enough to find back a cowboy.

.. todo:: Order the results by the number of occurences.

Name search
-----------

Consider a simple problem: we have a cowboy database, and we need to be able to find them by their names
(and we have control on the user input):

- We do not have to understand a whole natural language like English, because proper nouns won't appear in a dictionnary.
  Also each name stands for a unique person, and there is no name synonyms. In that case it seems useless to deal with
  **stemming or lemmatization**.
- We can consider our search queries will be indexed maximum once for each cowboy. Thus, we can avoid using **pertinence
  algorithms**.
- We just want to find approximate matches, so case and accents won't matter. Thus, we can use **alphabet reduction
  techniques**.
- We want to allow users to misspell cowboy names, so we might want to use **typo correction algorithms**.

Let us start with a simple implementation:

.. code-block:: python

    >>> import unidecode
    >>> import itertools
    >>> def cowboy_indexation(string):
    ...     lowercase = string.lower()
    ...     unaccented = unidecode.unidecode(lowercase)
    ...     return {
    ...         word[x:y]
    ...         for word in unaccented.split(" ")
    ...         for x, y in itertools.combinations(range(len(word)+1), r=2)
    ...     }
    ...
    >>> def cowboy_query(string):
    ...     lowercase = string.lower()
    ...     unaccented = unidecode.unidecode(lowercase)
    ...     return unaccented.split(" ")
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboys_1"
    ...     name = sheraf.StringAttribute().index(
    ...         values=cowboy_indexation,
    ...         search=cowboy_query,
    ...     )

Here we wrote two indexations and query functions that we use for the cowboy names indexation.
The query method lowers the string, removes the accents, and returns every words in the string.
The indexation method does computes every subwords in almost the same steps except it returns
every subwords for every words in the string. Let us see how it behaves:

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol Junior")
    ...
    ...     assert [george] == Cowboy.search(name="George Abitbol Junior")
    ...     assert [george] == Cowboy.search(name="george")
    ...     assert [george] == Cowboy.search(name="geor")
    ...     assert [george] == Cowboy.search(name="g")
    ...     assert [george] == Cowboy.search(name="GeOrGe")
    ...
    ...     assert [] == Cowboy.search(name="georgio")
    ...     assert [] == Cowboy.search(name="georgettetito")


We see that we can query the exact full name, just the first or second name, a substring of
the first or second name, any case variants. However there are two problems with this implementation:

- our indexation mechanism does not allow for typos and misspellings (searching for *georgio* did not
  find anything)
- searching for one character returns the whole cowboy name. That seems a bit excessive so we could
  probably save some space.

Let us edit our indexation and query function so they tolerate typos. We can use a naive algorithm
inspired from SymSpell. Basically the idea is to index a name and variants of this name with typos,
and then search for a term and variants of this term with typos. Unlike the Levenshtein algorithm,
SymSpell only consider one operation to calculate distance between words, that is **deletion**. So
for each name, we will index it with missing letters, and when we will query a term, we will query
it with missing letters too. We can set a limit to how many deletions can occur before we consider
a word is too different from another. Here, let us consider 2.

The rationale is:

- If the query term has at most 2 letter more than the indexed term, we can match them by removing
  two letters from the query term.
- On the other hand, if the query term has at most 2 letter less than the indexed term, we can match
  them by removing two letters from the indexed term.
- If both terms have at least two different character, we can match them by removing the different
  letters in both terms.

.. code-block:: python

    >>> def subwords(string, max_deletions=2):
    ...     deletes = {string}
    ...     queue = [string]
    ...     while len(queue) > 0:
    ...         word = queue.pop()
    ...         if len(word) > max(1, len(string) - max_deletions):
    ...             for character in range(len(word)):
    ...                 word_minus_c = word[:character] + word[character + 1:]
    ...                 deletes.add(word_minus_c)
    ...                 queue.append(word_minus_c)
    ...     return deletes

We can take back our functions, and use deletions within a range of 2 instead of all
possible subwords. Now let us check our previous tests.

.. code-block:: python

    >>> def cowboy_indexation(string):
    ...     lowercase = string.lower()
    ...     unaccented = unidecode.unidecode(lowercase)
    ...     return {
    ...         subword
    ...         for word in unaccented.split(" ")
    ...         for subword in subwords(word)
    ...     }
    ...
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboys_2"
    ...     name = sheraf.StringAttribute().index(
    ...         values=cowboy_indexation,
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol Junior")
    ...
    ...     assert [george] == Cowboy.search(name="George Abitbol De La Muerte")
    ...     assert [george] == Cowboy.search(name="george")
    ...     assert [george] == Cowboy.search(name="georges")
    ...     assert [george] == Cowboy.search(name="geor")
    ...     assert [george] == Cowboy.search(name="GeOrGe")
    ...     assert [george] == Cowboy.search(name="georgio")
    ...
    ...     assert [] == Cowboy.search(name="g")
    ...     assert [] == Cowboy.search(name="geo")
    ...     assert [] == Cowboy.search(name="georgettetito")

We see that we can query the exact full name, just the first or second name, a substring of
the first or second name, any case variants, and with a tolerance for 2 letters changes.

Document search
---------------

TBD.

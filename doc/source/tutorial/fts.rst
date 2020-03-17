.. _fts:

A full-text search engine
=========================

Let us see how to apply all the concepts we saw earlier to build a small full-text search engine with sheraf.

Full-text search takes a query from a user, and tries to match documents containing the words in the query.
Generally we expect it to tolerate typos, and understand plural forms, conjugationsa and variants of the same
word (for instance *work* and *working* should be considered as very close). We also expect the result to be
orderd by pertinence. For instance, a document containing several times a search word should appear in a better
position than a document where it only appears once.

Those expectations leads to several treatments on the text we should index, and on the search queries. Here
are some steps that can appear:

1. **case**: This concept is simple. Basically it is about ignoring case in the indexation and queries.
   It can be applied for instance by only handling lowercase strings.
2. **accent folding**: This is about considering that the accented letters (for instance **e**, **é** and **è**) are
   equivalent, and ignoring accents in indexation and querying. This can be done for instance with :func:`unidecode.unidecode`.
3. **stemming** or **lemmatization**: Stemming is about deleting prefixes and suffixes, and reducing a word to
   another word that represents its sense. For instance *translations* and *translated* can both be reduced to
   *translat*. Both words refer to the same concept we call here *translat*, even if it is not a proper English word.
   Thus, a query containing *translations* can return results containing *translated*.
   With the proper tooling, this step is done automatically, and depends on the language. Indeed different languages have different
   prefixes and suffixes. Stemming can be done with librarys like `pystemmer <https://github.com/snowballstem/pystemmer>`_
   or `nltk <https://github.com/nltk/nltk>`_.

   lemmatization is a variant of stemming that only reduce words to existing words. For instance *translations* and
   *translated* could be reduced to *translate*. This is slower than stemming, but is more accurate. You can
   lemmatize with libraries like nltk.
4. **typo correction**: *errare humamun est*, this adage is still true whith query search. Typo correction is about
   allowing the users to make little mistakes in the information they index or query, and still match pertinent results.
   This is sometimes called *fuzzy searching*.

   - Some algorithms like the `Levenshtein distance <https://en.wikipedia.org/wiki/Levenshtein_distance>`_ or the
     `Damerau-Levenshtein <https://en.wikipedia.org/wiki/Damerau%E2%80%93Levenshtein_distance>`_ allow to estimate
     the similarity between two words. The promiximity of the variant letters, their numbers etc. are taken in account.
     Computing the Levenshtein distance between one query word and a set of reference words is tedious, as you have to
     compute the distance between your query word and each word in the set. Some datastructures like
     `BK Trees <https://en.wikipedia.org/wiki/BK-tree>`_ allow you to organize your reference set so you just need
     to compute the Levenshtein distance against a subset of words before you find the best match.

     The Levenshtein distance is implemented in libraries like `fuzzywuzzy <https://github.com/seatgeek/fuzzywuzzy>`_ or
     `python-levenshtein <https://github.com/ztane/python-Levenshtein/>`_. :mod:`difflib` also bring string similarity
     methods.
   - Other algorithms like Wolf Garbe's LinSpell or SymSpell take a different approach but seem to be faster than
     BK/Damerau-Levenshtein. Symspell especially trades query speed against memory usage and pre-computation speed.

   Another complementary approach is to check words against dictionnaries and then correct them. This for instance is what does
   `pyenchant <https://pyenchant.github.io/pyenchant/>`_, based on tools like `aspell <http://aspell.net/>`_. Note
   that pyenchant can allow you to define your own dictionnary.
5. **pertinence**: Pertinence is about knowing if a word takes an important place in a document. For instance
   a document where a searched word appears several time is more pertinent than a document where it appears only
   once. A document where a searched word appears in the title is more pertitent than a document where it appears
   in the footer. You can do this with some algorithms family like `BM25 <https://en.wikipedia.org/wiki/Okapi_BM25>`_.
   BM25 is implemented for instance in `rank_bm25 <https://github.com/dorianbrown/rank_bm25>`_.

Depending on the number of documents, the size of the document, the nature of your data (natural language, small sets
of terms you choosed etc.), you might want to use and tune this or that technique. There is no magical formula to
give perfect results. You can also define strategies where you use some of those techniques only when exact matches
does not return good enough results.
Some libraries like `Whoosh <https://whoosh.readthedocs.io/>`_ implement almost all the previous concepts,
and it also manages the storing of indexes.

Let us see what we can do with those concepts in sheraf. The idea is not to pretend we can replace tools like Whoosh,
but to experiment the flexibility sheraf offers.

Name completion
---------------

TBD.

Name search
-----------

Let us start with a simple problem, and consider we have a cowboy database, and we need to be able to search
in their names:

- We do not have to understand a whole natural languale like English, because proper nouns won't appear in a dictionnary.
  In that case it seems useless to deal with stemming or lemmatization.
- We can avoid using pertinence algorithms since the search documents (i.e. the name and location) are very small. We can
  consider our search queries will be indexed maximum once for each cowboy.
- We just want to find approximate matches, so case and accents won't matter.
- However we do want to allow users to mispell cowboy names.

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

Here we wrote two indexation and query functions that we use for the cowboy names indexation.
The query method lowers the string, removes the accents, and return all the words in the string.
The indexation method does computes all the subwords in almost the same steps except it returns
all the subwords for all the words in the string. Now let us see how it behaves:

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol De La Muerte")
    ...
    ...     assert [george] == Cowboy.search(name="George Abitbol De La Muerte")
    ...     assert [george] == Cowboy.search(name="george")
    ...     assert [george] == Cowboy.search(name="geo")
    ...     assert [george] == Cowboy.search(name="g")
    ...     assert [george] == Cowboy.search(name="GeOrGe")
    ...
    ...     assert [] == Cowboy.search(name="georgio")
    ...     assert [] == Cowboy.search(name="georgettetito")


Now we see that we can query the exact full name, just the first or second name, a substring of
the first or second name, any case variants. However there are two problems with this implementation:

- our indexation mechanism does not allow for typos (searching for *gerge* did not find anything)
- searching for one character returns the whole cowboy name. That seems a bit excessive so we could
  probably save some space.

Let us edit our indexation and query function so they tolerate typos. We can use a naive algorithm
inspired from SymSpell. Basically the idea is to index a name and variants of this name with typos,
and then search for a term with variants of this term with typos. Unlike the Levenshtein algorithm,
SymSpell only consider one operation to calculate distance between words, that is **deletion**. So
for each name, we will index it with missing letters, and when we will query a term, we will query
it with missing letters too. We can set a limit to how many deletions can occur before we consider
a word is too different from another. Here, let us consider 2.

.. code-block:: python

    >>> def subwords(string, max_deletions=2):
    ...     deletes = {string}
    ...     queue = {string}
    ...     for _ in range(max_deletions):
    ...         temp_queue = set()
    ...         for word in queue:
    ...             if len(word) > max(1, len(string) - max_deletions):
    ...                 for character in range(len(word)):
    ...                     word_minus_c = word[:character] + word[character + 1:]
    ...                     deletes.add(word_minus_c)
    ...                     temp_queue.add(word_minus_c)
    ...         queue = temp_queue
    ...     return deletes

We can take back our functions, and use deletions within a range of 2 instead of all
possible subwords:

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
    ...     george = Cowboy.create(name="George Abitbol De La Muerte")
    ...
    ...     assert [george] == Cowboy.search(name="George Abitbol De La Muerte")
    ...     assert [george] == Cowboy.search(name="george")
    ...     assert [george] == Cowboy.search(name="geo")
    ...     assert [george] == Cowboy.search(name="GeOrGe")
    ...     assert [george] == Cowboy.search(name="georgio")
    ...
    ...     assert [] == Cowboy.search(name="g")
    ...     assert [] == Cowboy.search(name="georgettetito")

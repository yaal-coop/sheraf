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
    ...         index_keys_func=cowboy_indexation,
    ...         search_keys_func=cowboy_query,
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
    ...         index_keys_func=cowboy_indexation,
    ...         search_keys_func=cowboy_query,
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
    ...         index_keys_func=cowboy_indexation,
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

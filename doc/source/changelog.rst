Roadmap and changelog
#####################

Versions follow `Semantic Versioning <https://semver.org/>`_ (<major>.<minor>.<patch>). Hopefully some day we will respect `Keep a Changelog <https://keepachangelog.com>`_ recommandations.

Roadmap
-------

- Refactor the migration and check tools;
- Deleted models check/migration;
- Deleted attributes check/migration;
- Fix TODO comments in the code;
- Add a check that tests if the blob configuration is OK.
- 100% coverage.

During version 4
================


Model attribute indexation:

À faire
-------

- tests de performances 2 : comparer order avec et sans indexation sur de gros volumes
- Dev/test : une fonction utilitaire pour vérifier ce que produit la values_function d'un attribut + documentation
- Question : Comment se comporte le système quand on passe d'unique à multiple & vice-versa ?
- Question : Comment nommer filter et filter_raw ?
  -> vu que filter est basé sur la fonction donnée a l'indexation, on pourrait etre explicite a ce sujet.
- Peut-être ? read_raw pour les données brutes, read pour les données dans un queryset
- Épique : Un exemple de recherche fulltext avec un algo comme bm25 https://github.com/dorianbrown/rank_bm25

En cours
--------

- Check : Vérifier l'état des index

  - Chaque index d'une table d'index doit pointer vers des modèles existants (càd dont l'id est présent dans la table de modèles) et dont les valeurs d'attributs correspondent à celle de l'index (càd: l'index de valeur 'george abitbol' d'un attribut 'nom' d'un modèle 'Cowboy' doit pointer vers un objet 'Cowboy' dont la valeur de l'attribut 'nom' est bien 'george abitbol' (après fonction de transformation))
  - Chaque valeur de chaque attribut indexé d'un modèle doit être présent dans sa table d'indexation (après fonction de transformation).
  - Reste: faire des tests pour les index MULTIPLE + objets supprimes en base mais encore presents dans l'index

À challenger
------------

Fait
----

- Migration : Effacer puis recréer la table d'indexation d'un modèle.
- Dev/test : dans les tables d'indexation, stocker les persistent plutôt que les ids (à faire quand les index seront stockés dans les persistent)
- cv perf_filter.py -- tests de performances 1 : comparer filter avec et sans indexation sur de gros volumes (commentaire: temps lineaire)
- Question : sheraf.UNIQUE ou unique=True ?
  -> Z: Y a-t-il d'autres options que sheraf.UNIQUE et sheraf.MULTIPLE? Si non, unique=True me parait plus direct.
  -> É: Yep.
- Dev/test : structure de données particulières pour les tables d'index de certains types d'attributs
  (les IntegerAttribute utiliseront probablement des IOBTrees ou des LOBTrees). Fournir des bons types par défaut, mais laisser à l'utilisateur la possibilité de les choisir.
  -> Z: dans le cas ou on donne des cles, on sera obliges de laisser l'utilisateur choisir, le type sera connu a l'interpretation seulement, sauf si on l'indique (*type hints*).
     Proposition : ajouter un argument optionnel "type=" dans la fonction index()?
  -> É: fait, dans un paramètre 'mapping' de AttributeIndex
- Question : Dans le cas des index multiples : quelle structure de donées choisir pour stocker la collection de modèles indexés ?
  -> É: On parle d'une collection de persistents, donc il s'agit forcément d'un \*OBTree. Je pense que LargeList fera l'affaire dans un premier temps.
- Dev/test : À la création d'un modèle :

  - Si la table d'indexation n'existe pas:

    - Si c'est le premier modèle de la base : créer la table, indexer le modèle ;
    - Sinon ne rien faire. Peut-être émettre un warning perso. Vérifier que sentry le remonte bien;
  - Si la table d'indexation existe: indexer le modèle ;
- Dev/test : À l'édition d'un attribut indexé d'un modèle: même chose que point précédent (Peut-être tester aussi l'édition d'un attribut indexé sur un modèle fraîchement créé);
- Dev/test : si l'état de la base n'est pas cohérent (modèles présents en base, index absents en base, index présents dans le code) alors la méthode filter doit être aussi lente que lorsque non indexé.


During later versions
=====================

- Attributes typing & Mypy.

sheraf 3 versions
----------------

.. include:: ../../CHANGELOG.md

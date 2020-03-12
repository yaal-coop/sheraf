A look on the database tree
===========================

Let us have a look on how the database tree is like in a case with indexed models,
external models attributes and indexed models attributes.

.. contents::
   :local:

First-level model
-----------------

.. code-block:: python

   >>> class Saloon(sheraf.Model):
   ...     table = "saloon"
   ...     location = sheraf.StringAttribute()
   ...
   >>> with sheraf.connection(commit=True):
   ...     saloon = Saloon.create(location="heaven")

Here we have a :class:`~sheraf.models.Model` *Saloon* with a table named *saloon*, and we
create one instance of *Saloon*. In the database, it means that the table *saloon* will be
created to host all the index tables for this model. The only index here is *id* (that is
implicit for all the first-level models), and an index table will be created for ids.

The database tree will look like this:

.. graphviz::
   :align: center

    digraph cowboy {
        node [
            shape="box"
        ];
        edge [
            arrowhead="none"
        ];

        "root" [label="root"];
        "table_saloon" [label="OOBTree"];
        "root" -> "table_saloon" [label=" saloon"];
        "saloon_index_id" [label="OOBTree"];
        "saloonmapping" [label="SmallDict
    id: '62a29766-3ccc'
    location: 'heaven'"];

        "table_saloon" -> "saloon_index_id" [label="id"];
        "saloon_index_id" -> "saloonmapping" [label="62a29766-3ccc"];
     }

Note that for the sake of readability, the :class:`~uuid.UUID` have been shortened in the graphs.

Additional indexes
------------------

Now let us add some cowboys in the saloon.

.. code-block:: python

   >>> class Cowboy(sheraf.Model):
   ...     table = "cowboy"
   ...     name = sheraf.StringAttribute().index(unique=True)
   ...     age = sheraf.IntegerAttribute()
   ...
   >>> with sheraf.connection(commit=True):
   ...     peter = Cowboy.create(name="peter", age=30)

Here we define a now *Cowboy* model with a table named *cowboy*. In addition
to the default *id* index, it has an index on *name*. The new *name* index will
be added in the *Cowboy* table near *id*.

.. graphviz::
   :align: center

    digraph cowboy {
        node [
            shape="box"
        ];
        edge [
            arrowhead="none"
        ];

        "root" [label="root"];
        "table_saloon" [label="OOBTree"];
        "table_cowboy" [label="OOBTree"];
        "root" -> "table_saloon" [label=" saloon"];
        "root" -> "table_cowboy" [label=" cowboy"];

        subgraph cowboy {
            "cowboy_index_id" [label="OOBTree"];
            "cowboy_index_name" [label="OOBTree"];

            "table_cowboy" -> "cowboy_index_id" [label=" id"];
            "table_cowboy" -> "cowboy_index_name" [label=" name"];

            subgraph peter {
                "persistent_peter" [label="SmallDict
    id: 238745982085
    name: 'peter'"];

                "cowboy_index_id" -> "persistent_peter" [label=" 146de06d-b700"];
                "cowboy_index_name" -> "persistent_peter" [label=" peter"];
            }
        }

        subgraph saloon {
            "saloon_index_id" [label="OOBTree"];
            "saloonmapping" [label="SmallDict
    id: '62a29766-3ccc'
    location: 'heaven'"];

            "table_saloon" -> "saloon_index_id" [label="id"];
            "saloon_index_id" -> "saloonmapping" [label="62a29766-3ccc"];
         }
     }

Multiple indexes
----------------

What if we want to remember the favorite guns of the cowboys.

.. code-block:: python

   >>> class Cowboy(sheraf.Model):
   ...     table = "cowboy"
   ...     name = sheraf.StringAttribute().index(unique=True)
   ...     age = sheraf.IntegerAttribute()
   ...     gun = sheraf.StringAttribute().index()
   ...
   >>> with sheraf.connection(commit=True):
   ...     peter = Cowboy.read(name="peter")
   ...     peter.gun = "remington"

We edited *Cowboy* to add a *gun* index. Indices are multiple by default,
so as we did not passed any argument to :func:`~sheraf.attributes.base.BaseAttribute.index`,
the *gun* index is multiple.

This means that each entry in the *gun* index will match a list of references
to *Cowboy* instances (instead of a single reference if the index has been unique). By default
a :class:`~sheraf.types.LargeList` are used.

.. graphviz::
   :align: center

    digraph cowboy {
        node [
            shape="box"
        ];
        edge [
            arrowhead="none"
        ];

        "root" [label="root"];
        "table_saloon" [label="OOBTree"];
        "table_cowboy" [label="OOBTree"];
        "root" -> "table_saloon" [label=" saloon"];
        "root" -> "table_cowboy" [label=" cowboy"];

        subgraph cowboy {
            "cowboy_index_id" [label="OOBTree"];
            "cowboy_index_name" [label="OOBTree"];
            "cowboy_index_gun" [label="OOBTree"];

            "cowboy_index_gun_list" [label="LargeList"];

            "table_cowboy" -> "cowboy_index_id" [label=" id"];
            "table_cowboy" -> "cowboy_index_name" [label=" name"];
            "table_cowboy" -> "cowboy_index_gun" [label=" gun"];

            "persistent_peter" [label="SmallDict
    id: 238745982085
    name: 'peter'
    gun: 'remington'"];

            "cowboy_index_id" -> "persistent_peter" [label=" 146de06d-b700"];
            "cowboy_index_name" -> "persistent_peter" [label=" peter"];
            "cowboy_index_gun" -> "cowboy_index_gun_list" [label=" remington"];
            "cowboy_index_gun_list" -> "persistent_peter" [label=" 0"];
        }

        subgraph saloon {
            "saloon_index_id" [label="OOBTree"];
            "saloonmapping" [label="SmallDict
    id: '62a29766-3ccc'
    location: 'heaven'"];

            "table_saloon" -> "saloon_index_id" [label="id"];
            "saloon_index_id" -> "saloonmapping" [label="62a29766-3ccc"];
         }
     }


External model attributes
-------------------------

We just forgot to link the cowboys and the saloons.

.. code-block:: python

   >>> class Cowboy(sheraf.Model):
   ...     table = "cowboy"
   ...     name = sheraf.StringAttribute().index(unique=True)
   ...     age = sheraf.IntegerAttribute()
   ...     gun = sheraf.StringAttribute().index()
   ...     saloon = sheraf.ModelAttribute(Saloon)
   ...
   >>> with sheraf.connection(commit=True):
   ...     peter = Cowboy.read(name="peter")
   ...     peter.saloon = saloon

We edited *Cowboy* to add an external reference to the *Saloon* model we
created before.
As external references are not real ZODB references, just the *Saloon* id is stored.

.. graphviz::
   :align: center

    digraph cowboy {
        node [
            shape="box"
        ];
        edge [
            arrowhead="none"
        ];

        "root" [label="root"];
        "table_saloon" [label="OOBTree"];
        "table_cowboy" [label="OOBTree"];
        "root" -> "table_saloon" [label=" saloon"];
        "root" -> "table_cowboy" [label=" cowboy"];

        subgraph cowboy {
            "cowboy_index_id" [label="OOBTree"];
            "cowboy_index_name" [label="OOBTree"];
            "cowboy_index_gun" [label="OOBTree"];

            "cowboy_index_gun_list" [label="LargeList"];

            "table_cowboy" -> "cowboy_index_id" [label=" id"];
            "table_cowboy" -> "cowboy_index_name" [label=" name"];
            "table_cowboy" -> "cowboy_index_gun" [label=" gun"];

            "persistent_peter" [label="SmallDict
    id: 238745982085
    name: 'peter'
    gun: 'remington'
    saloon: '62a29766-3ccc'"];

            "cowboy_index_id" -> "persistent_peter" [label=" 146de06d-b700"];
            "cowboy_index_name" -> "persistent_peter" [label=" peter"];
            "cowboy_index_gun" -> "cowboy_index_gun_list" [label=" remington"];
            "cowboy_index_gun_list" -> "persistent_peter" [label=" 0"];
        }

        subgraph saloon {
            "saloon_index_id" [label="OOBTree"];
            "saloonmapping" [label="SmallDict
    id: '62a29766-3ccc'
    location: 'heaven'"];

            "table_saloon" -> "saloon_index_id" [label="id"];
            "saloon_index_id" -> "saloonmapping" [label="62a29766-3ccc"];
         }
     }

Indexed attribute models
------------------------

Now we should consider some horses so cowboys can actually go in the saloon.

.. code-block:: python

   >>> class Horse(sheraf.AttributeModel):
   ...     name = sheraf.StringAttribute().index(primary=True)
   ...     breed = sheraf.StringAttribute()
   ...
   >>> class Cowboy(sheraf.Model):
   ...     table = "cowboy"
   ...     name = sheraf.StringAttribute().index()
   ...     age = sheraf.IntegerAttribute()
   ...     gun = sheraf.StringAttribute().index()
   ...     saloon = sheraf.ModelAttribute(Saloon)
   ...     horses = sheraf.IndexedModelAttribute(Horse)
   ...
   >>> with sheraf.connection(commit=True):
   ...     steven = Cowboy.create(name="steven", age=35)
   ...     jolly = steven.horses.create(name="jolly", breed="mustang")
   ...     polly = steven.horses.create(name="polly", breed="shetland")

Here we added a *Horse* attribute model, with its *name* as the primary index.
We modified *Cowboy* so it can host *Horse* instances. Then we created a new
cowboy called *steven* that own two horses.

The indexation mechanism works near the same way for first-level models or
attribute models. So the index table for *Horse* is an *OOBTree*. The *Horse*
only index is *name* (there is no *id* index as this is not a first-level model).
So there is another *OOBTree* for names in the *Horse* index table. Then,
the horses :class:`~sheraf.types.SmallDict` are indexed by their names.

.. graphviz::
   :align: center

    digraph cowboy {
        node [
            shape="box"
        ];
        edge [
            arrowhead="none"
        ];

        "root" [label="root"];
        "table_saloon" [label="OOBTree"];
        "table_cowboy" [label="OOBTree"];
        "root" -> "table_saloon" [label=" saloon"];
        "root" -> "table_cowboy" [label=" cowboy"];

        subgraph cowboy {
            "cowboy_index_id" [label="OOBTree"];
            "cowboy_index_name" [label="OOBTree"];
            "cowboy_index_gun" [label="OOBTree"];

            "cowboy_index_gun_list" [label="LargeList"];

            "table_cowboy" -> "cowboy_index_id" [label=" id"];
            "table_cowboy" -> "cowboy_index_name" [label=" name"];
            "table_cowboy" -> "cowboy_index_gun" [label=" gun"];

            subgraph peter {
                "persistent_peter" [label="SmallDict
    id: 238745982085
    name: 'peter'
    saloon: '62a29766-3ccc'"];

                "cowboy_index_id" -> "persistent_peter" [label=" 146de06d-b700"];
                "cowboy_index_name" -> "persistent_peter" [label=" peter"];
                "cowboy_index_gun" -> "cowboy_index_gun_list" [label=" remington"];
                "cowboy_index_gun_list" -> "persistent_peter" [label=" 0"];
            }

            subgraph steven {
                "persistent_steven" [label="SmallDict
    id: 2715507222553
    name: 'steven'"];
                "persistent_horses" [label="OOBTree"];
                "horse_name_index" [label="OOBTree"];
                "jollymapping" [label="SmallDict
    name: 'jolly'
    breed: 'mustang'"];
                "pollymapping" [label="SmallDict
    name: 'polly'
    breed: 'shetland'"];

                "cowboy_index_id" -> "persistent_steven" [label=" a9a6938f-4800"];
                "cowboy_index_name" -> "persistent_steven" [label=" steven"];

                "persistent_steven" -> "persistent_horses" [label=" horses"];
                "persistent_horses" -> "horse_name_index" [label=" name"];
                "horse_name_index" -> "jollymapping" [label=" jolly"];
                "horse_name_index" -> "pollymapping" [label=" polly"];
            }
        }

        subgraph saloon {
            "saloon_index_id" [label="OOBTree"];
            "saloonmapping" [label="SmallDict
    id: '62a29766-3ccc'
    location: 'heaven'"];

            "table_saloon" -> "saloon_index_id" [label="id"];
            "saloon_index_id" -> "saloonmapping" [label="62a29766-3ccc"];
         }
     }


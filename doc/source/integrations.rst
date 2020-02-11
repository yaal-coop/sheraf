Integrations
############

sheraf integrates well with some other libraries. Here are some examples.

WTForms
-------

WTForms :class:`~wtforms.form.Form` and sheraf :class:`~sheraf.models.base.BaseModel` both interact well with python dicts. And because they can both behave like dicts, they interact well with each other. On one hand :func:`wtforms.form.BaseForm.process` or the :class:`~wtforms.form.Form` constructor can be initialized with a dict matching its structure, and a :class:`~sheraf.models.base.BaseModel` can easilly be casted as a dict. On the other hand, the model :func:`sheraf.models.base.BaseModel.assign` method can update the model values from a dictionnary matching the form structure, and :class:`~wtforms.form.Form` can also be casted as a dict. Let us see how to make them work together.

Writing models and forms
~~~~~~~~~~~~~~~~~~~~~~~~

Let us define some simple, but nested models:

.. doctest::

    >>> import sheraf
    >>> class Horse(sheraf.InlineModel):
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboys"
    ...
    ...     name = sheraf.SimpleAttribute()
    ...     age = sheraf.IntegerAttribute()
    ...     horses = sheraf.SmallListAttribute(sheraf.InlineModelAttribute(Horse))

Now we build forms matching the same structure as the models. Form fields must have the same names as the model attributes:

.. doctest::

    >>> import wtforms
    >>> class HorseForm(wtforms.Form):
    ...     name = wtforms.StringField(label="The horse name")
    ...
    >>> class CowboyForm(wtforms.Form):
    ...     name = wtforms.StringField(label="The cowboy name")
    ...     age = wtforms.IntegerField(label="The cowboy age")
    ...     horses = wtforms.FieldList(
    ...         wtforms.FormField(HorseForm),
    ...     )

The last thing needed is some glue between WTForms and sheraf. Let us apply that glue in the function handling our http request:

.. doctest::

    >>> @sheraf.commit
    ... def cowboy_form(request, cowboy_id):
    ...     cowboy = Cowboy.read(cowboy_id)
    ...
    ...     form = CowboyForm(request.form or None, cowboy)
    ...
    ...     if request.method == 'POST':
    ...         if form.validate():
    ...             cowboy.assign(**form.data)
    ...         else:
    ...             print(form.errors)
    ...
    ...     # Usually this is where we return a werkzeug answer,
    ...     # but for the test, let's return the form and the model
    ...     return cowboy, form

1. First we get the *Cowboy* object from the database (note: raises a :class:`~sheraf.exceptions.ObjectNotFoundException` if the *cowboy_id* is not valid).
2. Then we initialize the :class:`~wtforms.form.Form` with both the request form and the *Cowboy*. If no form was sent in the request, the :class:`~wtforms.form.Form` will be initialized with the model values. Else it will be initialize with the data sent in the form.
3. If there is a request form and WTForms validates it, then we update the *Cowboy* with the form data, with :func:`~sheraf.models.base.BaseModel.assign`. Note that you may want to use :func:`~sheraf.models.base.BaseModel.update` instead of :func:`~sheraf.models.base.BaseModel.assign` if you do not want to delete data from your form.
4. Finally, we should return some HTTP answer. We do not focus on that here, so for the sake of the test, we return our form and object.

.. note :: We use :func:`sheraf.models.base.BaseModel.assign` instead of :func:`wtforms.form.Form.populate_obj` because :func:`~wtforms.form.Form.populate_obj` has no way to know how to instantiate a new *Horse* if there are more horses in the form than in the base. :func:`~sheraf.models.base.BaseModel.assign` will be able to add or delete a horse to/from the horses list depending on the data it gets from the form.

.. warning :: Because of a `bug in WTForms 2.2 <https://github.com/wtforms/wtforms/issues/414>`_ there can be some unexpected behaviors with :class:`~wtforms.fields.BooleanField` if ``request.form`` is empty but not ``None``. This is why it is preferable to use ``request.form or None``.

Usage
~~~~~

.. doctest ::

    >>> from werkzeug.test import EnvironBuilder
    >>> from werkzeug.wrappers import Request

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol", age=50, horses=[
    ...         {"name": "Jolly Jumper"},
    ...     ])

Now that we have a cowboy, let us see how the form is initialized:

.. doctest ::

    >>> # This is an utility to simulate a real werkzeug request
    >>> request = Request(EnvironBuilder(method='GET').get_environ())

    >>> with sheraf.connection():
    ...     cowboy, form = cowboy_form(request, george.id)
    ...     cowboy.name
    'George Abitbol'

    >>> form.name.data
    'George Abitbol'

    >>> form.horses.data
    [{'name': 'Jolly Jumper'}]

We can check that the form is initialized with the cowboy data. George Abitbol is 51 years old,
and he has another horse. Let us edit the form and send it back:

.. doctest ::

    >>> request = Request(EnvironBuilder(method='POST', data={
    ...     'name': 'George Abitbol',
    ...     'age': 'fifty-one',
    ...     'horses-0-name': 'Jolly Jumper',
    ...     'horses-1-name': 'Polly Pumper',
    ... }).get_environ())

    >>> with sheraf.connection():
    ...     cowboy, form = cowboy_form(request, george.id)
    {'age': ['Not a valid integer value']}

    >>> with sheraf.connection():
    ...     cowboy.age
    50

    >>> with sheraf.connection():
    ...     len(cowboy.horses)
    1

We made a mistake here by setting the age as a text value instead of an integer value. As WTForms did not validate the form,
the model was not edited. Neither the cowboy age nor its horses have changed. Let us try again with some better values:

.. doctest ::

    >>> request = Request(EnvironBuilder(method='POST', data={
    ...     'name': 'George Abitbol',
    ...     'age': 51,
    ...     'horses-0-name': 'Jolly Jumper',
    ...     'horses-1-name': 'Polly Pumper',
    ... }).get_environ())
    ...

    >>> with sheraf.connection():
    ...     cowboy, form = cowboy_form(request, george.id)
    ...     cowboy.age
    51

Now we realize that *Polly Pumper* is an old horse, and has a stupid name anyway. So we do not include it in the form, and
it will be deleted.

.. doctest ::

    >>> request = Request(EnvironBuilder(method='POST', data={
    ...     'name': 'George Abitbol',
    ...     'age': 51,
    ...     'horses-0-name': 'Jolly Jumper',
    ... }).get_environ())

    >>> with sheraf.connection():
    ...     cowboy, form = cowboy_form(request, george.id)
    ...     len(cowboy.horses)
    1

.. _views:

Backoffice Views
================

A Backoffice View is a combination of:

* A Django template
* A subclass of :class:`~advanced_reports.backoffice.base.BackOfficeView` which renders the template
* Optionally a piece of extra JavaScript used by the template

They provide a basis for extremely pluggable components that can be placed anywhere on the Backoffice.


The Python side
---------------

A :class:`~advanced_reports.backoffice.base.BackOfficeView` subclass can be registered to a
:class:`~advanced_reports.backoffice.base.BackOfficeBase` subclass instance using the
:meth:`~advanced_reports.backoffice.base.ViewMixin.register_view` method.

One of the most important methods of the ``BackOfficeView`` base class is::

    def get(self, request):
        return render(request, self.template, self.get_context(request))


The default implementation just returns a :class:`~django.http.HttpResponse` with the rendered ``self.template``.

To add some extra context, implement ``get_extra_context``::

    def get_extra_context(self, request):
        return {}

A very simple view would then look like this::

    from advanced_reports.backoffice.base import BackOfficeView

    class SimpleView(BackOfficeView):
        template = 'my_simple_view.html'

        def get_extra_context(self, request):
            return {'simple': True}


Defining a ``slug`` is not required. It will take by default the lowercase version of the class name minus the
``View``-suffix. In this case, the slug would be ``"simple"``.


The Django Template side
------------------------

Nothing special here, you can write any HTML you like including Django template tags. You have access to the context
like you would expect.

.. _view_js:

The JavaScript side
-------------------


.. seealso::

    See the :ref:`angular` section


.. warning::

    Because we are mixing AngularJS templates with Django templates, it is discouraged to use the ``{{ }}``
    interpolations from AngularJS. You can easily work around them by using
    `ng-bind <https://docs.angularjs.org/api/ng/directive/ngBind>`_.
    If you really **do** require the interpolations, you can always use the ``{% verbatim %}`` and ``{% endverbatim %}``
    template tags. By doing this, you can clearly see which parts of your template is rendered by the browser and the server.

Now things become interesting. As you already know, the Backoffice makes use of `AngularJS <http://angularjs.org>`_ for
its web frontend. There is a ``view``-directive exposed that you can use. This directive is used like this::

    <div view="simple" params="{simpleness: 5}"></div>


What will happen is that the underlying ``get()``-method gets called and the Django template will be rendered inside
this ``<div>``. You have access to the ``params`` using ``request.view_params``, which is a ``dict``-like object you
can query.

Not only that, your template itself has access to a special ``view`` object available in the ``$scope``.

This object exposes the following API:

* ``view.fetch()``: retrieve the template again (calls the ``get()`` again)
* ``view.action('method_name', {param1: 'lol'})``: calls the method ``method_name`` on the ``BackOfficeView`` subclass
  and refreshes the view using ``view.fetch()``.
* ``view.call('method_name', {param1: 'lol'})``: the same as ``view.action()`` but without the refreshing.
  Returns a promise object.


The ``method_name``-method can look like this in Python::

    class SimpleView(BackOfficeView):
        ...

        def method_name(self, request):
            param1 = request.action_params.get('param1')
            messages.success(request, 'successful happyness!')
            return {'happy': True, 'data': 3}


It is *that* easy to communicate from your JavaScript frontend to your Python code.
Notice that you can use the Django messages framework. They show up in the Backoffice website!
Make sure that you only use simple objects in the communication, as they will be converted to JSON behind the scenes.


Full example
------------

This example illustrates how this simple view is constructed:

.. image:: /backoffice/example_view1.png

.. rubric:: simple.html

.. literalinclude:: /backoffice/example_view1.html
   :language: html

.. rubric:: views.py

.. literalinclude:: /backoffice/example_view1.py

.. rubric:: definitions.py

.. code-block:: python

    ...

    backoffice_instance.register_view(SimpleView)

    ...

.. rubric:: anywhere.html

.. code-block:: html

    <div view="simple" extra="true"></div>

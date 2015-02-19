.. _models:

Backoffice Models
=================


A Backoffice Model is a combination of:

* A Django model
* A subclass of :class:`~advanced_reports.backoffice.base.BackOfficeModel`
* Templates for the tabs defined in the :class:`~advanced_reports.backoffice.base.BackOfficeModel` subclass

When you attach a Django model to a BackOfficeModel, and register it to a
:class:`~advanced_reports.backoffice.base.BackOfficeBase` subclass, it will become a part of the Backoffice website.


Creating a BackOfficeModel
--------------------------

Let's have a look at a fairly minimal example which exposes the Django :class:`~django.contrib.auth.models.User` model.

.. rubric:: definitions.py

.. code-block:: python

    class UserModel(BackOfficeModel):
        model = User

        tabs = (BackOfficeTab('details', u'Details', 'user-details.html'),)

        def get_title(self, instance):
            return u'%s (%s)' % (instance.username, instance.get_full_name())

        def search_index(self, instance):
            return u' '.join((instance.username, instance.get_full_name(), instance.email))

    ...

    backoffice_instance.register_model(UserModel)

    ...

As you can see, we just say that we want to use the :class:`~django.contrib.auth.models.User` model, and that we want
to show only one tab for it, called "Details", rendered by a template "user-details.html":

.. code-block:: html

    <div view="user" params="{pk: model.id}"></div>

As you can see, this is a simple invocation of the "user" view. This is what will be rendered when the end users
selects the "Details" tab.

.. note::

    If you don't know what is meant by a "view" here, refer to the :ref:`views` section.

.. _model_object:

The ``model`` object
--------------------

What stands out in this view invocation is the ``{pk: model.id}`` parameter. In your
:class:`~advanced_reports.backoffice.base.BackOfficeTab` template, you have access to a ``model`` object in the current
`AngularJS <http://angularjs.org>`_ ``$scope``. This object represents an instance of your model. In our example, this
represents a single user. Thanks to this ``model`` object, the view knows which user to display.

In this case, this is what the ``model`` object contains::

    {
      "title": "jef (Jef Geskens)",
      "tabs": {
        "details": {
          "shadow": null,
          "slug": "details",
          "template": "...",
          "title": "Details"
        }
      },
      "route": {
        "model": "user",
        "id": 1
      },
      "id": 1,
      "meta": {
        "tabs": [
          {
            "shadow": null,
            "slug": "details",
            "title": "Details"
          }
        ],
        "show_in_parent": false,
        "collapsed": true,
        "verbose_name_plural": "users",
        "has_header": true,
        "verbose_name": "user",
        "slug": "user",
        "is_meta": true
      },
      "parents": [],
      "is_object": true,
      "model": "user",
      "children": [],
      "header_template": "..."
    }


This looks like a lot of information, but apart from the basic meta information about your model, we add extra
information related to parents, children, relationships, tabs, headers and routes. Most of this extra stuff will
probably not directly be useful for you, but it helps the Backoffice website render the tabs, menu items,
parent links, child links and headers.

.. note::

    Using this information, you could write your own frontend with your technology of choice to implement the same
    Backoffice functionality. Or, you could extend or replace existing functionality.


Let's go over the most useful parts:

* ``"title"``: This comes directly from your :meth:`~advanced_reports.backoffice.base.BackOfficeModel.get_title`
  implementation.
* ``"model"``: This is the model :attr:`~advanced_reports.backoffice.base.BackOfficeModel.slug`.
* ``"id"``: This is the primary key value of your model instance.
* ``"route"``: This object can be directly passed to the ``$scope.get_url()`` function in the AngularJS environment.
  It looks redundant but it is guaranteed to only contain route-related components.

This list can be extended using the :meth:`~advanced_reports.backoffice.base.BackOfficeModel.serialize` method.

.. seealso:: The :ref:`boreverser`


.. _angular:

Backoffice and AngularJS
========================


.. note::

    The Backoffice website framework makes use of `AngularJS <http://angularjs.org>`_ for its web frontend.
    However, this does not mean that you have to learn all the dirty details. You can choose yourself how much
    of AngularJS you actually want to use.

    It is advised that you have a quick look a the `homepage <http://angularjs.org>`_ to grasp the examples
    illustrated there, so you have an idea what for example ``ng-show`` means.


BackOfficeApp module
--------------------

Inside ``backoffice.js``, found in the ``static`` folder, the ``angular.module('BackOfficeApp')`` can be found. Below is a list of everything included with this module.

boApi service
-------------

The ``boApi`` service exposes some function which make it easy to communicate to the :ref:`backoffice_api`.

* ``configure(url)``: configure the boApi service instance with the given ``url``.
* ``get(method, params)``: perform an AJAX GET request to the configured url plus the ``method``. The ``params`` will be converted to a querystring. Hence, nesting of objects is not supported here, only simple parameters. Returns a ``$q.promise`` object, which resolves to the response data.
* ``post(method, data, url_suffix='')``: perform an AJAX POST request to the configured url plus the ``method`` and ``url_suffix``. The ``data`` will be converted to JSON and be put in the request body. Hence, this is much more flexible than the ``get()`` call. Returns a ``$q.promise`` object, which resolves to the response data.
* ``post_form(method, data)``: The same as ``post()`` except that the ``data`` is encoded using the ``application/x-www-form-urlencoded`` scheme instead of put as JSON in the request body. Returns a ``$q.promise`` object, which resolves to the response data.
* ``link(method, params)``: Returns a web link based on the configured url plus the ``method``. The ``params`` will be encoded as a querystring. This is useful for some API endpoints returning for example normal web pages or downloadable content.

.. _main_controller:

MainController controller
-------------------------

The main controller governing the Backoffice website. Some useful functions exposed to the ``$scope``:

* ``isLoading()``: Returns a boolean whether the ``boApi`` service is currently performing web requests. Can be useful to temporarily disable some submit buttons, to prevent accidental double submissions:

  .. code-block:: html

      <input type="submit" ng-disabled="isLoading()">

* ``fetchModel(force)``: Refetches the ``model`` object, causing practically the whole page to refresh. See the :ref:`model_object` section for more details on the contents of the ``model`` object.
* ``action(method, params)``: Calls the method ``method`` on the ``BackOfficeModel`` subclass and refreshes the tab using ``fetchModel(true)``. See also :ref:`view_js` from the :ref:`views` section.
* ``call(method, params)``: The same as ``action()`` but without the refreshing.
  Returns a ``$q.promise`` object.
* ``goto(route)``: Returns a function which goes to the given route. Handy to attach to a ``$q.promise`` from the ``call()`` function:

  .. code-block:: html

      <form ng-submit="call('edit', {data: form.data}).then(goto(model.parents[0].route))">
          ...
      </form>

* ``get_url(route, extra_routing_info={})``: Returns a web link using the given ``route``. It is possible to inject some extra routing information, for example if you have a route object to a model, but you want to navigate directly to a specific tab. Then you would call it like this: ``get_url(model.route, {tab: 'details'})``.

.. _boreverser:

boReverser service
------------------

The ``boReverser`` service takes a route object and creates a web link from it. It does this in a generic way.


* ``configure(hierarchy, prefix='#/')``: Configures this ``boReverser`` instance with the given ``hierarchy``, which is a list of named path components.
  The :ref:`main_controller`, which depends on ``boReverser``, uses this configuration:

  .. code-block:: js

      boReverser.configure(['model', 'id', 'tab', 'detail']);

* ``reverse(route)``: Returns a web link based on the given ``route`` object, which is just a simple key/value pair. Keys which are one of the configured ``hierarchy`` list, will render as a path delimited by slashes (``/``). Other keys are rendered as a querystring behind the path. Also, if there are ``hierarchy`` keys missing in the ``route`` object, the rendered result depends on the current browser location and how far to the right that the missing key is on the ``hierarchy``. Some examples based on the configuration above make this hopefully a bit clearer:

  .. code-block:: js

      // Current path is: '#/'
      boReverser.reverse({model: 'user'})
      // Returns: '#/user/'

      // Current path is: '#/'
      boReverser.reverse({model: 'user', id: 5})
      // Returns: '#/user/5/'

      // Current path is: '#/user/5/'
      boReverser.reverse({tab: 'details'})
      // Returns: '#/user/5/details/'

      // Current path is: '#/user/5/details/'
      boReverser.reverse({model: 'comment', id: 55})
      // Returns: '#/comment/55/'

      // Current path is: '#/user/5/'
      boReverser.reverse({report: 'myreport'})
      // Returns: '#/user/5/?report=myreport'

  As you can see, this small utility is quite powerful and covers most use cases for URL generation inside your application.

compile directive
-----------------

.. warning::

    Only use this during the development phase! This can be very dangerous on production and will easily allow XSS attacks!


Use this directive like this:

.. code-block:: html

    <textarea ng-model="code" cols="80" rows="25"></textarea>
    <div compile="code"></div>

Then you will have a ``<textarea>`` where you can try out some functionality, and the result will be displayed
immediately in the ``<div>`` below.

view directive
--------------

.. seealso:: See also the :ref:`views` section.

.. code-block:: html

    <div view="myview" params="{a: 5, b: 3}" c="mystring" eval-d="5+3" instance="myview1"></div>

The ``view`` directive renders a Backoffice View defined by a :class:`~advanced_reports.backoffice.base.BackOfficeView` subclass.

Attributes:

* ``view``: The :attr:`~advanced_reports.backoffice.base.BackOfficeView.slug` of the :class:`~advanced_reports.backoffice.base.BackOfficeView` subclass.
* ``params``: An object with key/value pairs of parameters.
* ``*``: An attribute that is passed as string (not evaluated). This will be added to the parameters.
* ``eval-*``: An attribute that is passed as a calculated value. This will be added to the parameters.
* ``instance``: (Optional) The name under which to expose the ``view`` object to the current ``$scope``. By default, this is the ``slug``. This is useful if you have multiple instances of views with the same ``slug`` and want to talk to one of them from the outside.

Functions and attributes exposed to the ``$scope`` of the view :attr:`~advanced_reports.backoffice.base.BackOfficeView.template`:

* ``view.params``: An object containing the parameters of the view.
* ``view.fetch()``: Refetches the initial view template (calls :meth:`~advanced_reports.backoffice.base.BackOfficeView.get`)

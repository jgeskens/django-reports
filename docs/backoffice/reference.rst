Backoffice Reference
====================

:py:class:`~advanced_reports.backoffice.base.BackOfficeBase` is the base class and entry point for the backoffice
website. It defines the base urls and views for logging in, and the core REST-like API implementation which serves
as a basis for extensions.

BackOfficeBase is extended by a few mixins:

* :py:class:`~advanced_reports.backoffice.base.ModelMixin`
* :py:class:`~advanced_reports.backoffice.base.SearchMixin`
* :py:class:`~advanced_reports.backoffice.base.ViewMixin`



.. image:: /backoffice/BackOfficeBase.png


.. automodule:: advanced_reports.backoffice.base
   :members:
   :undoc-members:

.. :changelog:

Changelog
---------

0.9.2 (2015-02-20)
++++++++++++++++++

* First release on PyPI.

0.9.3 (2015-02-27)
++++++++++++++++++

* Add api for reindexing the search index
* Small bugfixes related to sorting querysets in reports
* Extra unit tests for report sorting
* Remove redundant AutoSlug for BackOfficeTab

0.9.4 (2015-02-27)
++++++++++++++++++

* Fix issue where the translation system could be triggered too soon

0.9.5 (2015-03-03)
++++++++++++++++++

* Add possibility to add report-wide actions using ``is_report_action=True``.
* Add full CRUD example to examples page on demo website
* Small bugfix concerning the confirmation dialog

0.9.6 (2015-03-04)
++++++++++++++++++

* Escape AdvancedReport field values by default for security
* Add link_to HTML decorator possibility by providing the BackOfficeReportMixin
* Small cleanups and fix MANIFEST.in
* Fix setup.py and add changelog to docs
* Converted README to reST format

0.9.7 (2015-03-05)
++++++++++++++++++

* `2691ba3 <https://github.com/vikingco/django-advanced-reports/commit/2691ba3>`_ Fix report form error styling issue <Jef Geskens>
* `31ee2e5 <https://github.com/vikingco/django-advanced-reports/commit/31ee2e5>`_ Add example of ``link_to`` HTML decorator <Jef Geskens>
* `086ec98 <https://github.com/vikingco/django-advanced-reports/commit/086ec98>`_ Fix enriched queryset ordering issue <Jakub Paczkowski>
* `3a47616 <https://github.com/vikingco/django-advanced-reports/commit/3a47616>`_ Add tests for the enriched queryset ordering issue fix <Jakub Paczkowski>
* `521a257 <https://github.com/vikingco/django-advanced-reports/commit/521a257>`_ Add default ordering to the enriched queryset <Jakub Paczkowski>

0.9.8 (2015-03-10)
++++++++++++++++++

* `7e4adf4 <https://github.com/vikingco/django-advanced-reports/commit/7e4adf4>`_ Expose fetch_report so it can be called from outside <Jef Geskens>
* `ca38578 <https://github.com/vikingco/django-advanced-reports/commit/ca38578>`_ Fix styling issue for new compact view <Jef Geskens>
* `5406d7b <https://github.com/vikingco/django-advanced-reports/commit/5406d7b>`_ Extra examples for new compact property <Jef Geskens>
* `8118733 <https://github.com/vikingco/django-advanced-reports/commit/8118733>`_ Introduce compact mode and inline action buttons <Jef Geskens>

0.9.9 (2015-09-07)
++++++++++++++++++

* `ced26b2 <https://github.com/vikingco/django-advanced-reports/commit/ced26b2>`_ deduplicate call <Daniel Borzęcki>
* `61f032d <https://github.com/vikingco/django-advanced-reports/commit/61f032d>`_ ensure request is present when executing multiple actions <Daniel Borzęcki>
* `961c1d0 <https://github.com/vikingco/django-advanced-reports/commit/961c1d0>`_ enable row limit choice in reports' pages <Alexandros Ntavelos>
* `a92567e <https://github.com/vikingco/django-advanced-reports/commit/a92567e>`_ re-arrange if/else conditions <Alexandros Ntavelos>
* `d51a6b7 <https://github.com/vikingco/django-advanced-reports/commit/d51a6b7>`_ fix for tests <Jakub Paczkowski>
* `7ed1664 <https://github.com/vikingco/django-advanced-reports/commit/7ed1664>`_ add comment <Jakub Paczkowski>
* `2890472 <https://github.com/vikingco/django-advanced-reports/commit/2890472>`_ fix generation of large csv's <Jakub Paczkowski>
* `8685a81 <https://github.com/vikingco/django-advanced-reports/commit/8685a81>`_ optimize generation of csv <Jakub Paczkowski>


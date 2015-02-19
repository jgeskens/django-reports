Advanced Reports
================

[![image](https://travis-ci.org/vikingco/django-advanced-reports.svg?branch=master)](https://travis-ci.org/vikingco/django-advanced-reports) 
[![Circle CI](https://circleci.com/gh/vikingco/django-advanced-reports/tree/master.svg?style=svg)](https://circleci.com/gh/vikingco/django-advanced-reports/tree/master)
[![Coverage Status](https://coveralls.io/repos/vikingco/django-advanced-reports/badge.svg?branch=master)](https://coveralls.io/r/vikingco/django-advanced-reports?branch=master) 
[![Read The Docs](https://readthedocs.org/projects/django-advanced-reports/badge/?version=latest)](http://django-advanced-reports.readthedocs.org/en/latest/)

[View demo website](http://backoffice.oemfoeland.com)

![image](https://cloud.githubusercontent.com/assets/142114/3298713/8d550794-f605-11e3-845c-8953fc9ac00b.png)

Introduction
------------

Advanced Reports is a Django library which simplifies creating dynamic reports focusing on business processes. Custom actions can be defined on individual items and/or sets of items. Features include:

* Display of information in a table layout with columns
* Sorting
* Searching
* Filtering
* Editing individual items by using standard Django (Model-)Forms.
* Bulk actions

In addition to these features, Advanced Reports also contains a Backoffice component, which allows you to combine multiple reports and custom pages with AngularJS, which can in turn be combined to form complete administration interfaces. Features include:

* Integrate regular Django Models with the Backoffice interface by overriding a simple Python class and by providing Django/AngularJS templates. 
* Easily define how models can be searched by a full-text-search implementation which supports MySQL Full Text Search and Postgres Full Text Search. There is also a fallback using __icontains for simplifying testing with SQLite.
* A very simple and flexible way to add widgets that communicate with the server-side backend.

More information and examples are coming soon.


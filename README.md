Advanced Reports
================

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

About this branch
-----------------

This branch is an effort to clean up Advanced Reports and to open it up to the open source community. This way, it will be easier to enjoy the benefits of Advanced Reports in your own project, but also to allow you to contribute patches and pull requests. We took a lot of care into designing Advanced Reports, and want to share this to the world.

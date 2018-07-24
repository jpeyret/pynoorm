===============================
PyNoORM
===============================

.. image:: https://img.shields.io/pypi/v/pynoorm.svg
        :target: https://pypi.python.org/pypi/pynoorm


.. image:: https://img.shields.io/travis/jpeyret/pynoorm.svg
        :target: https://travis-ci.org/jpeyret/pynoorm

.. image:: https://readthedocs.org/projects/pynoorm/badge/?version=latest
        :target: https://readthedocs.org/projects/pynoorm/?badge=latest
        :alt: Documentation Status


Use Python with or without an ORM.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyNoORM consists of several very loosely-coupled classes that facilitate the use of Python in a web or SQL
context without having to rely on an ORM.  Working with an ORM is entirely possible, in fact, it's used with
the Django ORM and SQLAlchemy in an application that interfaces with Oracle, Microsoft SQL Server and PostgreSQL all at the same time.

Focus is on:

 - simplicity for the user
 - support for databases that are not under "controlled" by the Python application or may be read-only for it.
 - performance

+------------------------+-----------------------------------------------------------------------+
| Class                  | Role                                                                  |
+========================+=======================================================================+
| Binder                 | abstract SQL query binding                                            |
+------------------------+-----------------------------------------------------------------------+
| Linker                 | join objects together                                                 |
+------------------------+-----------------------------------------------------------------------+
| TemplateGenerator      | generate Django Templates dynamically from query results, loosely     |
| *(to be added)*        | inspired by Django Tables 2                                           |
+------------------------+-----------------------------------------------------------------------+


The Binder class
================

A Binder support easier raw SQL by abstracting differences in the underlying database's bind variable syntax and also substituting bind variables from a list of arguments, using dict, then attribute lookup.

Using native database binds also helps to protect you against SQL injection attacks.

supported:  PostgreSQL, sqlite3, Oracle, MySQL, SQL Server

Basic Use
---------

Simple **sqlite3** example::

    from pynoorm.binder import Binder
    binder = Binder.factory("qmark")

    query, parameters = binder("select * from orders where custid = %(custid)s", dict(custid="ACME"), binder)

``query`` and ``parameters`` are now in the sqlite3/qmark format::

	>>> print(query)
	select * from orders where custid = ?
	>>> print(parameters)
	('ACME',)

Oracle, with multiple parameters ::

    import cx_Oracle
    binder_ora = Binder.factory(cx_Oracle.paramstyle)

    #just for test... assign a custid for attribute lookup
    binder_ora.custid = "AMAZON"

    tqry = "select * from orders where custid = %(custid)s and has_shipped = %(shipped)s"
    query, parameters = binder_ora(tqry, binder_ora, dict(custid="ACME", shipped=1))

    >>> print(query)
    select * from orders where custid = :custid and has_shipped = :shipped
    >>> print(parameters)
    {'shipped': 1, 'custid': 'AMAZON'}

SQL IN list criteria:

This allows binding of Python lists as standard SQL ``in ('foo','bar')`` expressions, but as a prepared statement.

It relies on using `'l'`, rather than `'s'` as the format qualifier.  Notice the `%(custid)l` below ::

    from pynoorm.binder import Binder
    binder = Binder.factory("qmark")

    query, parameters = binder(
        "select * from orders where custid in (%(custid)l)"
        , dict(custid=["ACME","FOO","BAR"])
        )


Contents of `query` and `parameters`::
    
    select * from orders where custid in (?, ?, ?)
    ('ACME', 'FOO', 'BAR')
    

And now with an empty list::

    query, parameters = binder(
        """select * 
        from orders 
        where custid in (%(custid)l) 
        and status=%(status)s"""
        , dict(custid=[], status="any")
        )

Contents of `query` and `parameters`::


    select * from orders where custid in (NULL) and status=?
    ('any',)



Features
--------

* adjust query to support database parameter style
* find and prepare bind parameters from `*args`.



The Linker class
================

A Linker allows you to join objects or dictionaries without the need for an ORM.  You can think of it as performing `parent-child` linking, but it uses `left-right` instead as a more neutral terminology instead.

Basic use 
---------

Sample data, in dictionaries: ::

    customers = [
        dict(id=1, xref=1),
        dict(id=2, xref=2),
    ]

    orders = [
        dict(custid=1, xref=1, orderid=11),
        dict(custid=1, xref=1, orderid=12),
        dict(custid=2, xref=2, orderid=21),
        dict(custid=2, xref=2, orderid=22),
    ]

Create a linker, then a lookup dictionary for the left side.  Finally, link the left and right side. ::

    linker = Linker(key_left="id")
    lookup = linker.dict_from_list(customers)
    linker.link(lookup, orders, attrname_on_left="orders", key_right="custid")


The customers now have an `orders` list:  ::

    [ { 'id': 1,
        'orders': [ { 'custid': 1, 'orderid': 11, 'xref': 1},
                    { 'custid': 1, 'orderid': 12, 'xref': 1}],
        'xref': 1},
      { 'id': 2,
        'orders': [ { 'custid': 2, 'orderid': 21, 'xref': 2},
                    { 'custid': 2, 'orderid': 22, 'xref': 2}],
        'xref': 2}]

Features
--------
    
    * supports objects or dictionaries
    * takes basic Python objects so can join across different databases, allowing for example tagging of objects in a read-only database
    * allows compound field keys and aliasing
    * orphans, on the left or the right, can be initialized with empty attribute values.


Note on Python 3.7 support:
---------------------------

3.7 tests run to success locally, but travis-ci does not support Python 3.7 yet.  So expect `builds` to show
"failing" 3.7, pending resolution of Travisissue485_.

.. _Travisissue485: https://github.com/jopohl/urh/pull/485


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

* Free software: MIT license
* Documentation: https://pynoorm.readthedocs.org.

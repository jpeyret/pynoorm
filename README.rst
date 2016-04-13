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


Easier raw SQL, with or without an ORM.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Binder class
----------------

A Binder abstracts differences in the underlying database's bind variable syntax and also grabs bind variables
from a list of arguments, using dict, then attribute lookup.

Using native database binds also helps to protect you against SQL injection attacks.

supported:  Postgresql, sqlite3, Oracle, MySQL

Simple **sqlite3** example::

    from pynoorm.binder import Binder
    binder = Binder.factory("qmark")

    #just for test... assign a custid to binder for attribute lookup
    binder.custid = "AMAZON"

    query, parameters = binder("select * from orders where custid = %(custid)s", dict(custid="ACME"), binder)

``query`` and ``parameters`` are now in the sqlite3/qmark format::

	>>> print(query)
	select * from orders where custid = ?
	>>> print(parameters)
	('ACME',)

Oracle, with mutiple parameters?::

    import cx_Oracle
    binder_ora = Binder.factory(cx_Oracle.paramstyle)

    tqry = "select * from orders where custid = %(custid)s and has_shipped = %(shipped)s"
    query, parameters = binder_ora(tqry, dict(custid="ACME", shipped=1), binder)

    >>> print(query)
    select * from orders where custid = :custid and has_shipped = :shipped
    >>> print(parameters)
    {'shipped': 1, 'custid': 'ACME'}


* Free software: MIT license
* Documentation: https://pynoorm.readthedocs.org.

Features
--------

* adjust query to support database parameter style
* find and prepare bind parameters from `*args`.

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

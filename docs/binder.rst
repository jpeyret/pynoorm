=====
The Binder Class
=====

A Binder is used to abstract differences in the underlying database's bind variable syntax (see PEP249_).

Calling `Binder.format(query_template, *args)` does the following:

	- Any variable in standard Python `%(key)s` format found in `query_template` are adjusted to use bind placeholders for the target database. i.e. *'where custid = %(custid)s'* would become *'where custid = ?'* on **sqlite3**. 

	- Each `key` is looked up against the `*args` list, first to last.  For each argument, a dictionary lookup is tried first, then an attribute lookup.  If the variable is not found, then the check is performed against the next argument.  If all args are exhausted, a **KeyError** is thrown.

	- When a variable is found in the `*args` list it is added to a database-dependent object which can be passed to `cursor.execute()` as its `parameter`.  For sqlite3, this might result in `("CUSTOMER001",)`, while Oracle would receive `{"custid":"CUSTOMER001"}`.

.. note::
	1. `Binder.format` is also aliased to `__call__` to allow calling instances directly.
	2. Refer to PEP249_ for details more details about expected variable placeholders and parameter objects.
	3. Oracle, SQLite, MS SQL Server and PostgreSQL are currently supported, but Binder subclasses are extremely simple to write.

	.. _PEP249: https://www.python.org/dev/peps/pep-0249


Basic use of Binder
----------------

Getting the appropriate binder for your database::

    import sqlite3
    from pynoorm.binder import Binder
    binder = Binder.factory(sqlite3.paramstyle)

This creates a binder for **sqllite3**::

	>>> pprint(binder)
	BinderQmark paramstyle=qmark supports: sqlite3


Create a query with substitution variables and some arguments::

    query_template = "select * from orders where custid = %(custid)s"

    class Argument(object):
        """simple class to hold attributes"""
        def __init__(self, **kwds):
            self.__dict__.update(kwds)

        def __repr__(self):
            return "argument:%s" % str(self.__dict__)[1:-1]

    arg0 = dict(custid="AMAZ")
    obj = Argument(custid="ACME", email="contact@acme.com")

Format the query template and prepare bind parameters for cursor.execute()::

    query, parameters = binder(query_template, arg0, obj)


`query` is now using **sqlite3** bind variable notation and `parameters` is as expected::

	>>> pprint(query)
	'select * from orders where custid = ?'
	>>> pprint(parameters)
	('AMAZ',)

You can now execute on an **sqlite3** cursor::

    cursor.execute(query, parameters)

Switching to **Oracle** just requires switching paramstyle when you create the binder::

    import cx_Oracle
    binder = Binder.factory(cx_Oracle.paramstyle)

    #this would have worked just as well
    #binder = Binder.factory("named")

	>>> pprint(binder)
	BinderNamed paramstyle=named supports: Oracle

	query, parameters = binder.format(query_template, dict(custid="Oracle customer"), arg0, obj)


`query` and `parameters` are now Oracle-compatible::

	>>> pprint(query)
	'select * from orders where custid = :custid'
	>>> pprint(parameters)
	{'custid': 'Oracle customer'}

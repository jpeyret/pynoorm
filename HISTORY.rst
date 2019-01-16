=======
History
=======

0.1.0 (2016-02-17)
------------------

* First release on github.

0.1.1 (2016-02-22)
------------------

* Registered on PyPI

0.2.0 (2016-04-12)
------------------

* Added support for Python 3.3+ and MySQL

0.3.0 (2017-09-06)
------------------

* Added SQL Server support
* Added Linker class to support object cross-referencing

0.4.0 (2018-07-24)
------------------

* Updating to Beta status
* Optimized Linker class
* Python list => SQL IN (xxx, yyy) functionality on Binder.

0.4.1 (2018-08-07)
------------------

* adjusted for Python 3 

0.4.2 (2019-01-10)
------------------

* ran Black for code formatting
* updated PyYaml to 4.2b4 to fix security vulnerability


0.4.3 (2019-01-10)
------------------

* removed Python 3.7 from tox since that Python version is not supported yet by tox.


0.4.4 (2019-01-15)
------------------

* adjusted list binding variable names from `__xxx_000` to `xxx_000__` because leading underscore are invalid under Oracle.
"""
Binder classes perform two functions through their format method

- given a query template with %(somevar)s python substition


    class MyClass(object):
        pass

    arg1 = MyClass()
    arg1.customer = 101

    default = MyClass()
    default.customer = 201
    arg2.country = "CAN"

    qry, sub = format("
        select *
        from customer
        where country = %(country)s
        and custid = %(customer)s", arg1, default)

    means that we will be fetching for country=CAN, custid=101

- the query template itself is transformed to a format
  that fits the underlying database's bind variable
  scheme which protects against sql injection attacks.

  For example, assuming an Oracle database (paramstyle="named")

  qry:
      "select * from customer where country = :country and custid = :customer"
  sub:
      {"country":"CAN", "customer" : 101}

  Postgres (paramstyle=""):

  qry:
      "select * from customer where country = :country and custid = :customer"
  sub:
      {"country":"CAN", "customer" : 101}


  a positional database (paramstyle="numeric") (NotImplementedError)
  would instead return

  qry:
      "select * from customer where country = :1 and custid = :2"
  sub:
      ["CAN", 101]


"""

import re


class Binder(object):
    """query template and substitution management - generic
    """

    def __init__(self, *args, **kwds):
        pass

    def format(self, tqry, *args):
        """
        :param tqry: query with optional substitution variables
                     Python style i.e.
                     select * from orders where custid = %(custid)s
        :param *args: zero or more arguments that will be checked
                      left-to-right, argument[<key>], getattr(argument,<key>)
        """

    def __repr__(self):
        msg = "%s paramstyle=%s" % (self.__class__.__name__, self.paramstyle)

        if hasattr(self, "supports"):
            msg += " supports: %s" % (self.supports)

        return msg

    def _case_sensitive(self, key):
        return [key]

    def _case_insensitive(self, key):
        if key == key.upper():
            return [key, key.lower()]
        if key == key.lower():
            return [key, key.upper()]
        return [key]

    _key_expand = _case_sensitive

    def _get_from_args(self, key_in):
        """generic way to look for a key in the arg list"""

        li_key = self._key_expand(key_in)

        for key in li_key:
            for arg in self.li_arg:
                try:
                    got = arg[key]
                    return got
                except (KeyError):
                    try:
                        # try getattr
                        got = getattr(arg, key)
                        return got
                    except AttributeError:
                        continue

                except (AttributeError, TypeError):
                    # no __getitem__, try getattr
                    try:
                        got = getattr(arg, key)
                        return got
                    except AttributeError:
                        continue

        try:
            raise KeyError(key_in)
        except Exception as e:
            raise

    @classmethod
    def factory(cls, paramstyle, case_insensitive=False):
        """
        return a Binder subclass instance appropriate
        to the underlying db library paramstyle bind variable

        :param paramstyle: parameter style string as per PEP-249
        :case_insensitive: %(custid)s will match {"custid":1} or {"CUSTID":2}, with priority
        going to the initial case.  mixed-case keys (custId) will only match {"custId":3}

        """

        try:
            inst = cls._di_paramstyle[paramstyle]()
            if case_insensitive:
                inst._key_expand = inst._case_insensitive

            return inst
        except KeyError:
            msg = """got:%s,
                  but expecting one of %s.
                  See
                  https://www.python.org/dev/peps/pep-0249/#paramstyle
                  for details""" % (
                paramstyle,
                "/".join(list(cls._di_paramstyle.keys())),
            )
            raise ValueError(msg)
        except NotImplementedError:
            msg = "%s is not implemented yet" % (paramstyle)
            raise NotImplementedError(msg)

    _di_paramstyle = {}

    # the regular expression pattern that looks for list type binds
    re_pattern_listsubstition = re.compile("%\([a-zA-Z0-9_]+\)l")

    # leading '__' variable name makes name clashes more unlikely
    T_LIST_KEYNAME = "%s_%03d__"

    # def _pre_process(self):
    #     """do nothing for now - intended to support list substitutions"""
    #     pass

    def _pre_process(self):
        li_listsubstition = self.re_pattern_listsubstition.findall(self.tqry)
        if li_listsubstition:
            self.preprocess_listsubstitution(li_listsubstition)

    def preprocess_listsubstitution(self, li_hit):
        """ this will transform %(xxx)l into %(__xxx_000)s, %(__xxx_001)s """

        di_list_sub = {}

        self.li_arg.insert(0, di_list_sub)

        for hit in li_hit:
            key = hit[2:-2]
            got = self._get_from_args(key)

            if not isinstance(got, (list, set)):
                raise ValueError(
                    "list substitutions require an iterable parameter: `%s` was of type `%s`"
                    % (key, type(got))
                )
                #
                # self.tqry = self.tqry.replace(hit, hit[:-1] + "s")
            else:

                li = []
                if not got:
                    # empty list or set
                    self.tqry = self.tqry.replace(hit, "NULL")
                    continue

                for ix, val in enumerate(got):
                    ikeyname = self.T_LIST_KEYNAME % (key, ix)
                    ikeyname_sub = "%%(%s)s" % (ikeyname)
                    di_list_sub[ikeyname] = val
                    li.append(ikeyname_sub)

                # replace the original bind %(xxx)l with
                # %(__xxx_000)s, %(__xxx_001)s, ...
                repval = ", ".join(li)
                self.tqry = self.tqry.replace(hit, repval)


class Binder_pyformat(Binder):
    """support Postgresql
       query template and substitution management for postgresql
       query is unchanged because postgresql is happy
       with %(somevar)s as a  bind
    """

    paramstyle = "pyformat"
    supports = "Postgresql"

    def _pre_process(self):
        li_listsubstition = self.re_pattern_listsubstition.findall(self.tqry)
        if li_listsubstition:
            self.preprocess_listsubstitution(li_listsubstition)

    def format(self, tqry, *args):
        """
        looks up substitutions and sets them up in dictionary self.sub

        postgresql accepts Python named variable so keeping the query as is

        select * from foo where bar = %(somebar)s"
        =>
        select * from foo where bar = %(somebar)s
        {"somebar" : value-found-for-somebar}
        """

        self.sub = {}
        self.li_arg = list(args)
        self.tqry = tqry

        self._pre_process()

        try:
            self.tqry % (self)
        except (Exception,) as e:
            raise

        # Postgresql query format stays as %(foo)s
        # so we just return the original query
        # (which _pre_process may have altered)
        return self.tqry, self.sub

    __call__ = format

    def __getitem__(self, key):
        if key in self.sub:
            return None

        got = self._get_from_args(key)
        self.sub[key] = got
        return None


PARAMSTYLE_QMARK = PARAMSTYLE_SQLITE = PARAMSTYLE_SQLSERVER = "qmark"


class BinderQmark(Binder):
    """ supports:  sqlite3, SQL Server
        query template and substitution management for sqlite3
        query changes from %(somevar)s to ?

        select * from foo where bar = %(somebar)s
        =>
        select * from foo where bar = ?,
        (value-found-for-somebar,)
    """

    paramstyle = PARAMSTYLE_QMARK
    supports = "sqlite3, mssql"
    qry_replace = "?"

    def format(self, tqry, *args):
        """
        looks up substitutions and sets them up in self.sub

        Note:
            Assuming both will be happy with a tuple.
            Might be one SQL Server needs a list instead.

        """
        self.tqry = tqry
        self._di_sub = {}
        self.sub = []
        self.li_arg = list(args)

        self._pre_process()

        try:
            qry = self.tqry % (self)
        except (Exception,) as e:
            raise

        return qry, tuple(self.sub)

    __call__ = format

    def __getitem__(self, key):
        """
        finds a substitution and append it to the bind list
        but also transforms the variable in the query to ?
        """

        qry_replace = self.qry_replace

        try:
            got = self._di_sub[key]
        except KeyError:
            got = self._di_sub[key] = self._get_from_args(key)

        self.sub.append(got)
        return qry_replace


class BinderFormat(BinderQmark):

    """supports: MySQL
       query template and substitution management for MySQL
       query changes from %(somevar)s to %s format
       parameters are (<var1>,<var2>,)

       Note: pretty much identical to BinderQmark/sqlite3
       except for the placeholder being %s

    """

    paramstyle = "format"
    supports = "MySQL"
    qry_replace = "%s"


class BinderNamed(Binder):
    """supports: Oracle
       query template and substitution management for Oracle
       query changes from %(somevar)s to :somevar format
       list-based substitutions:
           %(somelist)l :__somelist_000, :__somelist_001...
    """

    paramstyle = "named"
    supports = "Oracle"
    t_qry_replace = ":%s"

    def format(self, tqry, *args):
        """
        looks up substitutions and sets them up in self.sub

        but also transforms the query to Oracle named
        format
        "select * from foo where bar = %(somebar)s"
        =>
        "select * from foo where bar = :somebar "
        {"somebar" : value-found-for-somebar}
        
        """

        self.sub = {}
        self.li_arg = list(args)
        self.tqry = tqry

        self._pre_process()

        try:
            qry = self.tqry % (self)
        except (Exception,) as e:
            raise

        return qry, self.sub

    __call__ = format

    def __getitem__(self, key):
        """
        finds a substitution
        but also transforms the variable in the query to Oracle named
        format :foo
        """

        # already seen so already in the substition dict
        # replace the query's %(foo)s with :foo
        if key in self.sub:
            return self.t_qry_replace % (key)

        got = self._get_from_args(key)
        self.sub[key] = got
        return self.t_qry_replace % (key)

    """
    https://www.python.org/dev/peps/pep-0249/#paramstyle

    paramstyle  Meaning

    qmark       Question mark style, e.g. ...WHERE name=?   sequence
    numeric     Numeric, positional style, e.g. ...WHERE name=:1
    named       Named style, e.g. ...WHERE name=:name
    format      ANSI C printf format codes, e.g. ...WHERE name=%s
    pyformat    Python extended format codes, e.g. ...WHERE name=%(name)s
    """


ExperimentalBinderNamed = BinderNamed


class Binder_NotImplementedError(Binder):
    """not implemented yet"""

    paramstyle = "not implemented"

    def __init__(self, *args, **kwds):
        raise NotImplementedError()


# This is what decides how the Binder
# will process incoming template substitutions
Binder._di_paramstyle["pyformat"] = Binder_pyformat
Binder._di_paramstyle["named"] = BinderNamed
Binder._di_paramstyle[PARAMSTYLE_QMARK] = BinderQmark
Binder._di_paramstyle["format"] = BinderFormat

Binder._di_paramstyle["experimentalnamed"] = ExperimentalBinderNamed

# and these are not done yet
Binder._di_paramstyle["numeric"] = Binder_NotImplementedError

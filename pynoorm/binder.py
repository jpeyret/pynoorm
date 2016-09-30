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

    def _get_from_args(self, key):
        """generic way to look for a key in the arg list"""

        for arg in self.li_arg:
            try:
                got = arg[key]
                return got
            except (KeyError):
                try:
                    #try getattr
                    got = getattr(arg, key)
                    return got
                except AttributeError:
                    continue

            except (AttributeError, TypeError):
                #no __getitem__, try getattr
                try:
                    got = getattr(arg, key)
                    return got
                except AttributeError:
                    continue

        try:
            raise KeyError(key)
        except Exception as e:
            raise

    @classmethod
    def factory(cls, paramstyle):
        """
        return a Binder subclass instance appropriate
        to the underlying db library paramstyle bind variable

        :param paramstyle: parameter style string as per PEP-249
        """

        try:
            return cls._di_paramstyle[paramstyle]()
        except KeyError:
            msg = """got:%s,
                  but expecting one of %s.
                  See
                  https://www.python.org/dev/peps/pep-0249/#paramstyle
                  for details""" % \
                  (paramstyle, "/".join(list(cls._di_paramstyle.keys())))
            raise ValueError(msg)
        except NotImplementedError:
            msg = "%s is not implemented yet" % (paramstyle)
            raise NotImplementedError(msg)

    _di_paramstyle = {}

    #the regular expression pattern that looks for list type binds
    re_pattern_listsubstition = re.compile("%\([a-zZ-Z0-9_]+\)l")

    #leading '__' variable name makes name clashes more unlikely
    T_LIST_KEYNAME = "__%s_%03d"

    def _pre_process(self):
        """do nothing for now - intended to support list substitutions"""
        pass

    def preprocess_listsubstitution(self, li_hit):
        """ this will transform %(xxx)l into %(__xxx_000)s, %(__xxx_001)s """

        di_list_sub = {}

        self.li_arg.insert(0, di_list_sub)

        for hit in li_hit:
            key = hit[2:-2]
            got = self._get_from_args(key)

            if not isinstance(got, (list, set)):
                self.tqry = self.tqry.replace(hit, hit[:-1] + "s")
            else:

                li = []
                for ix, val in enumerate(got):
                    ikeyname = self.T_LIST_KEYNAME % (key, ix)
                    ikeyname_sub = "%%(%s)s" % (ikeyname)
                    self.sub[ikeyname] = val
                    li.append(ikeyname_sub)

                #replace the original bind %(xxx)l with
                #%(__xxx_000)s, %(__xxx_001)s, ...
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

        """
        self.sub = {}
        self.li_arg = list(args)
        self.tqry = tqry

        self._pre_process()

        try:
            qry = self.tqry % (self)
        except Exception, e:
            raise

        return qry, self.sub


        """



        self.sub = {}
        self.li_arg = list(args)
        self.tqry = tqry

        self._pre_process()

        try:
            self.tqry % (self)
        except Exception, e:
            raise

        #Postgresql query format stays as %(foo)s
        #so we just return the original query
        return self.tqry, self.sub

    __call__ = format

    def __getitem__(self, key):
        if key in self.sub:
            return None

        # got = getattr(arg, key)
        # self.sub[key] = got
        # return None

        got = self._get_from_args(key)
        self.sub[key] = got
        return None
        

class BinderQmark(Binder):
    """ supports:  sqlite3, SQL Server
        query template and substitution management for sqlite3
        query changes from %(somevar)s to ?

        select * from foo where bar = %(somebar)s
        =>
        select * from foo where bar = ?,
        (value-found-for-somebar,)
    """

    paramstyle = "qmark"
    supports = "sqlite3"

    def format(self, tqry, *args):
        """
        looks up substitutions and sets them up in self.sub

        Note:
            Assuming both will be happy with a tuple.
            Might be one SQL Server needs a list instead.

        """

        self.sub = []
        self.li_arg = list(args)
        qry = tqry % (self)
        return qry, tuple(self.sub)

    __call__ = format

    qry_replace = "?"

    def __getitem__(self, key):
        """
        finds a substitution and append it to the bind list
        but also transforms the variable in the query to ?
        """

        qry_replace = self.qry_replace

        for arg in self.li_arg:
            try:

                got = arg[key]
                self.sub.append(got)
                return qry_replace
            except (KeyError):
                #OK, we have __getitem__, just doesn't have key
                try:
                    #try getattr
                    got = getattr(arg, key)
                    self.sub.append(got)
                    return qry_replace
                except AttributeError:
                    continue

            except (AttributeError, TypeError):
                #no getitem, try getattr
                try:
                    got = getattr(arg, key)
                    self.sub.append(got)
                    return qry_replace
                except AttributeError:
                    continue
        else:
            raise KeyError(key)


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
    """

    paramstyle = "named"
    supports = "Oracle"

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
        qry = tqry % (self)
        return qry, self.sub

    __call__ = format

    def __getitem__(self, key):
        """
        finds a substitution
        but also transforms the variable in the query to Oracle named
        format :foo
        """

        t_qry_replace = ":%s"

        #already seen so already in the substition dict
        #replace the query's %(foo)s with :foo
        if key in self.sub:
            return t_qry_replace % (key)

        for arg in self.li_arg:
            try:

                got = arg[key]
                self.sub[key] = got
                return t_qry_replace % (key)
            except (KeyError):
                #we have __getitem__, just no key

                try:
                    #try getattr
                    got = getattr(arg, key)
                    self.sub[key] = got
                    return t_qry_replace % (key)
                except AttributeError:
                    continue

            except (AttributeError, TypeError):
                #no __getitem__, try getattr
                try:
                    got = getattr(arg, key)
                    self.sub[key] = got

                    return t_qry_replace % (key)
                except AttributeError:
                    continue

        try:
            raise KeyError(key)
        except Exception as e:
            raise

    """
    https://www.python.org/dev/peps/pep-0249/#paramstyle

    paramstyle  Meaning

    qmark       Question mark style, e.g. ...WHERE name=?
    numeric     Numeric, positional style, e.g. ...WHERE name=:1
    named       Named style, e.g. ...WHERE name=:name
    format      ANSI C printf format codes, e.g. ...WHERE name=%s
    pyformat    Python extended format codes, e.g. ...WHERE name=%(name)s
    """


class ExperimentalBinderNamed(BinderNamed):
    """supports: Oracle
       query template and substitution management for Oracle
       query changes from %(somevar)s to :somevar format
       list-based substitutions:  %(somelist)l :__somelist_000, :__somelist_001...
    """

    paramstyle = "named"
    supports = "Oracle"

    def _pre_process(self):
        li_listsubstition = self.re_pattern_listsubstition.findall(self.tqry)
        if li_listsubstition:
            self.preprocess_listsubstitution(li_listsubstition)

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
        except Exception, e:
            raise

        return qry, self.sub

    __call__ = format


    def __getitem__(self, key):
        """
        finds a substitution
        but also transforms the variable in the query to Oracle named
        format :foo
        """

        t_qry_replace = ":%s"

        #already seen so already in the substition dict
        #replace the query's %(foo)s with :foo
        if key in self.sub:
            return t_qry_replace % (key)

        got = self._get_from_args(key)
        self.sub[key] = got
        return t_qry_replace % (key)


    """
    https://www.python.org/dev/peps/pep-0249/#paramstyle

    paramstyle  Meaning

    qmark       Question mark style, e.g. ...WHERE name=?
    numeric     Numeric, positional style, e.g. ...WHERE name=:1
    named       Named style, e.g. ...WHERE name=:name
    format      ANSI C printf format codes, e.g. ...WHERE name=%s
    pyformat    Python extended format codes, e.g. ...WHERE name=%(name)s
    """


class Binder_NotImplementedError(Binder):
    """not implemented yet"""

    paramstyle = "not implemented"

    def __init__(self, *args, **kwds):
        raise NotImplementedError()

#This is what decides how the Binder
#will process incoming template substitutions
Binder._di_paramstyle["pyformat"] = Binder_pyformat
Binder._di_paramstyle["named"] = BinderNamed
Binder._di_paramstyle["qmark"] = BinderQmark
Binder._di_paramstyle["format"] = BinderFormat

Binder._di_paramstyle["experimentalnamed"] = ExperimentalBinderNamed

#and these are not done yet
Binder._di_paramstyle["numeric"] = Binder_NotImplementedError

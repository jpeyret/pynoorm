"""
Binder classes perform two functions through their format method

- given a list of arguments in addition to a query template they will find the
first argument that satisfies lookups driven by the query's substition variables
and return them in a suitable substition

    class MyClass(object):
        pass

    arg1 = MyClass()
    arg1.customer = 101

    default = MyClass()
    default.customer = 201
    arg2.country = "CAN"

    qry, sub = format("select * from customer where country = %(country)s and custid = %(customer)s", arg1, default)

    means that we will be fetching for country=CAN, custid=101

- the query template itself is transformed to a format that fits the underlying databases
  bind variable scheme which protects against sql injection attacks.

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


  a positional database (paramstyle="numeric") (NotImplementedError) would instead return

  qry:
      "select * from customer where country = :1 and custid = :2"
  sub:
      ["CAN", 101] 


"""


class Binder(object):
    """query template and substitution management - generic
    """

    def __init__(self, *args, **kwds):
        pass

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
See https://www.python.org/dev/peps/pep-0249/#paramstyle for details""" % \
    (paramstyle, "/".join(cls._di_paramstyle.keys()))
        except NotImplementedError, e2:
            msg = "%s is not implemented yet" % (paramstyle)
            raise NotImplementedError(msg)

    _di_paramstyle = {}


class Binder_pyformat(Binder):
    """query template and substitution management for postgresql 
       query is unchanged because postgresql is happy with %(somevar)s as a  bind
    """

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


        tqry % (self)
        return tqry, self.sub

    __call__ = format


    def __getitem__(self, keyname):
        if keyname in self.sub:
            return None

        for arg in self.li_arg:
            try:

                got = arg[keyname]
                self.sub[keyname] = got
                
                #"select * from foo where bar = %(somebar)s" => "select * from foo where bar = %(somebar)s"
                #so we're keeping the tqry at the end and the results of __getitem__ don't matter to the qry
                return None
            except (KeyError):
                continue
            except (AttributeError, TypeError):
                try:
                    got = getattr(arg, keyname)
                    self.sub[keyname] = got
                    return None
                except AttributeError:
                    continue

        try:
            raise KeyError(keyname)
        except Exception, e:
            raise


class Binder_qmark(Binder):
    """query template and substitution management for sqlite3
       query changes from %(somevar)s to ?


        select * from foo where bar = %(somebar)s
        => 
        select * from foo where bar = ?, 
        (value-found-for-somebar,)

    """

    def format(self, tqry, *args):
        """
        looks up substitutions and sets them up in self.sub
        """

        self.sub = []
        self.li_arg = list(args)
        self.qry = tqry % (self)
        return self.qry, tuple(self.sub)


    def __getitem__(self, keyname):
        """
        finds a substitution and append it to the bind list
        but also transforms the variable in the query to ?
        """

        for arg in self.li_arg:
            try:

                got = arg[keyname]
                self.sub.append(got)
                
                #replace the query's %(foo)s with ?
                return "?"
            except (KeyError):
                # continue

                try:
                    got = getattr(arg, keyname)
                    self.sub.append(got)
                    return "?"
                except AttributeError:
                    continue


            except (AttributeError, TypeError):
                try:
                    got = getattr(arg, keyname)
                    self.sub.append(got)

                    return "?"
                except AttributeError:
                    continue
        else:
            raise KeyError(keyname)



class Binder_named(Binder):
    """query template and substitution management for Oracle
       query changes from %(somevar)s to :somevar format
    """

        
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
        self.qry = tqry % (self)
        return self.qry, self.sub

    __call__ = format


    def __getitem__(self, keyname):
        """
        finds a substitution
        but also transforms the variable in the query to Oracle named 
        format :foo
        """

        t_qry_replace = ":%s"

        #already seen 
        #replace the query's %(foo)s with :foo
        if keyname in self.sub:
            return t_qry_replace % (keyname)

        for arg in self.li_arg:
            try:

                got = arg[keyname]
                self.sub[keyname] = got
                
                #replace the query's %(foo)s with :foo
                return t_qry_replace % (keyname)
            except (KeyError):
                continue
            except (AttributeError, TypeError):
                try:
                    got = getattr(arg, keyname)
                    self.sub[keyname] = got

                    return t_qry_replace % (keyname)
                except AttributeError:
                    continue

        try:
            raise KeyError(keyname)
        except Exception, e:
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

class Binder_NotImplementedError(Binder):
    """not implemented yet"""

    def __init__(self, *args, **kwds):
        raise NotImplementedError()

#This is what decides how the Varholder will process incoming template substitutions
Binder._di_paramstyle["pyformat"] = Binder_pyformat
Binder._di_paramstyle["named"] = Binder_named

#and these are not done yet
Binder._di_paramstyle["qmark"] = Binder_qmark
Binder._di_paramstyle["numeric"] = Binder_NotImplementedError
Binder._di_paramstyle["format"] = Binder_NotImplementedError

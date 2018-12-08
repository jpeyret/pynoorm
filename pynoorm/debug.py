
###################################################################
# Python 2 to 3.  !!!TODO!!!p4- Simplify after Python support ends.
###################################################################
try:
    _ = basestring
except (NameError,) as e:
    basestring = str
###################################################################


from pynoorm.binder import Binder_pyformat


class PGDebugBinder(Binder_pyformat):

    name_debug_dict = "di_query_debug"

    def __init__(self, name_debug_dict=None, multiple=False):

        if name_debug_dict:
            self.name_debug_dict = name_debug_dict

        self.multiple = multiple


    def track(self, target, query, queryname, multiple=False):
        
        try:
            di_qry = getattr(target, self.name_debug_dict, {})

            multiple = multiple or self.multiple

            if multiple:
                li = di_qry.setdefault(queryname, [])
                li.append(query)
            else:
                di_qry[queryname] = query

        except (Exception,) as e:
            raise


    def __getitem__(self, key):
        if key in self.sub:
            return None

        got = self._get_from_args(key)

        if isinstance(got, basestring):
            got = "'%s'" % (got)
        elif got is None:
            got = "null"
        #!!!todo!!!p4 - handle date/datetimes...

        self.sub[key] = got
        return None

    @classmethod
    def get_query(cls, tqry, *args, **kwds):

        flaginsecure = kwds.get("flaginsecure", True)

        inst = cls()
        dtqry, dsub = inst.format(tqry, *args)
        return "insecure:\n" * flaginsecure + dtqry % dsub

from pynoorm.binder import Binder_pyformat


class PGDebugBinder(Binder_pyformat):

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




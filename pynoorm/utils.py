class SlotProxy(object):
    """allow assignment to instances originally using __slots__"""

    def __init__(self, obj):
        self.__dict__["_obj"] = obj

    def __setattr__(self, attrname, value):
        if attrname in self._obj.__slots__:
            setattr(self._obj, attrname, value)
        else:
            self.__dict__[attrname] = value

    def __getattr__(self, attrname):
        try:
            return getattr(self._obj, attrname)
        except AttributeError:
            raise


def rename_bindnames(tqry, li_adjust):
    """use this to alter the query template to match expected attribute names in bind objects/dictionaries

       For example, a predefined query may be:  "select * from customers where custid = %(custid)s"
       But you are repeatedly passing bind dictionaries like {"customer" : "cust001"}, {"customer" : "cust002"}

       in that case qry_template = rename_bindnames(qry_template, [("custid","customer")])
       can make your client code simpler and speed it up as well.

    """
    for bindname, attrname in li_adjust:
        from_ = "%(" + bindname + ")s"
        to_ = "%(" + attrname + ")s"
        tqry = tqry.replace(from_, to_)
    return tqry

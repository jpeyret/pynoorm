
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

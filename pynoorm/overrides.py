########### debugging aids ##################
import pdb
from traceback import print_exc as xp


def cpdb():
    """do-nothing debugger test"""
    return cpdb.enabled


cpdb.enabled = False
########### debugging aids ##################


class AsObject(object):
    """used to convert result to objects"""

    def __init__(self, **kwds):
        self.__dict__.update(**kwds)


class Overrides(object):
    def __init__(self, attrnames, type_right=object, to_object_class=None):
        """prepare a dictionary for linking based on `left_key`
           :param attrnames:  attributes to set on overrides.  several forms are supported
           "tax" - a string, will get `tax` the right and assign it to `tax`
           ("rate","tax") assigns `tax` to `rate` as an alias.
           ["tax","state"] will get and assign both tax and state.
           Note that all attributes are expected to exist on the sources, KeyError or AttributeError
           happen otherwise.
           :param type_right: by default, attribute retrieval are done by `getattr` because objects
           are assumed.  passing in `dict` will use `dict[key]` instead.
           :param to_object_class:  used by `as_objects`.  You can pass in a class but it needs to 
           support keyword assignment for all attributes' assign aliases.

        """

        self.attrnames = attrnames
        self._dict = {}

        if to_object_class is None:
            self.to_object_class = AsObject
        else:
            self.to_object_class = to_object_class

        if issubclass(type_right, dict):
            self.setter = self._setter_attr_from_dict
        else:
            self.setter = self._setter_attr_from_object

        self._mapping = []

        if not isinstance(attrnames, list):
            attrnames = [attrnames]

        for attrname in attrnames:
            if isinstance(attrname, tuple):
                attrname_l, attrname_r = attrname
            else:
                attrname_l = attrname_r = attrname
            self._mapping.append((attrname_l, attrname_r))

    def __getitem__(self, attrname):
        return self._dict[attrname]

    def values(self):
        """needed to tell the Linker to expect dictionaries"""
        return [{}]

    def get(self, key, default=None):
        """returns an empty dictionary if the key doesnt exist yet"""

        try:
            return self._dict.setdefault(key, {})
        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def _setter_attr_from_dict(self, o_left, attrnames, o_right):
        """assigns right-side values to the working dictonary's aliases """
        try:
            for attrname_l, attrname_r in self._mapping:
                o_left[attrname_l] = o_right[attrname_r]
        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def _setter_attr_from_object(self, o_left, attrname, o_right):
        """assigns right-side attributes to the working dictonary's aliases """
        try:
            for attrname_l, attrname_r in self._mapping:
                o_left[attrname_l] = getattr(o_right, attrname_r)
        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def as_dict(self):
        """return overrides as dictionaries"""
        try:
            return self._dict.copy()
        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def as_objects(self):
        """return overrides as objects, using `to_object_class`, if provided """
        try:
            di = {}
            cls_ = self.to_object_class
            for k, v in self._dict.items():
                di[k] = cls_(**v)
            return di
        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def link(self, linker, data):
        """calls the linker providing itself as the lookup dictionary"""
        try:
            linker.link(self, data, attrname_on_left="_", setter_left=self.setter)
        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

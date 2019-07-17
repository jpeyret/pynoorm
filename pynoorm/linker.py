from operator import attrgetter, itemgetter, setitem
import collections

from six import string_types

from .utils import SlotProxy


########### debugging aids ##################
import pdb
from traceback import print_exc as xp


def cpdb():
    """do-nothing debugger test"""
    return cpdb.enabled


cpdb.enabled = False
########### debugging aids ##################


class LinkResultHelper(object):
    """returned by `Linker.link` and can be used to see what wasn't linked"""

    def __init__(_this, **kwds):
        """the odd bit with `_this` as first paremeter is because there is a `self`
           in the kwds from Linker.link, so that would clash.
           Assign all the Linker.link parameters to the instance's __dict__, then
           we go back to standard self"""

        # `self` in the kwds refers to the Linker instance
        kwds["linker"] = kwds.pop("self")
        # store everything that was passed as parameters to `link`.
        _this.__dict__.update(**kwds)

        self = _this
        self.right_orphans = []
        self.left_orphans = []
        self.exception = None

    def add_right_orphan(self, o):
        """track that linker.link didn't find a di_left[right.keyval]"""
        self.right_orphans.append(o)

    def initialize_rights(self):
        """initialize right-side objects that didn't get linked"""
        try:
            li = self.right_orphans
            return self._initialize(li, self.attrname_on_right, self.type_on_right)
        except (Exception,) as e:  # pragma: no cover
            if cpdb():
                pdb.set_trace()
            raise

    def _initialize(self, li, attrname, type_):
        """initialize objects that didn't get linked"""
        if not li:  # pragma: no cover
            return self

        linker = self.linker
        getter = self.linker._get_getter(li[0], attrname)
        _empty_setter = None
        for obj in li:
            try:
                v = getter(obj)
            except (AttributeError, KeyError):
                _empty_setter = _empty_setter or linker._get_empty_setter(
                    obj, attrname, type_
                )
                _empty_setter(obj, attrname, type_)
        return self

    def initialize_lefts(self):
        """initialize left-side objects that didn't get linked"""
        try:
            li = list(self.left.values())
            return self._initialize(li, self.attrname_on_left, self.type_on_left)
        except (Exception,) as e:  # pragma: no cover
            if cpdb():
                pdb.set_trace()
            raise


class Linker(object):
    """
        Used to set up very fast one or two-way links between
        objects.  You can think 'parent' for left and 'child' for right
        but that's not strictly true as sibling and scalar relationships
        are supported.  many-to-many is not supported.

    """

    TYPE_SCALAR = None

    def __init__(self, key_left):
        """key_left is either a string or tuple of strings
           stating which attributes/keys on future objects
           identify them.
           ex:  ("custid","order_id") for CustomerOrder Table
        """
        self.key_left = key_left

    def __repr__(self):
        return "%s on fields: %s" % (self.__class__.__name__, self.key_left)

    def _get_getter(self, obj, key):
        """returns a getter function appropriate for the getitem/getattr support in `obj`"""
        try:
            if isinstance(obj, collections.Mapping):
                if isinstance(key, string_types):
                    return itemgetter(key)
                elif isinstance(key, collections.Sequence):
                    return itemgetter(*key)
                else:
                    raise TypeError(
                        "expecting a string or tuple of strings as key.  got:%s[%s]"
                        % (str(key), type(key))
                    )
            else:
                if isinstance(key, string_types):
                    return attrgetter(key)
                elif isinstance(key, collections.Sequence):
                    return attrgetter(*key)
                else:
                    raise TypeError(
                        "expecting a string or tuple of strings as key.  got:%s[%s]"
                        % (str(key), type(key))
                    )

        except (Exception,) as e:  # pragma: no cover
            if cpdb():
                pdb.set_trace()
            raise

    def dict_from_list(self, li):
        """prepare a dictionary for linking based on `left_key`
           :param li:  a list of objects or dictionaries
        """

        key_left = self.key_left

        di_left = dict()

        li2 = None
        if isinstance(li, dict):
            li2 = li.values()
        li2 = li2 or li

        # !!!TODO!!!" 46.pynoorm/007.get_key_sampling"
        # sample from li2 rather than get_key or on each row
        get_key = None
        for o_left in li2:
            get_key = get_key or self._get_getter(o_left, key_left)
            try:
                keyval = get_key(o_left)
                # NOTE:  at this point, if we used a list instead of a simple assignment could we do m-n?
                di_left[keyval] = o_left
            except (Exception,) as e:  # pragma: no cover
                if cpdb():
                    pdb.set_trace()
                raise

        return di_left

    def link(
        self,
        left,
        right,
        attrname_on_left,
        setter_left=None,
        type_on_left=list,
        dictkey_attrname_left=None,
        key_right=None,
        setter_right=None,
        attrname_on_right=None,
        type_on_right=None,
    ):
        """
        :param left: a dictionary of objects or dictionaries which will be linked to right-side objects
        :param right: a list(iterator?) of objects or dictionaries.  you can also pass in a dictionary, its values will be used in that case
        :param attrname_on_left: the attribute name (or dictionary key) where the right-side object ref will be stored
        :param setter_left:  you can pass a callback to assign the right-side to left-side yourself.
                             call signature:  f(o_target, attrname, o_link)
        :param type_on_left:  None/Linker.scalar - direct assignment o_left.attrname_on_left = o_right
                              list (the default) - append each right-side object
                              dict - references are stored in a dict, but that requires dictkey_attrname_left to have been set as well.
                              
        :param dictkey_attrname_left: if your target's attribute is a dictonary, you need to provide the field that will be used on for that key
                                      ex:  attrname_on_left="tags", type_on_left=dict, dictkey_attrname_left="tagtype"
        :param key_right: specifying something here allows you to alias fields used in key_left
        :param setter_right: see setter_left
        :param attrname_on_right:  passing a value means a 2-way link
        :param type_on_right:  scalar is assumed, but list is also supported

        :return: LinkResultHelper instance to check orphans/assist initializations when needed

        """

        try:

            self.helper = LinkResultHelper(**locals())

            try:
                assert isinstance(attrname_on_left, string_types)
            except (AssertionError,) as e:  # pragma: no cover
                raise TypeError(
                    "attrname_on_left needs to be a valid python variable name"
                )

            key_left = self.key_left
            key_right = key_right or key_left

            # grab some sample objects from left and right
            # and use the samples to figure out getters and setters
            try:
                sample_left = next(iter(left.values()))
            except (StopIteration,) as e:
                self.helper.exception = ValueError("empty left", e)
                return self.helper

            it_right = iter(right)
            try:
                sample_right = next(it_right)
            except (StopIteration,) as e:
                self.helper.exception = ValueError("empty right", e)
                return self.helper

            get_key = self._get_getter(sample_right, key_right)
            setter_left = setter_left or self._get_setter(
                sample_left,
                attrname_on_left,
                type_on_left,
                dictkey_attrname_left,
                sample_right,
            )

            if attrname_on_right:
                setter_right = setter_right or self._get_setter(
                    sample_right, attrname_on_right, type_on_right
                )
            else:
                setter_right = None

            # do we need to set left-only? or left and right?
            if setter_right:
                prepped = self._preppedlinkleftright
            else:
                prepped = self._preppedlinkleft

            # finally, call the actual link, on the sample, then the rest
            for right_ in [[sample_right], it_right]:

                prepped(
                    left=left,
                    right=right_,
                    attrname_on_left=attrname_on_left,
                    setter_left=setter_left,
                    key_left=key_left,
                    key_right=key_right,
                    setter_right=setter_right,
                    attrname_on_right=attrname_on_right,
                    get_key=get_key,
                )

        except (Exception,) as e:  # pragma: no cover
            if cpdb():
                pdb.set_trace()
            raise
        else:
            return self.helper

    def _preppedlinkleft(
        self,
        left,
        right,
        attrname_on_left,
        setter_left,
        key_left,
        key_right,
        setter_right,
        attrname_on_right,
        get_key,
    ):
        """called from link, with all the getters/setters pre-discovered
           and knows that it won't be setting anything on the right side.
           however the signature is the same as `_preppedlinkleftright`, to unify and simplify
           calling
        """

        helper = self.helper
        for o_right in right:
            keyval = get_key(o_right)
            o_left = left.get(keyval, None)
            if o_left is None:
                helper.add_right_orphan(o_right)
                continue
            setter_left(o_left, attrname_on_left, o_right)

    def _preppedlinkleftright(
        self,
        left,
        right,
        attrname_on_left,
        setter_left,
        key_left,
        key_right,
        setter_right,
        attrname_on_right,
        get_key,
    ):
        """see `_preppedlinkleft`, but this will set attributes on the right
        """

        helper = self.helper
        for o_right in right:
            keyval = get_key(o_right)
            o_left = left.get(keyval, None)
            if o_left is None:
                helper.add_right_orphan(o_right)
                continue
            setter_left(o_left, attrname_on_left, o_right)
            setter_right(o_right, attrname_on_right, o_left)

    def _get_empty_setter(self, obj, attrname_on_tgt, type_on_tgt):
        """initialize the attribute to an appropriate empty value"""
        try:
            if isinstance(obj, collections.Mapping):

                def setdefault(tgt, attrname, value):
                    tgt.setdefault(attrname, value())

                def setvalue(tgt, attrname, value):
                    tgt[attrname] = value

                if callable(type_on_tgt):
                    return setdefault
                elif type_on_tgt is None:
                    return setvalue
                else:
                    raise NotImplementedError()
            else:

                def setdefault(tgt, attrname, value):
                    setattr(tgt, attrname, value())

                def setvalue(tgt, attrname, value):
                    setattr(tgt, attrname, value)

                if callable(type_on_tgt):
                    return setdefault
                elif type_on_tgt is None:
                    return setvalue
                else:
                    raise NotImplementedError()

        except (Exception,) as e:  # pragma: no cover
            if cpdb():
                pdb.set_trace()
            raise

    supported_target_types = [list, None]

    def _get_setter(
        self, obj, attrname_on_tgt, type_on_tgt, dictkey_attrname=None, o_src=None
    ):
        """determines the appropriate function to set values
           - mapping types will privilege setitem
           - other instance will use setattr

           type_on_tgt (default assumption is left 0..1 <=> 0..N right meaning that the left attribute is a list)
           also determines how to initialize attribute and add values.
        """

        assert isinstance(attrname_on_tgt, string_types)
        try:
            if isinstance(obj, collections.Mapping):

                def append(tgt, attrname, value):
                    li = tgt.setdefault(attrname, [])
                    li.append(value)

                if type_on_tgt == list:
                    return append
                elif type_on_tgt == dict:
                    raise NotImplementedError()
                elif type_on_tgt is None:
                    return setitem
                else:
                    raise TypeError(
                        "unsupported target type:%s.  Supported are: %s"
                        % (type_on_tgt, self.supported_target_types)
                    )
            else:

                def append(tgt, attrname, value):
                    li = getattr(tgt, attrname, None)
                    if li is None:
                        li = []
                        setattr(tgt, attrname, li)
                    li.append(value)

                if type_on_tgt == list:
                    return append
                elif type_on_tgt == dict:

                    getter_left = self._get_getter(o_src, dictkey_attrname)

                    def setdict(tgt, attrname, value):

                        di = getattr(tgt, attrname, None)
                        if di is None:
                            di = {}
                            setattr(tgt, attrname, di)
                        keyval = getter_left(value)
                        di[keyval] = value

                    return setdict

                elif type_on_tgt is None:
                    return setattr
                else:
                    raise TypeError(
                        "unsupported target type:%s.  Supported are: %s"
                        % (type_on_tgt, self.supported_target_types)
                    )

        except (Exception,) as e:  # pragma: no cover
            if cpdb():
                pdb.set_trace()
            raise

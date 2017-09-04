from operator import attrgetter, itemgetter, setitem
import collections

########### debugging aids ##################
class module_settings:
    USE_PDB = False
import pdb
from traceback import print_exc as xp
########### debugging aids ##################


class LinkResultHelper(object):

    def update(self, **kwds):
        self.__dict__.update(**kwds)        

    def __init__(_this, **kwds):
        """the odd bit with `_this` as first paremeter is because there is a `self`
           in the kwds from Linker.link, so that would clash.
           Assign all the Linker.link parameters to the instance's __dict__, then
           we go back to standard self"""

        try:
            kwds["linker"] = kwds.pop("self")
        except KeyError:
            pass

        _this.__dict__.update(**kwds)

        self = _this
        self.right_orphans = []
        self.left_orphans = []
        self.exception = None

    def set_exception(self, e):
        self.exception = e
        return e

    def add_right_orphan(self, o):
        """track that linker.link didn't find a di_left[right.keyval]"""
        self.right_orphans.append(o)

    def initialize_lefts(self):
        try:
            li = self.left.values()
            if not li:
                return

            linker = self.linker
            attrname_on_left = self.attrname_on_left
            type_on_left = self.type_on_left
            getter = self.linker._get_getter(li[0], attrname_on_left)

            _empty_setter_left = None
            for l_obj in li:
                try:
                    v = getter(l_obj)
                except (AttributeError, KeyError):
                    _empty_setter_left = _empty_setter_left or linker._get_empty_setter(l_obj, attrname_on_left, type_on_left)
                    _empty_setter_left(l_obj, attrname_on_left, type_on_left)

            return self
        except Exception, e:
            # logger.error(repr(e)[:100])
            print e
            pdb.set_trace() #!!! remove
            raise


class Linker(object):
    """
        Used to set up very fast one or two-way links between
        objects.  You can think 'parent' for left and 'child' for right
        but that's not strictly true as sibling and scalar relationships
        are supported.  many-to-many is not supported.

        You need to provide a common key to link objects

        ex:
        orders = select customer_id, id, total from CustomerOrder where customer_id between 100 and 200
        itemlines  = select customer_id, order_id, id, amount from OrderLines where customer_id = 100 and 200

        #orders are uniquely identified by customer_id and id
        linker = Linker(("customer_id", "id"))

        #create a dictionary where orders can be looked up by customer and id.
        di_orders = linker.dict_from_list(orders)

        #link the order lines, but alias CustomerOrder.id to OrderLines.order_id
        linker.link(orders, itemlines, attrname_on_left="lines", attrname_on_right="owner", key_right=("customer_id","order_id"))

    """

    TYPE_SCALAR = None

    def __repr__(self):
        return "Linker.%s" % (getattr(self,"name", None) or id(self))


    def __init__(self, key_left):
        """key_left is either a string or tuple of strings
           stating which attributes/keys on future objects
           identify them.
           ex:  ("customer_id","order_id") for CustomerOrder Table
        """
        self.key_left = key_left

    def _get_getter(self, obj, key):
        """returns a getter function appropriate for the getitem/getattr support in `obj`"""
        try:
            if isinstance(obj, collections.Mapping):
                if isinstance(key, basestring):
                    return itemgetter(key)
                elif isinstance(key, collections.Sequence):
                    return itemgetter(*key)
                else:
                    raise TypeError("expecting a string or tuple of strings as key.  got:%s[%s]" % (str(key),type(key)) )
            else:
                if isinstance(key, basestring):
                    return attrgetter(key)
                elif isinstance(key, collections.Sequence):
                    return attrgetter(*key)
                else:
                    raise TypeError("expecting a string or tuple of strings as key.  got:%s[%s]" % (str(key),type(key)) )

        except Exception, e:

            if module_settings.USE_PDB: pdb.set_trace()
            raise

    def dict_from_list(self, li):
        """given that we know the expected key accessor on the left we'll set up a dictionary for linking"""

        key_left = self.key_left

        di_left = dict()

        li2 = None
        if isinstance(li, dict):
            li2 = li.values()
        li2 = li2 or li

        get_key = None
        for o_left in li2:
            get_key = get_key or self._get_getter(o_left, key_left)
            try:
                keyval = get_key(o_left)
                #NOTE:  at this point, if we used a list instead of a simple assignment could we do m-n?
                di_left[keyval] = o_left
            except Exception, e:
                if module_settings.USE_PDB: pdb.set_trace()
                raise

        return di_left


    def link(self, left, right, attrname_on_left
        ,setter_left=None
        ,type_on_left=list
        ,dictkey_attrname_left=None
        ,key_right=None
        ,setter_right=None
        ,attrname_on_right=None
        ,type_on_right=None
        ):
        """
        :param left: a dictionary of objects or dictionaries which will be linked to right-side objects
        :param right: a list(iterator?) of objects or dictionaries.  you can also pass in a dictionary, its values will be used in that case
                              !!!TODO!!! test
        :param attrname_on_left: the attribute name (or dictionary key) where the right-side object ref will be stored

        :param setter_left:  you can pass a callback to assign the right-side to left-side yourself.
                             call signature:  f(o_left, attrname, o_right)

        :param type_on_left:  3 possibilities:
                              None or Linker.scalar - direct assignment o_left.attrname_on_left = o_right
                              list (the default) - append each right-side object
                              dict - references are stored in a dict, but that requires dictkey_attrname_left to have been set as well.
                              !!!TODO!!! rename dictkey_attrname_left to dictkey_attrname_right (cuz the lookup is on the right-side object)



        :return: LinkResultHelper instance to check orphans/assist initializations when needed

        """



        """the core method

        left - a dictionary of objects or dictionaries that have been keyed by the left_key

        right - a list of objects or dictionaries

        setter_left or setter_right - if specified, a function with a signature of f(obj, attrname, value).  Note that you would need to
        provide in the form obj_left.__class__.funcname, in order to unbind the method so that obj gets the value of the targets

        attrname_on_left, right - obj_left.attrname_on_left = obj_right.  by default, the left object is not assigned to the right objects

        type_on_left = multiple right children are assumed for each left, so this is a list.  set it to None to have a simple attribute.

        type_on_right = the right object is assumed to be a child with one parent
            (actually the results of getkey are handled as a scalar so many-many would not work)

        key_right - assume the same key as the left objects', but you could use this to alias attribute names.

            ex:  ("customer_id","order_id") for OrderLines, if OrderLines.order_id referred to CustomerOrder.id

        """

        try:

            self.helper = LinkResultHelper(**locals())

            try:
                assert isinstance(attrname_on_left, basestring)
            except AssertionError, e:
                raise TypeError("attrname_on_left needs to be a valid python variable name")

            key_left = self.key_left
            key_right = key_right or key_left

            get_key = _empty_setter_right = _empty_setter_left = None

            for o_right in right:

                #keeping this in-loop supports iterators on the right.
                get_key = get_key or self._get_getter(o_right, key_right)
                keyval = get_key(o_right)

                #NOTE:  at this point, if we handled a list instead of a scalar could we do m-n?
                o_left = left.get(keyval, None)
                if o_left is None:
                    self.helper.add_right_orphan(o_right)
                    continue

                #keep this like that as well, since it might not be cheap to pick the "first left"
                setter_left = setter_left or self._get_setter(o_left, attrname_on_left, type_on_left, dictkey_attrname_left, o_right)
                setter_left(o_left, attrname_on_left, o_right)

                if attrname_on_right:
                    setter_right = setter_right or self._get_setter(o_right, attrname_on_right, type_on_right)
                    setter_right(o_right, attrname_on_right, o_left)

        except Exception, e:
            if module_settings.USE_PDB: pdb.set_trace()
            raise
        finally:
            return self.helper


    def _get_empty_setter(self, obj, attrname_on_tgt, type_on_tgt, check_empty=False):
        """initialize the attribute to an appropriate empty value
        check_empty avoids overwriting if already set"""
        try:
            if isinstance(obj, collections.Mapping):

                def setdefault(tgt, attrname, value):
                    if check_empty and tgt.has_key(attrname):
                        return

                    tgt.setdefault(attrname, value())

                def setvalue(tgt, attrname, value):
                    if check_empty and tgt.has_key(attrname):
                        return

                    tgt[attrname] = value

                if callable(type_on_tgt):
                    return setdefault
                elif type_on_tgt is None:
                    return setvalue
                else:
                    raise NotImplementedError()

            else:

                def setdefault(tgt, attrname, value):
                    if check_empty and hasattr(tgt, attrname):
                        return

                    setattr(tgt, attrname, value())

                def setvalue(tgt, attrname, value):
                    if check_empty and hasattr(tgt, attrname):
                        return
                    setattr(tgt, attrname, value)

                if callable(type_on_tgt):
                    return setdefault
                elif type_on_tgt is None:
                    return setvalue
                else:
                    raise NotImplementedError()

        except Exception, e:
            if module_settings.USE_PDB: pdb.set_trace()
            raise

    supported_target_types = [dict, list, None]
    supported_target_types = [list, None]

    def _get_setter(self, obj, attrname_on_tgt, type_on_tgt, dictkey_attrname=None, o_src=None):
        """determines the appropriate function to set values
           - mapping types will privilege setitem
           - other instance will use setattr

           type_on_tgt (default assumption is left 0..1 <=> 0..N right meaning that the left attribute is a list)
           also determines how to initialize attribute and add values.
        """


        assert isinstance(attrname_on_tgt, basestring)

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
                    raise TypeError("unsupported target type:%s.  Supported are: %s" % (type_on_tgt, self.supported_target_types))
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
                    raise TypeError("unsupported target type:%s.  Supported are: %s" % (type_on_tgt, self.supported_target_types))

        except Exception, e:
            if module_settings.USE_PDB: pdb.set_trace()
            raise


# -*- coding: utf-8 -*-

"""
test_pynoorm
----------------------------------

Tests for `pynoorm.linker` module, 
"""
import pprint 
import unittest
from time import time

from pynoorm.linker import Linker, SlotProxy

import random
import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

import sys

### debuggging stuff###############
from traceback import print_exc as xp
import pdb

def cpdb(e=None):
    """conditional debugging
       use with:  `if cpdb(): pdb.set_trace()` 
    """
    return cpdb.enabled

cpdb.enabled = False
###################################




from test_linker import ppp, Customer

class AsObject(object):
    """used to convert result to objects"""
    def __init__(self, **kwds):
        self.__dict__.update(**kwds)

class OverrideManager(object):
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

    def get(self, key, default=None):
        """returns an empty dictionary if the key doesnt exist yet"""

        try:
            return self._dict.setdefault(key, {})
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise


    def _setter_attr_from_dict(self, o_left, attrnames, o_right):
        """assigns right-side values to the working dictonary's aliases """
        try:
            for attrname_l, attrname_r in self._mapping:
                o_left[attrname_l] = o_right[attrname_r]
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def _setter_attr_from_object(self, o_left, attrname, o_right):
        """assigns right-side attributes to the working dictonary's aliases """
        try:
            for attrname_l, attrname_r in self._mapping:
                o_left[attrname_l] = getattr(o_right, attrname_r)
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def as_dictionaries(self):
        """return overrides as dictionaries"""
        try:
            return self._dict.copy()
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
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
            if cpdb(): pdb.set_trace()
            raise

    def link(self, linker, data):
        """calls the linker providing itself as the lookup dictionary"""
        try:
            linker.link(self, data, attrname_on_left="ignore", setter_left=self.setter)
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise



class Test_SelfLinker(unittest.TestCase):

    def setUp(self):
        try:

            self.linker = Linker(key_left="custid")

            self.customer_rates = [
                Customer(custid="custA", tax=1.0, state="A")
                ,Customer(custid="custB", tax=1.0, state="Z")
                ,Customer(custid="custC", tax=3.0, state="C")
            ]

            self.customer_rates_overrides = [
                Customer(custid="custB", tax=2.0, state="B")
                ,Customer(custid="custD", tax=4.0, state="D")
            ]

            self.di_customer_rates = [vars(obj) for obj in self.customer_rates]
            self.di_customer_rates_overrides = [vars(obj) for obj in self.customer_rates_overrides]
        
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise



    def test_001_tax(self):
        """basic test"""

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = OverrideManager(attrnames="tax")

            linker.link(lookup, self.customer_rates, attrname_on_left="tax", setter_left=lookup.setter)
            linker.link(lookup, self.customer_rates_overrides, attrname_on_left="tax", setter_left=lookup.setter)

            di_data = lookup.as_objects()

            lookup = OverrideManager(attrnames="tax")


            lookup.link(linker, self.customer_rates)
            lookup.link(linker, self.customer_rates_overrides)

            di_data2 = lookup.as_objects()

            self.assertFalse(linker.helper.right_orphans)

            di_data3 = lookup.as_dictionaries()


            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr+1)
                key = "cust%s" % id_

                #version 1. direct
                inst = di_data[key]
                got = inst.tax
                msg = "explicit.%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

                #version 2. link on lookup
                inst = di_data2[key]
                got = inst.tax
                msg = "implicit.%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)


                di = di_data3[key]
                got = di["tax"]
                msg = "as_dict.%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)



        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise


    def test_002_tax_state(self):
        """get multiple attributes at one go"""

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = OverrideManager(attrnames=["tax","state"])

            lookup.link(linker, self.customer_rates)
            lookup.link(linker, self.customer_rates_overrides)

            di_data = lookup.as_objects()

            self.assertFalse(linker.helper.right_orphans)


            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr+1)
                key = "cust%s" % id_

                inst = di_data[key]

                got = inst.tax
                msg = "explicit.%s.tax.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

                exp = id_
                got = inst.state
                msg = "implicit.%s.state.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def test_003_aliasing(self):
        """translate right attribute name to left attribute name"""
        try:
            #make a lookup dictionary point to customers by custid
            lookup = OverrideManager(attrnames=[("rate","tax")])

            lookup.link(self.linker, self.customer_rates)
            lookup.link(self.linker, self.customer_rates_overrides)

            di_data = lookup.as_objects()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr+1)
                key = "cust%s" % id_

                inst = di_data[key]

                got = inst.rate
                msg = "explicit.%s.tax.exp:%s:<>:%s:got.rate" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb(): pdb.set_trace()

    def test_004_tax_from_dict(self):
        """source data is in dictionaries"""
        try:
            #create the linker and tell it what the left-hand key will be

            lookup = OverrideManager(attrnames="tax", type_right=dict)

            lookup.link(self.linker, self.di_customer_rates)
            lookup.link(self.linker, self.di_customer_rates_overrides)

            di_data = lookup.as_objects()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr+1)
                key = "cust%s" % id_

                inst = di_data[key]
                got = inst.tax
                msg = "%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def test_005_custom_object(self):
        """source data is in dictionaries"""
        try:
            #create the linker and tell it what the left-hand key will be

            othervalue_=3

            class CustomObject(object):
                def __init__(self, tax, othervalue=othervalue_):
                    self.tax = tax
                    self.othervalue = othervalue         

            lookup = OverrideManager(attrnames="tax", type_right=dict, to_object_class=CustomObject)

            lookup.link(self.linker, self.di_customer_rates)
            lookup.link(self.linker, self.di_customer_rates_overrides)

            di_data = lookup.as_objects()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr+1)
                key = "cust%s" % id_



                inst = di_data[key]

                self.assertEqual(inst.othervalue, othervalue_)

                got = inst.tax
                msg = "%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise



if __name__ == '__main__':

    #conditional debugging, but not in nosetests
    if "--pdb" in sys.argv:
        cpdb.enabled = not sys.argv[0].endswith("nosetests")
        sys.argv.remove("--pdb")

    sys.exit(unittest.main())

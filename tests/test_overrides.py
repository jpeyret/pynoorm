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




from test_linker import DummyObject, pretty, methi, ppp, Customer

class Value(object):
    def __init__(self, **kwds):
        self.__dict__.update(**kwds)

class OverrideDict(object):
    def __init__(self, attrnames, source_right=object):
        self.attrnames = attrnames
        self._dict = {}
        self.get = self._get_write

        if issubclass(source_right, dict):
            self.setter = self.setter_attr_from_dict
        else:
            self.setter = self.setter_attr_from_object

        self._mapping = []

        if not isinstance(attrnames, list):
            attrnames = [attrnames]

        for attrname in attrnames:
            if isinstance(attrname, tuple):
                attrname_l, attrname_r = attrname
            else:
                attrname_l = attrname_r = attrname
            self._mapping.append((attrname_l, attrname_r))            



    def __getattr__(self, attrname):
        return getattr(self._dict, attrname)

    def __getitem__(self, attrname):
        return self._dict[attrname]


    def _get_write(self, key, default=None):
        try:
            return self._dict.setdefault(key, {})
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def _get_read(self, key, default=None):
        try:
            return self._dict.get(key, default)
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def setter_attr_from_dict(self, o_left, attrnames, o_right):
        try:
            o_left[attrname_l] = o_right.get(attrname_r)
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def setter_attr_from_object(self, o_left, attrname, o_right):
        try:
            for attrname_l, attrname_r in self._mapping:
                o_left[attrname_l] = getattr(o_right, attrname_r)
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def get_workdict(self):
        return self._dict

    def get_workdict_as_objects(self):
        try:
            di = {}
            for k, v in self._dict.items():
                di[k] = Value(**v)

            return di
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise

    def link(self, linker, data):
        try:
            linker.link(self, data, attrname_on_left="ignore", setter_left=self.setter)
        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise



class Test_SelfLinker(unittest.TestCase):

    def setUp(self):
        self.customer_rates = [
            Customer(custid="custA", tax=1.0, state="A")
            ,Customer(custid="custB", tax=1.0, state="Z")
            ,Customer(custid="custC", tax=3.0, state="C")
        ]

        self.customer_rates_overrides = [
            Customer(custid="custB", tax=2.0, state="B")
            ,Customer(custid="custD", tax=4.0, state="D")
        ]


    def test_tax(self):
        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = OverrideDict(attrnames="tax")

            linker.link(lookup, self.customer_rates, attrname_on_left="tax", setter_left=lookup.setter)
            linker.link(lookup, self.customer_rates_overrides, attrname_on_left="tax", setter_left=lookup.setter)

            di_data = lookup.get_workdict_as_objects()

            lookup = OverrideDict(attrnames="tax")


            lookup.link(linker, self.customer_rates)
            lookup.link(linker, self.customer_rates_overrides)

            di_data2 = lookup.get_workdict_as_objects()

            self.assertFalse(linker.helper.right_orphans)


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

        except (Exception,) as e:
            if cpdb(): pdb.set_trace()
            raise


    def test_tax_state(self):
        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = OverrideDict(attrnames=["tax","state"])

            lookup.link(linker, self.customer_rates)
            lookup.link(linker, self.customer_rates_overrides)

            di_data = lookup.get_workdict_as_objects()

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



if __name__ == '__main__':

    #conditional debugging, but not in nosetests
    if "--pdb" in sys.argv:
        cpdb.enabled = not sys.argv[0].endswith("nosetests")
        sys.argv.remove("--pdb")

    sys.exit(unittest.main())

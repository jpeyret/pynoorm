# -*- coding: utf-8 -*-

"""
test_pynoorm
----------------------------------

Tests for `pynoorm.linker` module, 
"""
import pprint
import unittest
from time import time


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

from pynoorm.linker import Linker
from pynoorm.overrides import Overrides


from pynoorm.tests.test_linker import ppp, Customer


class Test_SelfLinker(unittest.TestCase):
    def setUp(self):
        try:

            self.linker = Linker(key_left="custid")

            self.customer_rates = [
                Customer(custid="custA", tax=1.0, state="A"),
                Customer(custid="custB", tax=1.0, state="Z"),
                Customer(custid="custC", tax=3.0, state="C"),
            ]

            self.customer_rates_overrides = [
                Customer(custid="custB", tax=2.0, state="B"),
                Customer(custid="custD", tax=4.0, state="D"),
            ]

            self.di_customer_rates = [vars(obj) for obj in self.customer_rates]
            self.di_customer_rates_overrides = [
                vars(obj) for obj in self.customer_rates_overrides
            ]

        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def test_001_tax(self):
        """basic test"""

        try:
            # create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            # make a lookup dictionary point to customers by custid
            lookup = Overrides(attrnames="tax")

            linker.link(
                lookup,
                self.customer_rates,
                attrname_on_left="tax",
                setter_left=lookup.setter,
            )
            linker.link(
                lookup,
                self.customer_rates_overrides,
                attrname_on_left="tax",
                setter_left=lookup.setter,
            )

            di_data = lookup.as_objects()

            lookup = Overrides(attrnames="tax")

            lookup.link(linker, self.customer_rates)
            lookup.link(linker, self.customer_rates_overrides)

            di_data2 = lookup.as_objects()

            self.assertFalse(linker.helper.right_orphans)

            di_data3 = lookup.as_dict()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr + 1)
                key = "cust%s" % id_

                # version 1. direct
                inst = di_data[key]
                got = inst.tax
                msg = "explicit.%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

                # version 2. link on lookup
                inst = di_data2[key]
                got = inst.tax
                msg = "implicit.%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

                di = di_data3[key]
                got = di["tax"]
                msg = "as_dict.%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def test_002_tax_state(self):
        """get multiple attributes at one go"""

        try:
            # create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            # make a lookup dictionary point to customers by custid
            lookup = Overrides(attrnames=["tax", "state"])

            lookup.link(linker, self.customer_rates)
            lookup.link(linker, self.customer_rates_overrides)

            di_data = lookup.as_objects()

            self.assertFalse(linker.helper.right_orphans)

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr + 1)
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
            if cpdb():
                pdb.set_trace()
            raise

    def test_003_aliasing(self):
        """translate right attribute name to left attribute name"""
        try:
            # make a lookup dictionary point to customers by custid
            lookup = Overrides(attrnames=[("rate", "tax")])

            lookup.link(self.linker, self.customer_rates)
            lookup.link(self.linker, self.customer_rates_overrides)

            di_data = lookup.as_objects()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr + 1)
                key = "cust%s" % id_

                inst = di_data[key]

                got = inst.rate
                msg = "explicit.%s.tax.exp:%s:<>:%s:got.rate" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()

    def test_004_tax_from_dict(self):
        """source data is in dictionaries"""
        try:
            # create the linker and tell it what the left-hand key will be

            lookup = Overrides(attrnames="tax", type_right=dict)

            lookup.link(self.linker, self.di_customer_rates)
            lookup.link(self.linker, self.di_customer_rates_overrides)

            di_data = lookup.as_objects()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr + 1)
                key = "cust%s" % id_

                inst = di_data[key]
                got = inst.tax
                msg = "%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise

    def test_005_custom_object(self):
        """source data is in dictionaries"""
        try:
            # create the linker and tell it what the left-hand key will be

            othervalue_ = 3

            class CustomObject(object):
                def __init__(self, tax, othervalue=othervalue_):
                    self.tax = tax
                    self.othervalue = othervalue

            lookup = Overrides(
                attrnames="tax", type_right=dict, to_object_class=CustomObject
            )

            lookup.link(self.linker, self.di_customer_rates)
            lookup.link(self.linker, self.di_customer_rates_overrides)

            di_data = lookup.as_objects()

            for cntr, id_ in enumerate("ABCD"):
                exp = float(cntr + 1)
                key = "cust%s" % id_

                inst = di_data[key]

                self.assertEqual(inst.othervalue, othervalue_)

                got = inst.tax
                msg = "%s.exp:%s:<>:%s:got" % (key, exp, got)
                self.assertEqual(exp, got, msg)

        except (Exception,) as e:
            if cpdb():
                pdb.set_trace()
            raise


if __name__ == "__main__":

    # conditional debugging, but not in nosetests
    if "--pdb" in sys.argv:
        cpdb.enabled = not sys.argv[0].endswith("nosetests")
        sys.argv.remove("--pdb")

    sys.exit(unittest.main())

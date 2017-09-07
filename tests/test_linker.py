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

def ppdb(e=None):
    """conditional debugging
       use with:  `if ppdb(): pdb.set_trace()` 
    """
    return ppdb.enabled

ppdb.enabled = False
###################################


size = 3
SHUFFLE_BY_DEFAULT = False




class DummyObject(object):
    """demos __getitem__, getattr precedence"""
    def __init__(self, _classname=None, **kwds):
        self.__dict__.update(**kwds)
        self._classname = _classname or self.__class__.__name__

# class DummyObjectPrint(DummyObject)

#     def __init__(self, **kwds):
#         self.__dict__.update(**kwds)

    def __repr__(self):
        di = self.__dict__.copy()
        try:
            del di["_classname"]
        except KeyError:
            pass

        res = "%s" % (di)
        res = res.replace("{","")
        res = res.replace("}","")
        res = res.replace(":","=")
        res = res.replace("'","")

        return "[%s %s]" % (getattr(self, "_classname", self.__class__.__name__), res)

class Customer(DummyObject): pass

class Address(DummyObject): pass

class Order(DummyObject): pass

DEFAULT_KEY = "custid"

SALES_TAX = [
    DummyObject(_classname="Tax", country="USA", state="OR", tax=0),
    DummyObject(_classname="Tax", country="CAD", state="BC", tax=12.5),
    DummyObject(_classname="Tax", country="USA", state="WA", tax=6.5),
]

di_state_tax = dict([(o.state,o.tax) for o in SALES_TAX])

def enhance_country_data(list_, attrname_country="country", attrname_state="state"):
    """spike incoming objects with a data from SALES_TAX"""

    for cntr, o in enumerate(list_):

        index = cntr % (len(SALES_TAX))

        country = SALES_TAX[index].country
        state = SALES_TAX[index].state
        if isinstance(o, dict):
            o[attrname_country] = country
            o[attrname_state] = state
        else:
            setattr(o,attrname_country, country)
            setattr(o,attrname_state, state)


def get_sample_data(customer_pk, order_fk=None, address_fk=None, shuffle=SHUFFLE_BY_DEFAULT, size=size, print_ = True):
    """prepare some simple customer/order data.  
       -    the _pk, _fk parameters allow you to vary the fieldnames used to link
       -    shuffle - shuffles the lists so that they are not ordered

       xref is populated so that it always matches the customer even on other object.

    """

    res = DummyObject(customers=[], orders=[], addresses=[])

    order_fk = order_fk or customer_pk
    address_fk = address_fk or customer_pk

    for cntr in range(1, size+1):

        custkey = "custid_%s" % (cntr)

        di = {
            customer_pk : custkey,
            "xref" : cntr,
        }

        res.customers.append(di)

        di = {
            address_fk : custkey,
            "xref" : cntr,
            "street" : "10%d 1st Ave." % (cntr),
        }

        res.addresses.append(di)

        numorders = min(10, cntr+1)

        for ordernum in range(1, numorders):
            di = {
                "order_id" : cntr * 1000 + ordernum,
                "xref" : cntr,
                order_fk : custkey
            }
            res.orders.append(di)

    if shuffle:
        random.shuffle(res.customers)
        random.shuffle(res.orders)
        random.shuffle(res.addresses)

    if print_:
        print("\n\ndata:") #!!!
        ppp(res)           #!!!

    return res

import inspect #!!! remove

pretty = pprint.PrettyPrinter(indent=2)

def methi(aMethod):             #!!! remove
    print (inspect.getargspec(aMethod)) #!!! remove

def ppp(obj):
    if not isinstance(obj, (list, dict)):
        di = vars(obj)
        try:
            del di["_classname"]
        except KeyError:
            pass

        pretty.pprint(di)
    else:
        pretty.pprint(obj)

class Test_2Way(unittest.TestCase):

    def test_orphans(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

        #transform customers and orders into objects...
        #knock out customer #1...
        xref_remove_customer = 1
        data.customers = [
            Customer(**di) 
            for di in data.customers 
            if di["custid"] != "custid_%s" % (xref_remove_customer)]

        #and orders for customer #3
        xref_remove_order = 3
        data.orders = [
            Order(**di) 
            for di in data.orders 
            if di["custid"] != "custid_%s" % (xref_remove_order)]

        customers = data.customers
        orders = data.orders

        print("\n\ndata2:")
        ppp(data)
        if ppdb(): pdb.set_trace()

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders", attrname_on_right="customer")

            customer = lookup["custid_%d" % (size-1)]
            print("\n\ncustomer.post")
            ppp(customer) #!!! remove

            print("\ncustomer.order #1")
            ppp(customer.orders[0])

            print("type(customer):%s" % type(customer))
            print("type(customer.orders[0]):%s" % type(customer.orders[0]))

            if ppdb(): pdb.set_trace()



            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders

                if customer.xref == 3:
                    if ppdb() : pdb.set_trace()
                    ppp(customer)
                    self.assertFalse(hasattr(customer, "orders"))
                else:
                    self.assertEqual(customer.xref, len(customer.orders))

                    #xref is expected to match, that's from the way the data was constructed
                    for order in customer.orders:
                        self.assertEqual(customer.xref, order.xref)
                        self.assertEqual(customer.custid, order.customer.custid)

            for order in orders:
                if order.xref == xref_remove_customer:
                    self.assertFalse(hasattr(order, "customer"))
                else:
                    self.assertEqual(order.xref, order.customer.xref)


        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise


    def test_orphans_with_initialization(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

        #transform customers and orders into objects...
        #knock out customer #1...
        xref_remove_customer = 1
        data.customers = [
            Customer(**di) 
            for di in data.customers 
            if di["custid"] != "custid_%s" % (xref_remove_customer)]

        #and orders for customer #3
        xref_remove_order = 3
        data.orders = [
            Order(**di) 
            for di in data.orders 
            if di["custid"] != "custid_%s" % (xref_remove_order)]

        customers = data.customers
        orders = data.orders

        print("\n\ndata2:")
        ppp(data)
        if ppdb(): pdb.set_trace()

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            helper = linker.link(lookup, orders, attrname_on_left="orders", attrname_on_right="customer")

            customer = lookup["custid_%d" % (size-1)]
            print("\n\ncustomer.post")
            ppp(customer) #!!! remove

            print("\ncustomer.order #1")
            ppp(customer.orders[0])

            print("type(customer):%s" % type(customer))
            print("type(customer.orders[0]):%s" % type(customer.orders[0]))

            if ppdb(): pdb.set_trace()
            helper.initialize_lefts().initialize_rights()

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders

                if customer.xref == 3:
                    if ppdb() : pdb.set_trace()
                    ppp(customer)
                    self.assertFalse(customer.orders)
                else:
                    self.assertEqual(customer.xref, len(customer.orders))

                    #xref is expected to match, that's from the way the data was constructed
                    for order in customer.orders:
                        self.assertEqual(customer.xref, order.xref)
                        self.assertEqual(customer.custid, order.customer.custid)

            for order in orders:
                if order.xref == xref_remove_customer:
                    self.assertFalse(order.customer)
                else:
                    self.assertEqual(order.xref, order.customer.xref)


        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise


    def test_basic_objects(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

        #transform customers and orders into objects...
        data.customers = [Customer(**di) for di in data.customers]
        data.orders = [Order(**di) for di in data.orders]

        customers = data.customers
        orders = data.orders

        print("\n\ndata2:")
        ppp(data)

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders", attrname_on_right="customer")

            customer = lookup["custid_%d" % (size-1)]
            print("\n\ncustomer.post")
            ppp(customer) #!!! remove

            print("\ncustomer.order #1")
            ppp(customer.orders[0])

            print("type(customer):%s" % type(customer))
            print("type(customer.orders[0]):%s" % type(customer.orders[0]))

            if ppdb(): pdb.set_trace()



            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)
                    self.assertEqual(customer.custid, order.customer.custid)

        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise


class Test_Speed(unittest.TestCase):

    def run_it(self, size):
        data = get_sample_data(customer_pk="custid", shuffle=False, size=size, print_ = False)

        customers = data.customers
        orders = data.orders

        try:
            start = time()
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            linker.link(lookup, orders, attrname_on_left="orders", attrname_on_right="customer")
            duration = time() - start

            print("%s customers and %s orders linked in %s seconds" % (len(customers), len(orders), duration))

        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise


    def test_basic_with_dictionaries(self):
        self.run_it(1000)
        self.run_it(10000)
        self.run_it(100000)

class Test_Basic(unittest.TestCase):

    def test_very_basic(self):
        customers = [
            dict(id=1, xref=1),
            dict(id=2, xref=2),
        ]

        orders = [
            dict(custid=1, xref=1, orderid=11),
            dict(custid=1, xref=1, orderid=12),
            dict(custid=2, xref=2, orderid=21),
            dict(custid=2, xref=2, orderid=22),
        ]

        linker = Linker(key_left="id")

        lookup = linker.dict_from_list(customers)

        linker.link(lookup, orders, attrname_on_left="orders", key_right="custid")

        ppp(customers)


    def test_basic_with_dictionaries(self):
        data = get_sample_data(customer_pk="custid", shuffle=False)

        customers = data.customers
        orders = data.orders

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders")

            ppp(data) #!!! remove
            ppp(lookup["custid_%d" % (size)]) #!!! remove

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer["xref"], len(customer["orders"]))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer["orders"]:
                    self.assertEqual(customer["xref"], order["xref"])

        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise

    def test_scalar_with_dictionaries(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer")

        customers = data.customers
        orders = data.orders
        addresses = data.addresses

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders")

            linker.link(lookup, addresses, attrname_on_left="address", key_right="customer",type_on_left=Linker.TYPE_SCALAR)


            ppp(data) #!!! remove
            ppp(lookup["custid_%d" % (size-1)]) #!!! remove
            if ppdb(): pdb.set_trace()

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer["xref"], len(customer["orders"]))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer["orders"]:
                    self.assertEqual(customer["xref"], order["xref"])

                #ditto for the adress
                self.assertEqual(customer["xref"], customer["address"]["xref"])

        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise

    def test_compound_keys(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

        #transform customers and orders into objects...
        data.customers = [Customer(**di) for di in data.customers]
        data.orders = [Order(**di) for di in data.orders]

        enhance_country_data(data.customers)

        customers = data.customers
        orders = data.orders
        addresses = data.addresses

        print("\n\ndata2:")
        ppp(data)

        print("customer:")
        tcustomer = customers[size-1]
        ppp(tcustomer) #!!! remove

        repr(tcustomer)

        print("\npost")
        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders")

            linker.link(lookup, addresses, attrname_on_left="address", key_right="customer", type_on_left=Linker.TYPE_SCALAR)

            linker_country = Linker(key_left=("country","state"))
            lookup_country = linker_country.dict_from_list(customers)

            linker_country.link(lookup_country
                , SALES_TAX
                , attrname_on_left="tax"
                , type_on_left=Linker.TYPE_SCALAR)

            ppp(tcustomer) #!!! remove

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)

                #ditto for the adress
                self.assertEqual(customer.xref, customer.address["xref"])
                self.assertEqual(customer.tax.tax, di_state_tax[customer.state])

        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise


    def test_slots(self):

        try:

            class Customer(object):
                __slots__ = ("custid", "xref")

                def __init__(self, custid, xref):
                    self.custid = custid
                    self.xref = xref

            customers = [
                Customer(custid=1, xref=1),
                Customer(custid=2, xref=2),
            ]

            orders = [
                dict(custid=1, xref=1, orderid=11),
                dict(custid=1, xref=1, orderid=12),
                dict(custid=2, xref=2, orderid=21),
                dict(custid=2, xref=2, orderid=22),
            ]

            linker = Linker(key_left="custid")
            lookup = linker.dict_from_list(customers)
            try:
                helper = linker.link(lookup, orders, attrname_on_left="orders")
                print("coucou")
            except AttributeError:
                print("coucou. AttributeError")
                pass
            except Exception:
                raise
            else:
                self.fail("should have had an AttributeError")

            customers = [SlotProxy(obj) for obj in customers]

            linker = Linker(key_left="custid")
            lookup = linker.dict_from_list(customers)
            helper = linker.link(lookup, orders, attrname_on_left="orders")

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(2, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order["xref"])


        except (Exception,) as e:
            if ppdb(): pdb.set_trace()
            raise

    def test_custom_setter(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

        #transform customers and orders into objects...
        data.customers = [Customer(**di) for di in data.customers]
        data.orders = [Order(**di) for di in data.orders]

        enhance_country_data(data.customers)

        customers = data.customers
        orders = data.orders
        addresses = data.addresses

        print("\n\ndata2:")
        ppp(data)

        print("customer:")
        tcustomer = customers[size-1]
        ppp(tcustomer) #!!! remove

        repr(tcustomer)



        print("\npost")
        try:
        


            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders")

            linker.link(lookup, addresses, attrname_on_left="address", key_right="customer", type_on_left=Linker.TYPE_SCALAR)

            linker_country = Linker(key_left=("country","state"))
            lookup_country = linker_country.dict_from_list(customers)

            def setter(o_left, attrname, o_right):
                o_left.tax = o_right.tax


            linker_country.link(lookup_country
                ,SALES_TAX
                ,attrname_on_left = "tax"
                ,setter_left = setter
                )

            ppp(tcustomer) #!!! remove

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)

                #ditto for the adress
                self.assertEqual(customer.xref, customer.address["xref"])
                self.assertEqual(customer.tax, di_state_tax[customer.state])

        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise


    def test_compound_keys_aliased(self):
        try:
            data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

            #transform customers and orders into objects...
            data.customers = [Customer(**di) for di in data.customers]
            data.orders = [Order(**di) for di in data.orders]

            enhance_country_data(data.customers, attrname_state="province")


            customers = data.customers
            orders = data.orders
            addresses = data.addresses

            print("\n\ndata2:")
            ppp(data)

            print("customer:")
            tcustomer = customers[size-1]
            ppp(tcustomer) #!!! remove

            self.assertTrue(tcustomer.province)


            repr(tcustomer)

            print("\npost")
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders")

            linker.link(lookup, addresses, attrname_on_left="address", key_right="customer", type_on_left=Linker.TYPE_SCALAR)

            linker_country = Linker(key_left=("country","province"))
            lookup_country = linker_country.dict_from_list(customers)

            linker_country.link(lookup_country
                , SALES_TAX
                , attrname_on_left="tax"
                , type_on_left=Linker.TYPE_SCALAR
                , key_right = ("country","state")
                )

            # customer = lookup["custid_%d" % (size-1)]
            ppp(tcustomer) #!!! remove

            print("type(customer):%s" % type(tcustomer))
            print("type(customer.address):%s" % type(tcustomer.address))
            print("type(customer.orders[0]):%s" % type(tcustomer.orders[0]))

            # ppdb()



            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)

                #ditto for the adress
                self.assertEqual(customer.xref, customer.address["xref"])

                # pdb.set_trace()
                self.assertEqual(customer.tax.tax, di_state_tax[customer.province])



        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise




    def test_basic_objects(self):
        data = get_sample_data(customer_pk="custid", address_fk="customer", shuffle=False)

        #transform customers and orders into objects...
        data.customers = [Customer(**di) for di in data.customers]
        data.orders = [Order(**di) for di in data.orders]

        customers = data.customers
        orders = data.orders
        addresses = data.addresses

        print("\n\ndata2:")
        ppp(data)

        try:
            #create the linker and tell it what the left-hand key will be
            linker = Linker(key_left="custid")

            #make a lookup dictionary point to customers by custid
            lookup = linker.dict_from_list(customers)

            #minimal use case for Linker, one-way, right-to-left assignment
            #each customer will be updated with its orders
            linker.link(lookup, orders, attrname_on_left="orders")

            linker.link(lookup, addresses, attrname_on_left="address", key_right="customer", type_on_left=Linker.TYPE_SCALAR)

            customer = lookup["custid_%d" % (size-1)]
            ppp(customer) #!!! remove

            print("type(customer):%s" % type(customer))
            print("type(customer.address):%s" % type(customer.address))
            print("type(customer.orders[0]):%s" % type(customer.orders[0]))

            if ppdb(): pdb.set_trace()



            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)

                #ditto for the adress
                self.assertEqual(customer.xref, customer.address["xref"])



        except (Exception,) as e: #!!!
            logger.error(repr(e)[:100])
            if ppdb(): pdb.set_trace()
            raise



if __name__ == '__main__':
    #conditional debugging, but not in nosetests
    if "--pdb" in sys.argv:
        ppdb.enabled = not sys.argv[0].endswith("nosetests")
        sys.argv.remove("--pdb")

    sys.exit(unittest.main())

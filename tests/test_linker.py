# -*- coding: utf-8 -*-

"""
test_pynoorm
----------------------------------

Tests for `pynoorm.linker` module, 
"""
import pprint 
import unittest


from pynoorm.linker import Linker

import random
import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# from lib.utils import ppp
from traceback import print_exc as xp

import pdb

size = 3
orders_by_cust = 3
SHUFFLE_BY_DEFAULT = False


class DummyObject(object):
    """demos __getitem__, getattr precedence"""
    def __init__(self, **kwds):
        self.__dict__.update(**kwds)

# class DummyObjectPrint(DummyObject)

#     def __init__(self, **kwds):
#         self.__dict__.update(**kwds)

    def __repr__(self):
        res = "%s" % (self.__dict__)
        res = res.replace("{","")
        res = res.replace("}","")
        res = res.replace(":","=")
        res = res.replace("'","")

        return "[%s %s]" % (self.__class__.__name__, res)

class Customer(DummyObject): pass

class Address(DummyObject): pass

class Order(DummyObject): pass

DEFAULT_KEY = "custid"

sales_tax = [
    DummyObject(country="USA", state="OR", tax=0),
    DummyObject(country="CAD", state="BC", tax=12.5),
    DummyObject(country="USA", state="WA", tax=6.5),
]


def enhance_country_data(list_, attrname_country="country", attrname_state="state"):

    for cntr, o in enumerate(list_):

        index = cntr % (len(sales_tax))

        country = sales_tax[index].country
        state sales_tax[index].state
        if isinstance(o, dict):
            o[attrname_country] = country
            o[attrname_state] = state
        else:
            setattr(o,attrname_country, country)
            setattr(o,attrname_state, state)


def get_sample_data(customer_pk, order_fk=None, address_fk=None, shuffle=SHUFFLE_BY_DEFAULT):
    """prepare some simple customer/order data.  
       -    the _pk, _fk parameters allow you to vary the fieldnames used to link
       -    xref should always match between a customer and the order
       -    shuffle - shuffles the lists so that they are not ordered
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

        numorders = min(100, cntr+1)

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

    print("\n\ndata:") #!!!
    ppp(res)           #!!!

    return res

# from utils import ppp  #!!!
use_pdb = True         #!!!

import inspect

pretty = pprint.PrettyPrinter(indent=2)

def methi(aMethod):             #!!! remove
    print (inspect.getargspec(aMethod)) #!!! remove

def ppp(obj):
    if not isinstance(obj, (list, dict)):
        pretty.pprint(vars(obj))
    else:
        pretty.pprint(obj)




class Test_Basic(unittest.TestCase):

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

        except Exception, e: #!!!
            logger.error(repr(e)[:100])
            if use_pdb: pdb.set_trace()
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

            pdb.set_trace()

            ppp(data) #!!! remove
            ppp(lookup["custid_%d" % (size-1)]) #!!! remove
            pdb.set_trace()

            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer["xref"], len(customer["orders"]))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer["orders"]:
                    self.assertEqual(customer["xref"], order["xref"])

                #ditto for the adress
                self.assertEqual(customer["xref"], customer["address"]["xref"])

        except Exception, e: #!!!
            logger.error(repr(e)[:100])
            if use_pdb: pdb.set_trace()
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

            pdb.set_trace()



            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)

                #ditto for the adress
                self.assertEqual(customer.xref, customer.address["xref"])



        except Exception, e: #!!!
            logger.error(repr(e)[:100])
            if use_pdb: pdb.set_trace()
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

            pdb.set_trace()



            for customer in customers:
                #each customer gets as many orders a  its sequence, i.e. customer 2 gets 2 orders
                self.assertEqual(customer.xref, len(customer.orders))

                #xref is expected to match, that's from the way the data was constructed
                for order in customer.orders:
                    self.assertEqual(customer.xref, order.xref)

                #ditto for the adress
                self.assertEqual(customer.xref, customer.address["xref"])



        except Exception, e: #!!!
            logger.error(repr(e)[:100])
            if use_pdb: pdb.set_trace()
            raise



if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

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

import sys
import pdb

size = 3
orders_by_cust = 3
SHUFFLE_BY_DEFAULT = False

def ppdb(e=None):
    if ppdb.enabled and not sys.argv[0].endswith("nosetests"):
        pdb.set_trace()



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
            if use_pdb: ppdb()
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

            ppdb()

            ppp(data) #!!! remove
            ppp(lookup["custid_%d" % (size-1)]) #!!! remove
            ppdb()

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
            if use_pdb: ppdb()
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
        # ppdb()

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
                self.assertEqual(customer.tax.tax, di_state_tax[customer.state])



        except Exception, e: #!!!
            logger.error(repr(e)[:100])
            if use_pdb: ppdb(e)
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

            ppdb()



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
            if use_pdb: ppdb()
            raise



if __name__ == '__main__':
    import sys

    if "--pdb" in sys.argv:
        ppdb.enabled = True
        sys.argv.remove("--pdb")
    else:
        ppdb.enabled = False

    sys.exit(unittest.main())

# -*- coding: utf-8 -*-

"""
test_pynoorm
----------------------------------

Tests for `pynoorm` module.
"""

import unittest

from pynoorm.binder import Binder

import sqlite3

binder = conn = cursor = None

import pdb

def setup():
    global conn, cursor, binder;


    if conn:
        return

    conn = sqlite3.connect(":memory")
    cursor = conn.cursor()

    qry_create = """CREATE TABLE orders
             (custid TEXT, ordernum INTEGER, sku text, qty INTEGER)"""

    try:
        cursor.execute(qry_create)
    except Exception, e:
        pass

    binder = Binder.factory(paramstyle=sqlite3.paramstyle)



def teardown():
    global conn, cursor;

    cursor.close()
    conn.close()
    conn = cursor = None

def parse_res(cursor, li_fetched):
    li_parsed = []
    for row in li_fetched:
        di = dict()
        li_parsed.append(di)

        for ix, tuple_ in enumerate(cursor.description):
            di[tuple_[0]] = row[ix]

    return li_parsed

qty = 7

class TestPynoorm(unittest.TestCase):

    li_custid = ["ACME","AMAZON"]
    num_orders = 5

    tqry_ins = "insert into orders(custid, ordernum, sku, qty) values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"

    tqry_orders_for_customer = "select * from orders where custid = %(custid)s "

    tqry_customer_ordernum = "select * from orders where custid = %(custid)s and ordernum = %(ordernum)s"


    def setUp(self):
        setup()

    def test_000_insert(self):
        
        for custid in self.li_custid:
            self.custid = custid

            for ordernum in range(0, self.num_orders):
                di = dict(custid="badcustid")
                di["sku"] = "sku.%s.%s" % (ordernum, custid)
                di["qty"] = 42
                di.update(dict(ordernum=ordernum))

                qry, sub = binder.format(self.tqry_ins, self, di)
                cursor.execute(qry, sub)

    def test_001_select(self):
        custid = self.li_custid[0]

        self.custid = self.li_custid[1]

        qry, sub = binder.format(self.tqry_orders_for_customer, dict(custid=custid), self)
        cursor.execute(qry, sub)
        res = cursor.fetchall()

        li_dict = parse_res(cursor, res)

        self.assertEqual(len(res), self.num_orders)

        for row in li_dict:
            self.assertEqual(custid, row["custid"])
            dummy, ordernum, custid2 = row["sku"].split(".")
            ordernum = int(ordernum)
            self.assertEqual(row["custid"], custid2)
            self.assertEqual(row["ordernum"], ordernum)

    def test_002_bobbytable(self):
        custid = self.li_custid[1]
        ordernum = 6

        qry, sub = binder.format(self.tqry_ins, 
            dict(
                sku="drop table orders;",
                ordernum=ordernum,
                custid=custid,
                qty=13,
                )
        )
        cursor.execute(qry, sub)

        class Test(object):
            pass

        test_crit = Test()
        test_crit.custid = custid
        test_crit.ordernum = ordernum

        qry, sub = binder.format(self.tqry_customer_ordernum, test_crit) 
        cursor.execute(qry, sub)

        res = cursor.fetchone()

        data = parse_res(cursor, [res])[0]

        self.assertTrue("drop table" in data["sku"])
        self.assertEqual(custid, data.get("custid"))
        self.assertEqual(ordernum, data.get("ordernum"))

    def test_003_repeated(self):
        custid = self.li_custid[1]
        ordernum = 7

        tqry_ins = """insert into orders(custid, ordernum, sku, qty)
        values (%(custid)s, %(ordernum)s, %(ordernum)s, %(qty)s)"""

        qry, sub = binder.format(tqry_ins, 
            dict(
                sku="wont_find_this",
                ordernum=ordernum,
                custid=custid,
                qty=0,
                )
        )

        self.assertEqual((custid, ordernum, ordernum, 0), sub)
        self.assertTrue("values (?, ?, ?, ?)" in qry)

        cursor.execute(qry, sub)

        class Test(object):
            pass

        test_crit = Test()
        test_crit.custid = custid
        test_crit.ordernum = ordernum

        qry, sub = binder.format(self.tqry_customer_ordernum, test_crit) 

        cursor.execute(qry, sub)

        res = cursor.fetchone()

        data = parse_res(cursor, [res])[0]

        #column type should be respected
        self.assertNotEqual(data["ordernum"], data["sku"])
        self.assertEqual(data["ordernum"], int(data["sku"]))


    def test_004_item_then_attr(self):
        custid = self.li_custid[1]
        ordernum = 8

        tqry_ins = """insert into orders(custid, ordernum, sku, qty)
        values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""

        default = dict(qty=0)

        class AttrDict(object):
            def __init__(self):
                self.data = {}

            def __getitem__(self, keyname):
                return self.data[keyname]

        item_sku = "item_sku"
        attr_sku = "attr_sku"

        test = AttrDict()
        test.data["sku"] = item_sku
        test.sku = attr_sku
        test.custid = custid
        test.ordernum = ordernum

        qry, sub = binder.format(tqry_ins,
            test,
            default,
        )

        self.assertEqual((custid, ordernum, item_sku, 0), sub)

        cursor.execute(qry, sub)

        class Test(object):
            pass

        test_crit = Test()
        test_crit.custid = custid
        test_crit.ordernum = ordernum

        qry, sub = binder.format(self.tqry_customer_ordernum, test_crit) 

        cursor.execute(qry, sub)

        res = cursor.fetchone()

        data = parse_res(cursor, [res])[0]

        #column type should be respected
        self.assertEqual(data["sku"], item_sku)

    def test_005_missingbind(self):
        custid = self.li_custid[1]

        di_substit = dict(
                sku="somesku",
                qty=13,
                )
        try:
            qry, sub = binder.format(self.tqry_ins, di_substit, locals())
            self.fail("should have thrown KeyError(ordernum)")
        except KeyError, e:
            self.assertTrue("ordernum" in str(e))

    def test_006_bind_from_globals_locals(self):
        custid = self.li_custid[0]
        ordernum = 1006

        di_substit = dict(
                sku="somesku",
                )
        qry, sub = binder.format(self.tqry_ins, di_substit, locals(), globals())

        #qty is coming from the module-level global value
        self.assertTrue(7 in sub)
        self.assertTrue(ordernum in sub)



if __name__ == '__main__':
    import sys
    try:
        sys.exit(unittest.main())
    finally:
        teardown()

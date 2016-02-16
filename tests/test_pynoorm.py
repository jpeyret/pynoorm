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

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)



def parse_res(cursor, li_fetched):
    li_parsed = []
    for row in li_fetched:
        di = dict()
        li_parsed.append(di)

        for ix, tuple_ in enumerate(cursor.description):
            di[tuple_[0]] = row[ix]

    return li_parsed


#global variables
qty = 7

#supporting objects
class AttrDict(object):
    """demos __getitem__, getattr precedence"""
    def __init__(self):
        self.data = {}

    def __getitem__(self, keyname):
        return self.data[keyname]

class BasicArgument(object):
    """just used to allow attribute assignment"""
    pass



class TestBinder(object):

    table_created = False


    def __repr__(self):
        return self.__class__.__name__


    li_custid = ["ACME","AMAZON"]
    num_orders = 5

    qry_drop = """DROP TABLE orders;"""


    qry_create = """CREATE TABLE orders
                 (custid TEXT, ordernum INTEGER, sku text, qty INTEGER)"""


    tqry_ins = """insert into orders(custid, ordernum, sku, qty) 
                             values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""

    tqry_orders_for_customer = """select * 
                                  from orders 
                                  where custid = %(custid)s """

    tqry_customer_ordernum = """select * 
                                from orders 
                                where custid = %(custid)s 
                                and ordernum = %(ordernum)s"""

    conn = cursor = binder = None

    defaults = BasicArgument()
    defaults.qty = 0

    type_sub = None

    @classmethod
    def tearDownClass(cls):
       cls.conn = cls.cursor = cls.binder = None

    @classmethod
    def setUpClass(cls):
        # logger.info("%s.setUpClass()" % (cls))
        try:
            cls.binder = Binder.factory(paramstyle=cls.paramstyle)
        except AttributeError, e:
            if "paramstyle" in str(e):
                logger.error("%s needs to have a paramstyle set" % (cls))
            raise

    def tearDown(self):
        try:
            delattr(self, "custid")
        except AttributeError:
            pass

    def check_query(self, query_template, query):

        class FindBinds(object):
            def __init__(self, query_template):
                self.li_key = []
                self.query_template = query_template

                self.query_template % (self)

            def __getitem__(self, key):
                self.li_key.append(key)
                return key

        finder = FindBinds(query_template)

        if self.type_sub == tuple:
            #could run a regex to count ? or :1, :2...
            return
        elif self.type_sub == dict:

            #what is the expected format of the bind param in the query?
            t_findbind = dict(
                named=":%s",
                pyformat="%%(%s)s",
                )[self.paramstyle]

            if "%" in query_template:
                try:
                    assert finder.li_key
                except Exception, e:
                    pdb.set_trace()
                    raise

            for key in finder.li_key:
                looking_for = t_findbind % key
                msg = "'%s' not found inquery:\n  %s" % (looking_for, query)

                self.assertTrue(looking_for in query, msg)


    def test_000_insert(self):
        """
        test precedence with 3 arguments:
           1.  self - this is where custid is coming from
           2.  a per-order dict that holds order info
           3.  self.defaults, which are not actually used as 
               all bind parameters are found in the first 2 arguments    
        """


        for custid in self.li_custid:
            self.custid = custid

            for ordernum in range(0, self.num_orders):
                #custid will come from the first argument, self
                di = dict(custid="badcustid")
                di.update(dict(ordernum=ordernum))

                di["sku"] = "sku.%s.%s" % (ordernum, custid)

                #precedence over that of self.defaults
                di["qty"] = 42

                qry, sub = self.binder.format(self.tqry_ins, self, di, self.defaults)

                #check the substitions
                # values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""
                if self.type_sub == tuple:
                    exp = (self.custid, ordernum, di["sku"], di["qty"])
                    self.assertEqual(exp, sub)

                elif self.type_sub == dict:
                    exp = dict(custid=self.custid, ordernum=ordernum, sku=di["sku"], qty=di["qty"])
                    self.assertEqual(exp, sub)

                if self.cursor:
                    self.cursor.execute(qry, sub)
                else:
                    logger.info("%s execute skipped - no cursor" % (self))
                    return

    def test_001_select(self):
        """... select the data inserted in test_000_insert"""

        custid = self.li_custid[0]
        self.custid = self.li_custid[1]

        #we should expect custid to come from self.li_custid[0]
        qry, sub = self.binder.format(self.tqry_orders_for_customer, dict(custid=custid), self)

        #check the substitions
        # values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""
        if self.type_sub == tuple:
            exp = (custid,)
            self.assertEqual(exp, sub)

        elif self.type_sub == dict:
            exp = dict(custid=custid)
            self.assertEqual(exp, sub)

            self.check_query(self.tqry_orders_for_customer, qry)

        if self.cursor:
            self.cursor.execute(qry, sub)
        else:
            logger.info("%s execute skipped - no cursor" % (self))
            return


        self.cursor.execute(qry, sub)
        res = self.cursor.fetchall()

        li_dict = parse_res(self.cursor, res)

        self.assertEqual(len(res), self.num_orders)

        for row in li_dict:
            self.assertEqual(custid, row["custid"])
            dummy, ordernum, custid2 = row["sku"].split(".")
            ordernum = int(ordernum)
            self.assertEqual(row["custid"], custid2)
            self.assertEqual(row["ordernum"], ordernum)

    def test_003_repeated(self):
        """supports repeated use of the same bind parameter"""

        custid = self.li_custid[1]
        ordernum = 7

        tqry_ins = """insert into orders(custid, ordernum, sku, qty)
        values (%(custid)s, %(ordernum)s, %(ordernum)s, %(qty)s)"""

        qry, sub = self.binder.format(tqry_ins, 
            dict(
                sku="wont_find_this",
                ordernum=ordernum,
                custid=custid,
                qty=0,
                )
        )


        if self.type_sub == tuple:
            exp = (custid, ordernum, ordernum, 0)
            self.assertEqual(exp, sub)

        elif self.type_sub == dict:
            exp = dict(custid=custid, ordernum=ordernum, qty=0)
            self.assertEqual(exp, sub)


        self.check_query(tqry_ins, qry)


        if not self.cursor:
            logger.info("%s.test_003_repeated.return - no cursor")
            return

        self.cursor.execute(qry, sub)

        test_crit = BasicArgument()
        test_crit.custid = custid
        test_crit.ordernum = ordernum

        qry, sub = self.binder.format(self.tqry_customer_ordernum, test_crit) 

        self.cursor.execute(qry, sub)

        res = self.cursor.fetchone()

        data = parse_res(self.cursor, [res])[0]

        #column type should be respected
        self.assertNotEqual(data["ordernum"], data["sku"])
        self.assertEqual(data["ordernum"], int(data["sku"]))



    def test_005_missingbind(self):
        """...if a given bind parameter is not found in the entire
           argument list, throw a KeyError
        """

        custid = self.li_custid[1]

        di_substit = dict(
                sku="somesku",
                qty=13,
                )
        try:
            qry, sub = self.binder.format(self.tqry_ins, di_substit, locals())
            self.fail("should have thrown KeyError(ordernum)")
        except KeyError, e:
            self.assertTrue("ordernum" in str(e))


    def test_006_bind_from_globals_locals(self):
        """...can grab global variables.  not necessarily a good idea"""

        custid = self.li_custid[0]
        ordernum = 1006

        di_substit = dict(
                sku="somesku",
                )
        qry, sub = self.binder.format(self.tqry_ins, di_substit, locals(), globals())

        #qty is coming from the module-level global value

        if self.type_sub == tuple:
            self.assertTrue(7 in sub)
            self.assertTrue(ordernum in sub)
        elif self.type_sub == dict:
            self.assertEqual(7, sub["qty"])
            self.assertEqual(ordernum, sub["ordernum"])


    def test_007_support_nobinds(self):
        """...queries without binds are supported"""

        tqry_safe = """select * from orders where qty = 0 """

        qry, sub = self.binder.format(tqry_safe, self, locals(), globals())

        self.assertEqual(qry, tqry_safe)

    def test_008_beware_of_sqlinjection(self):
        """...you can still shoot yourself in the foot!"""

        tqry_unsafe = """select * from orders where custid = '%(custid)s' """

        custid = "x' or 'a' = 'a"

        qry_unsafe = tqry_unsafe % locals()

        qry, sub = self.binder.format(qry_unsafe, self, locals(), globals())

        self.assertTrue("""or 'a' = 'a'""" in qry)
        logger.warning(qry)



class LiveTest(object):

    @classmethod
    def tearDownClass(cls):
       cls.cursor.close()
       cls.conn.close()
       cls.conn = cls.cursor = cls.binder = None

    @staticmethod
    def setup_class(cls):

        try:
            cls.cursor.execute(cls.qry_drop)
        except cls.OperationalError:
            pass

        try:
            cls.cursor.execute(cls.qry_create)
        except Exception, e:
            logger.error("%s table creation exception %s.  cursor:%s" % (cls, e, cls.cursor))

            raise

        cls.binder = Binder.factory(paramstyle=cls.paramstyle)

    def test_002_bobbytable(self):
        custid = self.li_custid[1]
        ordernum = 6

        if not self.conn:
            # unittest.skip("no connection")
            raise unittest.SkipTest("%s.no connection" % (self))

        qry, sub = self.binder.format(self.tqry_ins, 
            dict(
                sku="drop table orders;",
                ordernum=ordernum,
                custid=custid,
                qty=13,
                )
        )
        self.cursor.execute(qry, sub)

        test_crit = BasicArgument()
        test_crit.custid = custid
        test_crit.ordernum = ordernum

        qry, sub = self.binder.format(self.tqry_customer_ordernum, test_crit) 
        self.cursor.execute(qry, sub)

        res = self.cursor.fetchone()

        data = parse_res(self.cursor, [res])[0]

        self.assertTrue("drop table" in data["sku"])
        self.assertEqual(custid, data.get("custid"))
        self.assertEqual(ordernum, data.get("ordernum"))




    def test_004_item_then_attr(self):
        """
        for each argument:
            1. try argument[<keyname>]
            2. try getattr(<keyname>)
            3. if not found, advance to next argument
            4. when argument list is done, throw a KeyError(<keyname>)
        """

        custid = self.li_custid[1]
        ordernum = 8

        if not self.conn:
            # unittest.skip("no connection")
            raise unittest.SkipTest("%s.no connection" % (self))


        tqry_ins = """insert into orders(custid, ordernum, sku, qty)
        values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""

        default = dict(qty=0)


        #set up an argument with sku both as an item and an attribute
        item_sku = "item_sku"
        attr_sku = "attr_sku"

        test = AttrDict()
        test.data["sku"] = item_sku
        test.sku = attr_sku
        test.custid = custid
        test.ordernum = ordernum

        qry, sub = self.binder.format(tqry_ins,
            test,
            default,
        )

        self.assertEqual((custid, ordernum, item_sku, 0), sub)

        self.cursor.execute(qry, sub)


        test_crit = BasicArgument()
        test_crit.custid = custid
        test_crit.ordernum = ordernum

        qry, sub = self.binder.format(self.tqry_customer_ordernum, test_crit) 

        self.cursor.execute(qry, sub)

        res = self.cursor.fetchone()

        data = parse_res(self.cursor, [res])[0]

        #column type should be respected
        self.assertEqual(data["sku"], item_sku)


class Sqlite3(LiveTest, TestBinder, unittest.TestCase):

    paramstyle = sqlite3.paramstyle

    type_sub = tuple

    @classmethod
    def setUpClass(cls):

        cls.conn = sqlite3.connect(":memory")
        cls.cursor = cls.conn.cursor()

        # pdb.set_trace()
        LiveTest.setup_class(cls)

        cls.OperationalError = sqlite3.OperationalError


class DryRunTest_Oracle(TestBinder, unittest.TestCase):
    """test Oracle handling"""

    paramstyle = "named"

    type_sub = dict


class DryRunTest_Postgresql(TestBinder, unittest.TestCase):
    """test Postgresql handling"""

    paramstyle = "pyformat"

    type_sub = dict




if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

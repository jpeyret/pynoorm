# -*- coding: utf-8 -*-

"""
test_pynoorm
----------------------------------

Tests for `pynoorm` module.
"""

import unittest

from pynoorm.binder import Binder

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def parse_res(cursor, li_fetched):
    "simplistic parser for fetched cursor data"
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


class BinderHelper(object):
    """the basic test functionality, able to work on both
       a live test (i.e. where the orders table has been created)
       and a dryrun (where the orders table is not created but
       the qry and substitions can be tested)"""

    def __repr__(self):
        return self.__class__.__name__

    li_custid = ["ACME", "AMAZON"]
    num_orders = 5

    tqry_ins = """insert into orders
                  (custid, ordernum, sku, qty)
                   values
                   (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""

    tqry_orders_for_customer = """select *
                                  from orders
                                  where custid = %(custid)s """

    tqry_customer_ordernum = """select *
                                from orders
                                where custid = %(custid)s
                                and ordernum = %(ordernum)s"""

    tqry_max_order = """select *
              from orders
              where custid = %(custid)s
              and ordernum =
                  (select max(s.ordernum)
                   from orders s
                   where custid = orders.custid)"""

    conn = cursor = binder = None

    defaults = BasicArgument()
    defaults.qty = 0
    defaults.sku = "not provided"
    defaults.ordernum = -1

    type_sub = None

    @classmethod
    def tearDownClass(cls):
        cls.conn = cls.cursor = cls.binder = None

    @classmethod
    def setUpClass(cls):
        try:
            cls.binder = Binder.factory(paramstyle=cls.paramstyle)
        except AttributeError as e:
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
                except Exception as e:
                    # pdb.set_trace()
                    raise

            for key in finder.li_key:
                looking_for = t_findbind % key
                msg = "'%s' not found inquery:\n  %s" % (looking_for, query)

                self.assertTrue(looking_for in query, msg)

    def test_000_insert(self):
        """
        ...test precedence with 3 arguments:
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

                qry, sub = self.binder.format(
                    self.tqry_ins,
                    self,
                    di,
                    self.defaults,
                    )

                #check the substitions
                # values (%(custid)s, %(ordernum)s, %(sku)s, %(qty)s)"""
                if self.type_sub == tuple:
                    exp = (self.custid, ordernum, di["sku"], di["qty"])
                    self.assertEqual(exp, sub)

                elif self.type_sub == dict:
                    exp = dict(
                        custid=self.custid,
                        ordernum=ordernum,
                        sku=di["sku"],
                        qty=di["qty"])
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
        qry, sub = self.binder.format(
            self.tqry_orders_for_customer,
            dict(custid=custid),
            self)

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
        """...supports repeated use of the same bind parameter"""
        testname = "test_003_repeated"

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
            logger.info("%s.%s.return - no cursor" % (self, testname))
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

    def test_004_item_then_attr(self):
        """...first try arg[key] then getattr(arg, key)
        for each argument:
            1. try argument[<keyname>]
            2. try getattr(argument, <keyname>)
            3. if not found, advance to next argument
            4. when argument list is done, throw a KeyError(<keyname>)
        """

        testname = "test_004_item_then_attr"

        custid = self.li_custid[1]
        ordernum = 8

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

        qry, sub = self.binder.format(
            tqry_ins,
            test,
            default,
            )

        if self.type_sub == tuple:
            exp = (custid, ordernum, item_sku, 0)
            self.assertEqual(exp, sub)

        elif self.type_sub == dict:
            exp = dict(custid=custid, ordernum=ordernum, sku=item_sku, qty=0)
            self.assertEqual(exp, sub)

        self.check_query(tqry_ins, qry)

        if not self.cursor:
            logger.info("%s.%s.return - no cursor" % (self, testname))
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
        self.assertEqual(data["sku"], item_sku)

    def test_005_missingbind(self):
        """...if a bind parameter is found nowhere, throws KeyError
        """

        custid = self.li_custid[1]

        di_substit = dict(
                sku="somesku",
                qty=13,
                )
        try:
            qry, sub = self.binder.format(self.tqry_ins, di_substit, locals())
            self.fail("should have thrown KeyError(ordernum)")
        except KeyError as e:
            self.assertTrue("ordernum" in str(e))

    def test_006_bind_from_globals_locals(self):
        """...can grab global variables.  not necessarily a good idea"""

        custid = self.li_custid[0]
        ordernum = 1006

        di_substit = dict(
                sku="somesku",
                )
        qry, sub = self.binder.format(
            self.tqry_ins,
            di_substit,
            locals(),
            globals())

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

        #and you can also not pass in any arguments
        qry, sub = self.binder.format(tqry_safe)
        self.assertEqual(qry, tqry_safe)

    def test_008_beware_of_sqlinjection(self):
        """...if you aim carefully, you can shoot yourself in the foot!"""

        tqry_unsafe = """select * from orders where custid = '%(custid)s' """

        custid = "x' or 'a' = 'a"

        #we are not using binds here, just a dumb direct substitution
        qry_unsafe = tqry_unsafe % locals()

        qry, sub = self.binder.format(qry_unsafe, self, locals(), globals())

        self.assertTrue("""or 'a' = 'a'""" in qry)
        logger.info(qry)


    def test_009_like(self):
        """...check like-based searches"""
        testname = "test_009_like"

        tqry = """select * from orders where custid like %(crit_custid)s """

        crit_custid="AC%"
        qry, parameters = self.binder.format(tqry, dict(crit_custid=crit_custid), self,)
        # self.assertEqual(qry, tqry_safe)


        if self.type_sub == tuple:
            self.assertTrue(crit_custid in parameters)
            # self.assertTrue(ordernum in parameters)
        elif self.type_sub == dict:
            self.assertEqual(crit_custid, parameters["crit_custid"])

        if not self.cursor:
            logger.info("%s.%s.return - no cursor" % (self, testname))
            return

        self.cursor.execute(qry, parameters)

        res = self.cursor.fetchone()

        data = parse_res(self.cursor, [res])[0]

        #column type should be respected
        self.assertEqual(data["custid"], "ACME")




class LiveTest(object):

    def __repr__(self):
        return self.__class__.__name__

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()
        cls.conn = cls.cursor = cls.binder = None

    @classmethod
    def setUpClass(cls, subcls):

        try:
            subcls.cursor.execute(subcls.qry_drop)
        except subcls.OperationalError:
            pass

        try:
            subcls.cursor.execute(subcls.qry_create)
        except Exception as e:
            msg = "%s table creation exception %s. cursor:%s" \
                % (subcls, e, subcls.cursor)
            logger.error(msg)
            raise

        subcls.binder = Binder.factory(paramstyle=subcls.paramstyle)

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

    def test_009_bind_from_rows(self):
        """...bind from rows & against a property
        """

        testname = "test_009_bind_from_rows"
        self.custid = self.li_custid[1]

        class PropertyIncrementer(object):
            def __init__(self, ordernum):
                assert isinstance(ordernum, int)
                self._ordernum = ordernum

            def ordernum():
                doc = "The ordernum property."

                def fget(self):
                    # raise NotImplementedError()
                    self._ordernum += 1
                    return self._ordernum
                return locals()
            ordernum = property(**ordernum())

        def fetchmax():
            #making use of the Binder.__call__ shortcut
            qry_max, sub_max = self.binder(self.tqry_max_order, self)

            self.cursor.execute(qry_max, sub_max)
            res = self.cursor.fetchone()

            row = parse_res(self.cursor, [res])[0]
            return row

        row = fetchmax()

        old_ordernum = row["ordernum"]
        incrementer = PropertyIncrementer(old_ordernum)

        before = {}
        before.update(row)
        del before["ordernum"]

        qry_ins, sub = self.binder(self.tqry_ins, incrementer, row)

        if self.type_sub == tuple:
            exp = (row["custid"], old_ordernum + 1, row["sku"], row["qty"])
            self.assertEqual(exp, sub)

        elif self.type_sub == dict:
            exp = dict(
                custid=row["custid"],
                ordernum=old_ordernum + 1,
                sku=row["sku"],
                qty=row["qty"])
            self.assertEqual(exp, sub)

        #insert the new row, fetch it
        self.cursor.execute(qry_ins, sub)
        row2 = fetchmax()

        new_ordernum = row2["ordernum"]

        after = {}
        after.update(row2)
        del after["ordernum"]

        #expecting all data copied except for ordernum incrementation
        self.assertEqual(before, after)
        self.assertEqual(old_ordernum + 1, new_ordernum)


class Sqlite3(LiveTest, BinderHelper, unittest.TestCase):
    """test sqlite3"""

    qry_drop = """DROP TABLE orders;"""

    qry_create = """CREATE TABLE orders
                 (custid TEXT, ordernum INTEGER, sku text, qty INTEGER)"""

    type_sub = tuple

    @classmethod
    def setUpClass(cls):

        try:
            import sqlite3
        except ImportError:
            return

        cls.paramstyle = sqlite3.paramstyle

        cls.conn = sqlite3.connect(":memory")
        cls.cursor = cls.conn.cursor()
        cls.OperationalError = sqlite3.OperationalError

        LiveTest.setUpClass(cls)


class DryRunTest_Oracle(BinderHelper, unittest.TestCase):
    """test Oracle handling
       currently not executing sql however, just formatting"""

    paramstyle = "named"
    type_sub = dict


class DryRunTest_Postgresql(BinderHelper, unittest.TestCase):
    """test Postgresql handling
       currently not executing sql however, just formatting"""

    paramstyle = "pyformat"
    type_sub = dict

class DryRunTest_MySQL(BinderHelper, unittest.TestCase):
    """test Postgresql handling
       currently not executing sql however, just formatting"""

    paramstyle = "format"
    type_sub = tuple


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

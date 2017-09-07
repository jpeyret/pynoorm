
The Linker Class
================

Linker cross-links collections of objects (or dictionaries) together.  You tell it which attribute names to use to join objects and it will do the rest.  A **Linker** will link objects in a *"left-side"* collection with a *"right-side"* collection.  You may also want to think of a it as *parent-child* linking.

Easier by example, let's start out with some sample data.

A list of *customers*, as *dictionaries*::

	customers = [ { 'custid': 'custid_1', 'xref': 1},
	{ 'custid': 'custid_2', 'xref': 2},
	{ 'custid': 'custid_3', 'xref': 3}]

And their *orders*. ::

	orders = [ { 'custid': 'custid_1', 'order_id': 1001, 'xref': 1},
	{ 'custid': 'custid_2', 'order_id': 2001, 'xref': 2},
	{ 'custid': 'custid_2', 'order_id': 2002, 'xref': 2},
	{ 'custid': 'custid_3', 'order_id': 3001, 'xref': 3},
	{ 'custid': 'custid_3', 'order_id': 3002, 'xref': 3},
	{ 'custid': 'custid_3', 'order_id': 3003, 'xref': 3}] 


Start out by creating a **Linker**.  You tell it that objects on the left are keyed by `custid`::

	linker = Linker(key_left="custid")

Now, create a lookup dictionary which is keyed by `customer.custid`::
	
	lookup = linker.dict_from_list(customers)

We're only linking right-to-left (i.e. an `Order` does not get a pointer to its `Customer`) and the key names match, so we don't need to repeat them.  This is the simplest **Linker** use case.  We only need to tell what to call the list of orders on each customer.::

	linker.link(lookup, orders, attrname_on_left="orders")

.. note::
	A minimal call to `Linker.link` always needs to pass in the left's prepared dictionary, and the right's list/iterator.  It also needs to specify the attribute name for the relation on the left.


Now, if we look at custid_3, i.e. `lookup["custid_3"]` or `customers[2]`, we that it has been linked to its orders.  `customer.orders` is a **list**, because that's the default for the left-side attribute type on a **Linker.link**.  Think of it as a 1-N, parent-child relationship.::

	{ 'custid': 'custid_3',
	  'orders': [ { 'custid': 'custid_3', 'order_id': 3001, 'xref': 3},
	              { 'custid': 'custid_3', 'order_id': 3002, 'xref': 3},
	              { 'custid': 'custid_3', 'order_id': 3003, 'xref': 3}],
	  'xref': 3}

OK, let's spice it up a bit.  We're also going to link each Customer to her Address, except that Addresses store their customer id under `customer`, not `custid`::

	'addresses': [ { 'customer': 'custid_1',
	                   'street': '101 1st Ave.',
	                   'xref': 1},
	                 { 'customer': 'custid_2',
	                   'street': '102 1st Ave.',
	                   'xref': 2},
	                 { 'customer': 'custid_3',
	                   'street': '103 1st Ave.',
	                   'xref': 3}],
	
We can re-use the lookup dictionary, but tell it to link based on `customer` on the right-side.  We also need to specify the receiving attribute `customer.address` and the finally, each customer only has one address, so we specify that `customer.address` will be a scalar, rather than defaulting to a **list**. ::

	linker.link(lookup, addresses, attrname_on_left="address", key_right="customer",type_on_left=Linker.TYPE_SCALAR)

Checking `custid_2` we now see the address has been added: ::

	{ 'address': { 'customer': 'custid_2', 'street': '102 1st Ave.', 'xref': 2},
	  'custid': 'custid_2',
	  'orders': [ { 'custid': 'custid_2', 'order_id': 2001, 'xref': 2},
	              { 'custid': 'custid_2', 'order_id': 2002, 'xref': 2}],
	  'xref': 2}

Objects?  Or dictionaries?
--------------------------

Now, you may have noticed we've been talking about attributes, but we've been manipulating dictionaries, not objects.  Does this work on objects too?  Yes, it does.  Let's redo the same tests, with object-based data.  Addresses will however remain dictionaries. ::

	customers = [ [Customer xref= 1, custid= custid_1],
                 [Customer xref= 2, custid= custid_2],
                 [Customer xref= 3, custid= custid_3]]

  	orders = [ [Order order_id= 1001, xref= 1, custid= custid_1],
              [Order order_id= 2001, xref= 2, custid= custid_2],
              [Order order_id= 2002, xref= 2, custid= custid_2],
              [Order order_id= 3001, xref= 3, custid= custid_3],
              [Order order_id= 3002, xref= 3, custid= custid_3],
              [Order order_id= 3003, xref= 3, custid= custid_3]]

	addresses = [ { 'custid': 'custid_1', 'street': '101 1st Ave.', 'xref': 1},
                 { 'custid': 'custid_2', 'street': '102 1st Ave.', 'xref': 2},
                 { 'custid': 'custid_3', 'street': '103 1st Ave.', 'xref': 3}]


Let's redo the work with the new data types.  Same code as before, **Linker** recognizes when it gets objects rather than dictionaries and figures it out. ::

	linker = Linker(key_left="custid")
	lookup = linker.dict_from_list(customers)
	linker.link(lookup, orders, attrname_on_left="orders")
	linker.link(lookup, addresses, attrname_on_left="address", key_right="customer", type_on_left=Linker.TYPE_SCALAR)

And the result, again for customer 2: ::

	lookup["custid_2"] = { 'address': { 'customer': 'custid_2', 'street': '102 1st Ave.', 'xref': 2},
	  'custid': 'custid_2',
	  'orders': [ [Order order_id= 2001, xref= 2, custid= custid_2],
	              [Order order_id= 2002, xref= 2, custid= custid_2]],
	  'xref': 2}

	type(customer):<class '__main__.Customer'>
	type(customer.address):<type 'dict'>
	type(customer.orders[0]):<class '__main__.Order'>

.. note::
	You can't mix objects and dictionaries within a list. For example, all customers need to be either objects or dictionaries.  Linker only looks at the first item in each list to adjust its behavior.


Advanced Usage
============

Compound keys.
--------------

We want to track sales tax, which we'll assume is determined by **country**, **state**. ::

	SALES_TAX = [[Tax country= USA, state= OR, tax= 0], 
		[Tax country= CAD, state= BC, tax= 12.5], 
		[Tax country= USA, state= WA, tax= 6.5]]

And the customers now also have that data: ::

	[Customer country= USA, state= WA, xref= 3, custid= custid_3]

First we need to create another Linker and then its lookup dictionary.  Note that we provide a tuple as
the key this time ::

	linker_country = Linker(key_left=("country","state"))
	lookup_country = linker_country.dict_from_list(customers)

Then we just call the link. ::

	linker_country.link(lookup_country
	    , SALES_TAX
	    , attrname_on_left="tax"
	    , type_on_left=Linker.TYPE_SCALAR)

This gives: ::

	{ 'address': ...,
	  'country': 'USA',
	  'custid': 'custid_3',
	  'orders': [ ...],
	  'state': 'WA',
	  'tax': [Tax country= USA, state= WA, tax= 6.5],
	  'xref': 3}

Except that I live in Canada, and we have `provinces`, not `states`.  Let's change the customer object. ::

	customer:
	{ 'country': 'USA', 'custid': 'custid_3', 'province': 'WA', 'xref': 3}

We just need to change the linker we create and then alias the call from `province` to `state`: ::

    linker_country = Linker(key_left=("country","province"))
    lookup_country = linker_country.dict_from_list(customers)

    linker_country.link(lookup_country
        , SALES_TAX
        , attrname_on_left="tax"
        , type_on_left=Linker.TYPE_SCALAR
        , key_right = ("country","state")
        )

Result: ::

	{ 'address': ...,
	  'country': 'USA',
	  'custid': 'custid_3',
	  'orders': [ ...],
	  'province': 'WA',
	  'tax': [Tax country= USA, state= WA, tax= 6.5],
	  'xref': 3}


Custom setters
--------------

What if you didn't want to set `customer.tax` to a dictionary, but just wanted the tax rate in `customer.tax`?   All you need to do is to provide your own setter.  It'll be just as fast, if not faster, because `link` won't have to dynamically create a setter function.

Going back to our basic country/state, country/state data:  ::

	linker_country = Linker(key_left=("country","state"))
	lookup_country = linker_country.dict_from_list(customers)

	def setter(o_left, attrname, o_right):
		"""this is the expected function signature.  it allows you to do whatever you want"""
	    o_left.tax = o_right.tax

	linker_country.link(lookup_country
	    ,SALES_TAX
	    ,attrname_on_left = "tax"
	    ,setter_left = setter
	    )

Result, for customer #3: ::

	{ 'address': { 'customer': 'custid_3', 'street': '103 1st Ave.', 'xref': 3},
	  'country': 'USA',
	  'custid': 'custid_3',
	  'orders': [ [Order order_id= 3001, xref= 3, custid= custid_3],
	              [Order order_id= 3002, xref= 3, custid= custid_3],
	              [Order order_id= 3003, xref= 3, custid= custid_3]],
	  'state': 'WA',
	  'tax': 6.5,
	  'xref': 3}


Two-way linking
---------------

If you are only preparing data before rendering it with a **Django Template** or a **Jinja 2**, there is no real need for linking each order to its customer.  But in other cases, you may want `order.customer`, as well as `customer.orders`.Just use **attrname_on_right** to specify the attribute name to use on the right side of the relation.  It will default to a scalar ::

	linker.link(lookup, orders, attrname_on_left="orders", attrname_on_right="customer")


Note the new `customer` field in the `order` below: ::

	customer.order #1
	{ 'custid': 'custid_2',
	  'customer': [Customer xref= 2, custid= custid_2, orders= [[Order order_id= 2001, customer= [Customer xref= 2, custid= custid_2, orders= [...]],

Orphans
-------

Linker doesn't particularly care that there is missing data, it just won't link for those objects.

Here's some modified sample data, where **customer #1 and the orders for customer #3** are missing: ::

	'customers': [ [Customer xref= 2, custid= custid_2],
	             [Customer xref= 3, custid= custid_3]],

	'orders': [ [Order order_id= 1001, xref= 1, custid= custid_1],
	          [Order order_id= 2001, xref= 2, custid= custid_2],
	          [Order order_id= 2002, xref= 2, custid= custid_2]]}

calling `link` the same was as before gives :: 

	[Customer xref= 2, custid= custid_2, orders= [[Order order_id= 2001, customer= [Customer xref= 2...]],
	[Customer xref= 3, custid= custid_3]

And looking at the orders for the missing customer 1: ::

	[Order order_id= 1001, xref= 1, custid= custid_1],
	[Order order_id= 2001, customer= [Customer xref= 2, custid= custid_2...

So, customers without matching orders won't have a `customer.orders` field and orders without a customer won't have an `order.customer` field.  This makes sense, but may cause **KeyError/AttributeError** if the rest of your code expects those attributes.  

This is where the `helper` object returned by `Linker.link`, which we've ignored so far, can help. `initialize_left` and `initialize_right()`, will add empty attribute defaults for the left and right, respectively.  You don't have to tell it to use a `list` or `None`, because it knows that from your preceding call to `link`. ::

	helper = linker.link(lookup, orders, attrname_on_left="orders", attrname_on_right="customer")
	helper.initialize_lefts()
	helper.initialize_rights()

which you could chain as ::

	helper.initialize_lefts().initialize_rights()


Customer #3 now has an empty `orders` list and orders for customer #1 have customer=None:  ::

	{ 'custid': 'custid_3', 'orders': [], 'xref': 3}
	{ 'custid': 'custid_1', 'customer': None, 'order_id': 1001, 'xref': 1}


Slots-based objects
------------------

Some database libraries, like SQL Alchemy, return objects that use `__slots__` to minimize memory usage.  Objects with slots can't accept attribute assignments for attributes that haven't been defined in advance.

This is the type of error to expect from SQLAlchemy:  ::

	AttributeError: 'RowProxy' object has no attribute 'foo'



Performance
===========

Performance isn't a feature, but it's good to keep track of it.

On an early 2011 Mac Book Pro, 2.2Ghz, 16GB RAM and 512GB SSD, the processing time scales linearly, at least up 100k customers: ::

	1000 customers and 8964 orders linked in 0.0100049972534 seconds
	10000 customers and 89964 orders linked in 0.110321998596 seconds
	100000 customers and 899964 orders linked in 1.63230895996 seconds

API
===

.. autoclass:: pynoorm.linker.Linker
	:members: __init__, dict_from_list, link

.. autoclass:: pynoorm.linker.LinkResultHelper
	:members: __init__, initialize_rights, initialize_lefts



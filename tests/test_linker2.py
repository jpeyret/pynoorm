import test_linker
import pynoorm

from pynoorm.linker import Linker, LinkResultHelper
from six import string_types


class Linker2(Linker):


    def preppedlink(self, left, right, attrname_on_left
        ,setter_left
        ,key_left
        ,key_right
        ,setter_right
        ,attrname_on_right
        ,get_key
        ):
        """this is similar to the link, but has all the getters/setters pre-discovered
           and knows that it won't be setting anything on the right side.
           however the signature is the same as `preppedlink2way`, to unify and simplify
           calling
        """


        helper = self.helper


        for o_right in right:

            keyval = get_key(o_right)

            o_left = left.get(keyval, None)
            if o_left is None:
                helper.add_right_orphan(o_right)
                continue

            setter_left(o_left, attrname_on_left, o_right)


    def preppedlink2way(self, left, right, attrname_on_left
        ,setter_left
        ,key_left
        ,key_right
        ,setter_right
        ,attrname_on_right
        ,get_key
        ):
        """this is similar to the link, but has all the getters/setters pre-discovered
           and knows that it won't be setting anything on the right side.
           this method knows it has to set the right too
        """

        helper = self.helper

        for o_right in right:

            keyval = get_key(o_right)

            o_left = left.get(keyval, None)
            if o_left is None:
                helper.add_right_orphan(o_right)
                continue

            setter_left(o_left, attrname_on_left, o_right)
            setter_right(o_right, attrname_on_right, o_left)


    def link(self, left, right, attrname_on_left
        ,setter_left=None
        ,type_on_left=list
        ,dictkey_attrname_left=None
        ,key_right=None
        ,setter_right=None
        ,attrname_on_right=None
        ,type_on_right=None
        ):
        """
        :param left: a dictionary of objects or dictionaries which will be linked to right-side objects
        :param right: a list(iterator?) of objects or dictionaries.  you can also pass in a dictionary, its values will be used in that case
        :param attrname_on_left: the attribute name (or dictionary key) where the right-side object ref will be stored
        :param setter_left:  you can pass a callback to assign the right-side to left-side yourself.
                             call signature:  f(o_target, attrname, o_link)
        :param type_on_left:  None/Linker.scalar - direct assignment o_left.attrname_on_left = o_right
                              list (the default) - append each right-side object
                              dict - references are stored in a dict, but that requires dictkey_attrname_left to have been set as well.
                              
        :param dictkey_attrname_left: if your target's attribute is a dictonary, you need to provide the field that will be used on for that key
                                      ex:  attrname_on_left="tags", type_on_left=dict, dictkey_attrname_left="tagtype"
        :param key_right: specifying something here allows you to alias fields used in key_left
        :param setter_right: see setter_left
        :param attrname_on_right:  passing a value means a 2-way link
        :param type_on_right:  scalar is assumed, but list is also supported

        :return: LinkResultHelper instance to check orphans/assist initializations when needed

        """

        try:

            print "%sLinker2.link%s" % ("*"*80 + "\n", "\n"+ "*"*80)

            self.helper = LinkResultHelper(**locals())

            try:
                assert isinstance(attrname_on_left, string_types)
            except (AssertionError,) as e:  #pragma: no cover
                raise TypeError("attrname_on_left needs to be a valid python variable name")

            key_left = self.key_left
            key_right = key_right or key_left

            #grab some sample objects from left and right
            if not hasattr(right, "next"):
                right = iter(right)

            sample_right = right.next()
            sample_left = left.values()[0]

            #and use the samples to figure out getters and setters
            get_key = self._get_getter(sample_right, key_right)
            setter_left = setter_left or self._get_setter(sample_left, attrname_on_left, type_on_left, dictkey_attrname_left, sample_right)

            if attrname_on_right:
                setter_right = setter_right or self._get_setter(sample_right, attrname_on_right, type_on_right)
            else:
                setter_right = None

            #do we need to set left-only? or left and right?
            if setter_right:
                prepped = self.preppedlink2way
            else:
                prepped = self.preppedlink

            #finally, call the actual link, on the sample, then the rest
            for right_ in [[sample_right],right]:

                prepped(left=left, right=right_
                    ,attrname_on_left=attrname_on_left
                    ,setter_left=setter_left
                    ,key_left=key_left
                    ,key_right=key_right
                    ,setter_right=setter_right
                    ,attrname_on_right=attrname_on_right
                    ,get_key=get_key)

        except (Exception,) as e:    #pragma: no cover
            if cpdb(): pdb.set_trace()
            raise
        else:
            return self.helper




test_linker.Linker = Linker2

from test_linker import *

if __name__ == '__main__':
    #conditional debugging, but not in nosetests
    if "--pdb" in sys.argv:
        cpdb.enabled = not sys.argv[0].endswith("nosetests")
        sys.argv.remove("--pdb")

    sys.exit(unittest.main())
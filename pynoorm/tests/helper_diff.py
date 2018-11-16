import difflib
import json
from six import string_types as basestring


def format_dict(dict_):
    return json.dumps(dict_, sort_keys=True, indent=4)


class Differ(object):
    def __init__(self):
        self._differ = difflib.Differ()

    def get_diff(self, exp, got, testee="", legend=True):
        if isinstance(exp, basestring) and isinstance(got, basestring):
            return self._get_diff(exp, got, testee, legend)

        elif isinstance(exp, dict) and isinstance(got, dict):

            exp2 = format_dict(exp)
            got2 = format_dict(got)
            return self._get_diff(exp2, got2, testee, legend)

        elif isinstance(exp, list) and isinstance(got, list):

            exp2 = "\n".join([str(val) for val in exp])
            got2 = "\n".join([str(val) for val in got])

            return self._get_diff(exp2, got2, testee, legend)

        raise NotImplementedError()

    def _get_diff(self, exp, got, legend=True, testee=""):
        if not (isinstance(exp, basestring) and isinstance(got, basestring)):
            raise ValueError("exp and got must both be strings")
        try:
            exp_ = exp.splitlines()
            got_ = got.splitlines()

            if legend:

                if testee:
                    testee = "%s:" % (testee)

                _legend = ["(%s - exp, + got)\n" % (testee)]
            else:
                _legend = []

            lines = self._differ.compare(exp_, got_)
            lines2 = list(lines)
            msg = "\n".join(_legend + lines2)
            return msg
        except (Exception,) as e:
            raise


differ = Differ()

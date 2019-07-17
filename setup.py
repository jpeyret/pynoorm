#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import re


if sys.version_info < (2, 7):
    raise Exception("PyNoORM requires Python 2.7 or higher.")

if sys.version_info >= (3,):
    if sys.version_info < (3, 3):
        raise Exception("PyNoORM requires Python 3.3 or higher")


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


# with open('README.rst') as readme_file:
#     readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]


def parse_readme(text):
    """start on reStructuredText banner and end at software declaration"""

    start = re.compile("~~~~~~~", re.IGNORECASE)
    end = re.compile("Free software:", re.IGNORECASE)
    from_ = to_ = description = None

    lines = text.split("\n")

    for lineno, line in enumerate(lines):

        if from_ is None and start.search(line):
            from_ = lineno - 1
            description = lines[from_].strip()

        if to_ is None and end.search(line):
            to_ = lineno

    return description, "\n".join(lines[from_:to_])


with open(os.path.join(os.path.dirname(__file__), "README.rst")) as r_file:
    description, readme = parse_readme(r_file.read())

    assert description.strip()
    assert readme.strip()


setup(
    name="pynoorm",
    version="1.0.1",
    description=description,
    long_description=readme + "\n\n" + history,
    author="JL Peyret",
    author_email="jpeyret@gmail.com",
    url="https://github.com/jpeyret/pynoorm",
    packages=["pynoorm"],
    package_dir={"pynoorm": "pynoorm"},
    include_package_data=True,
    install_requires=requirements,
    license="MIT License",
    zip_safe=False,
    keywords="sql database multiplatform",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Database :: Front-Ends",
        "Topic :: Utilities",
        "Operating System :: OS Independent",
    ],
    test_suite="tests",
    tests_require=test_requirements,
)

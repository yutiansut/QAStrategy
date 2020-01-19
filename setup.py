
# coding=utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2017 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import codecs
import io
import os
import re
import sys
import webbrowser
import platform
import configparser
try:
    from setuptools import setup
except:
    from distutils.core import setup
"""
"""

if sys.version_info.major != 3 or sys.version_info.minor not in [4, 5, 6, 7, 8]:
    print('wrong version, should be 3.4/3.5/3.6/3.7/3.8 version')
    sys.exit()

with io.open('QAStrategy/__init__.py', 'rt', encoding='utf8') as f:
    context = f.read()
    VERSION = re.search(r'__version__ = \'(.*?)\'', context).group(1)
    AUTHOR = re.search(r'__author__ = \'(.*?)\'', context).group(1)


def read(fname):

    return codecs.open(os.path.join(os.path.dirname(__file__), fname)).read()


NAME = "QAStrategy"
"""
"""
PACKAGES = ["QAStrategy"]
"""
"""

DESCRIPTION = "QUANTAXIS:Quantitative Financial Strategy Framework"


"""
"""

KEYWORDS = ["quantaxis", "quant", "finance", "Backtest", 'Framework']
"""
"""

AUTHOR_EMAIL = "yutiansut@qq.com"

URL = "https://github.com/yutiansut/QAStrategy"


LICENSE = "MIT"


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description='QAStrategyBase',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    install_requires=['quantaxis', 'qaenv', 'qifiaccount','quantaxis_pubsub'],
    entry_points={
    },
    # install_requires=requirements,
    keywords=KEYWORDS,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license=LICENSE,
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=True
)

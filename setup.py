# -*- coding: utf-8 -*-
"""Setup file for the DebTools project.
"""
from __future__ import unicode_literals

import codecs
import os.path
import re

from setuptools import setup, find_packages
requirements = ['stdeb>=0.8.5', 'pip', ]

try:
    import lzma
except ImportError:
    lzma = None
    requirements.append('backports.lzma')


# avoid a from debtools import __version__ as version (that compiles debtools.__init__
# and is not compatible with bdist_deb)
version = None
for line in codecs.open(os.path.join('debtools', '__init__.py'), 'r', encoding='utf-8'):
    matcher = re.match(r"""^__version__\s*=\s*['"](.*)['"]\s*$""", line)
    version = version or matcher and matcher.group(1)

# get README content from README.md file
with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as fd:
    long_description = fd.read()

entry_points = {'console_scripts': ['deb-dep-tree = debtools.debdeptree:main',
                                    'multideb = debtools.multideb:main',
                                    'aptenv = debtools.aptenv:main', ]}

setup(
    name='debtools',
    version=version,
    description='Utilities for creating mutliple Debian packages.',
    long_description=long_description,
    author='Matthieu Gallet',
    author_email='gallet.matthieu@19pouces.net',
    license='CeCILL-B',
    url='https://github.com/d9pouces/DebTools',
    entry_points=entry_points,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='debtools.tests',
    install_requires=requirements,
    setup_requires=[],
    classifiers=[],
)

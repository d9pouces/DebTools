# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase
import pkg_resources
from debtools.utils import get_control_data

__author__ = 'Matthieu Gallet'


class TestGetControlData(TestCase):

    @property
    def filename(self):
        return pkg_resources.resource_filename('debtools.tests', 'python-debtools_0.3-1_all.deb')

    def test_get_control_data(self):
        data = (get_control_data(self.filename))
        self.assertEqual(
            {
                'Maintainer': 'Matthieu Gallet <gallet.matthieu@19pouces.net>',
                'Description': 'Utilities for creating mutliple Debian packages.\nDebTools\n========',
                'Package': 'python-debtools',
                'Section': 'python',
                'Depends': 'python (>= 2.7), python (<< 2.8), python-stdeb, python-backports.lzma',
                'Priority': 'optional',
                'Source': 'debtools',
                'Installed-Size': '88',
                'Version': '0.3-1',
                'Architecture': 'all'
            },
            data
        )

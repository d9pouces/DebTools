# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import argparse
import codecs

import sys

import re
from distutils.version import LooseVersion

from pip import get_installed_distributions
# noinspection PyProtectedMember
from pip._vendor import requests
# noinspection PyProtectedMember
from pip._vendor.pkg_resources import Distribution
from pip.download import PipSession
from pip.req import parse_requirements
from pip.req.req_install import InstallRequirement
from stdeb.util import debianize_name

__author__ = 'Matthieu Gallet'

ubuntu_distribs = {'precise', 'precise-updates', 'trusty', 'trusty-updates', 'wily', 'wily-updates', 'xenial',
                   'xenial-updates', 'yakkety'}
debian_distribs = {'wheezy', 'wheezy-backports', 'jessie', 'jessie-backports', 'stretch', 'sid'}
default_map = {'ansible': 'ansible', 'Fabric': 'fabric', 'PyYAML': 'python-yaml',
               'ipython': 'ipython', 'pybtex': 'pybtex', 'pylint': 'pylint',
               'pytz': 'python-tz', }


class EnvironmentBuilder(object):
    def __init__(self, base_urls, python_version='3', package_mapping=None, required_packages=None):
        self.base_urls = base_urls
        self.python_version = python_version
        self.package_mapping = package_mapping or {}
        self.required_packages = required_packages or []

    def get_debian_package(self, python_package):
        if python_package in self.package_mapping:
            return self.package_mapping[python_package]
        debian_name = debianize_name(python_package)
        if debian_name.startswith('python-'):
            debian_name = debian_name.partition('-')[2]
        if self.python_version == '3':
            return 'python3-' + debian_name
        return 'python-' + debian_name

    def get_available_package_version_in_url(self, base_url, python_package):
        debian_package = self.get_debian_package(python_package)
        url = base_url + debian_package
        r = requests.get(url)
        if r.status_code != 200:
            return None
        content = r.text
        start_pos = content.find('<h1>')
        end_pos = content.find('</h1>')
        if 0 < start_pos < end_pos:
            title = content[start_pos + 4:end_pos].strip()
        else:
            return None
        title = title.replace(' ', ' ').partition(' [')[0]
        matcher = re.match(r'^\w+\s*:[^(]*\((\d:|)(.*)-.*\).*$', title)
        if not matcher:
            return None
        version_info = matcher.groups()[1].partition('+')[0]
        return version_info

    def get_best_available_package_version(self, python_package, descending=True):
        versions = [self.get_available_package_version_in_url(base_url, python_package) for base_url in self.base_urls]
        loose_versions = [LooseVersion(x) for x in versions if x]
        loose_versions.sort(reverse=descending)
        if not loose_versions:
            return None
        return loose_versions[0]

    def print_requirements(self):
        for python_package in self.required_packages:
            if python_package in self.package_mapping and not self.package_mapping[python_package]:
                continue
            version = self.get_best_available_package_version(python_package)
            if not version:
                sys.stderr.write('Unable to find any version for %s\n' % python_package)
            else:
                print('%s==%s' % (python_package, version))


def main():
    parser = argparse.ArgumentParser(description='Build a Python virtual env using the versions also available as '
                                                 'official Debian or Ubuntu packages')
    parser.add_argument('-u', '--URL',
                        help='"wheezy", "xenial-update", other distrib name or any URL '
                             'like https://packages.debian.org/stretch/',
                        default=[], action='append')
    parser.add_argument('-M', '--defaultmap', help='Use name mapping for well-known packages', action='store_true',
                        default=False)

    parser.add_argument('-m', '--mapfile',
                        help='mapping file between Python package names and Debian ones:'
                             ' each line is like "python-package-name=debian-package-name".'
                             'Otherwise, use the default Debianized name ("python[3]-package-name"). '
                             'Add"python-package-name=" to ignore this package',
                        default=None)
    parser.add_argument('-p', '--python', help='Python version: "2" or "3" (default: "%s")' % sys.version_info[0],
                        default=str(sys.version_info[0]))
    parser.add_argument('-r', '--requirements', help='Requirements file (otherwise use "pip list")',
                        default=None)
    args = parser.parse_args()
    base_urls = []
    for url in args.URL:
        if url in ubuntu_distribs:
            base_urls.append('http://packages.ubuntu.com/%s/' % url)
        elif url in debian_distribs:
            base_urls.append('https://packages.debian.org/%s/' % url)
        elif url.startswith('http'):
            base_urls.append(url)
        else:
            print('Invalid URL: %s' % url)
            print('Known default values: %s, %s' % (', '.join(ubuntu_distribs), ', '.join(debian_distribs)))

    package_mapping = {}
    if args.defaultmap:
        package_mapping.update(default_map)
    if args.mapfile:
        with codecs.open(args.mapfile, 'r', encoding='utf-8') as fd:
            for line in fd:
                python_name, sep, debian_name = line.partition('=')
                if sep != '=':
                    continue
                python_name = python_name.strip()
                if not python_name.startswith('#'):
                    package_mapping[python_name] = debian_name.strip()
    required_packages = []
    if args.requirements is None:
        for r in get_installed_distributions():
            assert isinstance(r, Distribution)
            required_packages.append(r.project_name)

    else:
        for r in parse_requirements(args.requirements, session=PipSession()):
            assert isinstance(r, InstallRequirement)
            required_packages.append(r.name)
    builder = EnvironmentBuilder(base_urls, python_version=args.python, package_mapping=package_mapping,
                                 required_packages=required_packages)
    builder.print_requirements()

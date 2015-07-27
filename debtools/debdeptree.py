# -*- coding: utf-8 -*-
"""Calculate the complete dependencies tree

"""
from __future__ import unicode_literals, print_function

import argparse
import codecs
import os
import subprocess
from debtools.utils import get_control_data, parse_deps, parse_dpkg, check_version_constraint

__author__ = 'Matthieu Gallet'


class DepTree(object):
    def __init__(self, recursive=False, installed_packages=None):
        self.dependencies_by_package = {}
        self.recursive = recursive
        self.installed_packages = installed_packages or {}

    def add(self, file_or_package_name):
        if file_or_package_name in self.dependencies_by_package:
            return
        if not file_or_package_name.endswith('.deb'):
            previous_content = set(os.listdir('.'))
            subprocess.check_call(['apt-get', 'download', file_or_package_name])
            new_content = set(os.listdir('.'))
            diff = [x for x in (new_content - previous_content) if x.endswith('.deb')]
            if not diff:
                raise ValueError('Unable to download %s' % file_or_package_name)
            elif len(diff) > 1:
                raise ValueError('Unable to find %s in %s' % (file_or_package_name, diff))
            file_or_package_name = diff[0]
        control_data = get_control_data(file_or_package_name)
        package_name = control_data['Package']
        package_depends = control_data['Depends']
        self.dependencies_by_package[package_name] = parse_deps(package_depends)
        if self.recursive:
            for other_package_name, version_constraints in self.dependencies_by_package[package_name].items():
                is_installed = False
                if other_package_name in self.installed_packages:
                    installed_version = self.installed_packages[other_package_name]
                    is_installed = True
                    for version_constraint in version_constraints:
                        if not check_version_constraint(installed_version, version_constraint[0], version_constraint[1]):
                            is_installed = False
                if not is_installed:
                    self.add(other_package_name)


def main():
    """Main function, intended for use as command line executable.

    Args:
        None
    Returns:
      * :class:`int`: 0 in case of success, != 0 if something went wrong

    """
    parser = argparse.ArgumentParser(description='Sample command line interface')
    parser.add_argument('--dir', default='.', help='Download directory')
    parser.add_argument('package', action='append', default=[], help='Filename (must ends by .deb) or package name to analyze')
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help='Recursive download')
    parser.add_argument('-i', '--installed', default=None, help='file with the result of `dpkg -l`')
    args = parser.parse_args()
    os.chdir(args.dir)
    if args.installed:
        with codecs.open(args.installed, 'r', encoding='utf-8') as fd:
            dpkg_content = fd.read()
        installed_packages = parse_dpkg(dpkg_content)
    else:
        installed_packages = {}
    if not args.package:
        print('Please provide a package name')
        return 1
    dep_tree = DepTree(recursive=args.recursive, installed_packages=installed_packages)
    for file_or_package_name in args.package:
        dep_tree.add(file_or_package_name)
    for package_name, dependencies in dep_tree.dependencies_by_package.items():
        print(package_name)
        print('=' % len(package_name))
        print('')
        for other_package, constraints in dependencies.items():
            constraint_str = ''
            if constraints:
                constraint_str = ', ' .join(['%s %s' % x for x in constraints])
                constraint_str = '(%s)' % constraint_str
            print('  * %s %s' % (other_package, constraint_str))
    return 0

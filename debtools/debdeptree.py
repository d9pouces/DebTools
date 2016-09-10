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
    def __init__(self, recursive=False, ignored_packages=None, local_packages=None):
        self.dependencies_by_package = {}
        self.recursive = recursive
        self.ignored_packages = ignored_packages or {}
        self.local_packages = local_packages

    @staticmethod
    def find_package(package_name):
        """ Tries to find the .deb in the working dir
        :param package_name:
        :type package_name:
        :return:
        :rtype:
        """
        present_files = [x for x in os.listdir('.')
                         if x.startswith(package_name + '_') and os.path.isfile(x) and x.endswith('.deb')]
        if len(present_files) == 1:
            return present_files[0]
        return None

    def add(self, file_or_package_name):
        if file_or_package_name in self.dependencies_by_package:
            return
        if not file_or_package_name.endswith('.deb'):
            proposed_filename = self.find_package(file_or_package_name)
            if proposed_filename:
                file_or_package_name = proposed_filename
            else:
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
        deps = {}
        for key in ('Depends', 'Pre-Depends'):
            if key in control_data:
                deps.update(parse_deps(control_data[key], local_packages=self.local_packages))
        self.dependencies_by_package[package_name] = deps
        if not self.recursive:
            return
        for other_package_name, version_constraints in self.dependencies_by_package[package_name].items():
            is_ignored = False
            if other_package_name in self.ignored_packages:
                ignored_version = self.ignored_packages[other_package_name]
                is_ignored = True
                for version_constraint in version_constraints:
                    if not check_version_constraint(ignored_version, version_constraint[0], version_constraint[1]):
                        is_ignored = False
            if not is_ignored:
                self.add(other_package_name)


def main():
    """Main function, intended for use as command line executable.
    Returns:
      * :class:`int`: 0 in case of success, != 0 if something went wrong

    """
    parser = argparse.ArgumentParser(description='Display all dependencies')
    parser.add_argument('--dir', default='.', help='Download directory')
    parser.add_argument('package', nargs='+', default=None,
                        help='Filename (must ends by .deb) or package name to analyze')
    parser.add_argument('-r', '--recursive', action='store_true', default=False, help='Recursive download')
    parser.add_argument('-i', '--ignored', default=None, help='file with the result of `dpkg -l`')
    parser.add_argument('-l', '--local', default=False, action='store_true',
                        help='use locally installed packages for solving dependencies with choices')
    args = parser.parse_args()
    os.chdir(args.dir)
    if not args.package:
        print('Please provide a package name')
        return 1

    if args.ignored:
        with codecs.open(args.ignored, 'r', encoding='utf-8') as fd:
            dpkg_content = fd.read()
        ignored_packages = parse_dpkg(dpkg_content)
    else:
        ignored_packages = {}

    local_packages = None
    if args.local:
        dpkg_output = subprocess.check_output(['dpkg', '-l'])
        local_packages = parse_dpkg(dpkg_output.decode('utf-8'))

    dep_tree = DepTree(recursive=args.recursive, ignored_packages=ignored_packages, local_packages=local_packages)
    for file_or_package_name in args.package:
        dep_tree.add(file_or_package_name)
    package_names = list(dep_tree.dependencies_by_package.keys())
    package_names.sort()
    for package_name in package_names:
        dependencies = dep_tree.dependencies_by_package[package_name]
        print(package_name)
        print('=' * len(package_name))
        print('')
        for other_package, constraints in dependencies.items():
            constraint_str = ''
            if constraints:
                constraint_str = ', ' .join(['%s %s' % x for x in constraints])
                constraint_str = '(%s)' % constraint_str
            print('  * %s %s' % (other_package, constraint_str))
        print('')
    return 0

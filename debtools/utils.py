# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from distutils.version import LooseVersion
import io
import re
import tarfile

try:
    import lzma
except ImportError:
    from backports import lzma

from debtools.ar import ArFile

__author__ = 'Matthieu Gallet'


def parse_control_data(control_data, continue_line=' ', split=': ', skip_after_blank=False):
    """ Parse a debian control file

    :param control_data:
    :type control_data: :class:`str`
    :param continue_line:
    :type continue_line: :class:`str`
    :param split:
    :type split: :class:`str`
    :param skip_after_blank:
    :type skip_after_blank: :class:`bool`
    :return:
    :rtype: :class:`dict`
    """
    offset = len(continue_line)
    result_data = {}
    key, value = None, None
    description = ''
    add_to_description = False
    for line in control_data.splitlines():
        if not line.split() and skip_after_blank:
            add_to_description = True
        if add_to_description:
            description += "\n"
            description += line
            continue
        if not line or line[0:offset] == continue_line:
            if key is not None:
                value += "\n"
                value += line[offset:]
        else:
            if key is not None:
                result_data[key] = value
            key, value = line.split(split, 1)
            value = value.lstrip()
    if key is not None:
        result_data[key] = value
    if add_to_description:
        result_data['description'] = description
    return result_data


def parse_deps(dep_string, local_packages=None):
    """Parse the dependencies of a `.deb` package and return a dict, whose keys are packages names and values are a list of version constraints

     >>> parse_deps("python (>= 2.7), python (<< 2.8), python-stdeb, python-backports.lzma")
     {u'python': [(u'>=', LooseVersion ('2.7')), (u'<<', LooseVersion ('2.8'))], u'python-stdeb': [], u'python-backports.lzma': []}

    Choices between two packages are ignored.

    :param dep_string:
    :type dep_string: :class:`str`
    :param local_packages: dict of [package_name, package_version], used when there is a choice between packages
    :type local_packages: :class:`dict`
    :return: dict, whose keys are packages names and values are a list of version constraints
    :rtype: :class:`dict`
    """
    deps = {}
    for dep_info in dep_string.split(','):
        dep_info = dep_info.strip()
        if '|' in dep_info and local_packages is None:
            continue
        elif '|' in dep_info:
            for sub_dep_info in dep_info.split('|'):
                sub_dep_info, __, __ = sub_dep_info.partition('(')
                if sub_dep_info.strip() in local_packages:
                    dep_info = sub_dep_info.strip()
                    break
            else:
                continue
        matcher = re.match('^(.*)\s+\((>=|<<|>>|==|>=|=)\s+(.*)\)$', dep_info)
        if matcher:
            package_name = matcher.group(1)
            constraint_type = matcher.group(2)
            contraint_value = matcher.group(3)
            deps.setdefault(package_name, []).append((constraint_type, LooseVersion(contraint_value)))
        else:
            deps.setdefault(dep_info, [])
    return deps


def parse_dpkg(dpkg_string):
    """
    >>> parse_dpkg("ii  xfonts-utils     1:7.7~1   amd64  X Window System font utility programs")
    {u'xfonts-utils': LooseVersion ('1:7.7~1')}

    :param dpkg_string:
    :type dpkg_string: :class:`str`
    :return: dict of [package_name, package_version]
    :rtype: :class:`dict`
    """
    installed_packages = {}
    for line in dpkg_string.splitlines():
        matcher = re.match('^ii\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+.*$', line)
        if not matcher:
            continue

        package_name, __, __ = matcher.group(1).partition(':')
        package_version = matcher.group(2)
        installed_packages[package_name] = LooseVersion(package_version)
    return installed_packages


def check_version_constraint(version_1, op, version_2):
    """
    :param version_1:
    :type version_1: :class:`distutils.version.LooseVersion`
    :param op:
    :type op: :class:`str`
    :param version_2:
    :type version_2: :class:`distutils.version.LooseVersion`
    :return:
    :rtype:
    """
    if op == '<=':
        return version_1 <= version_2
    elif op == '>=':
        return version_1 >= version_2
    elif op == '<<' or op == '<':
        return version_1 < version_2
    elif op == '>>' or op == '>':
        return version_1 > version_2
    elif op == '==' or op == '=':
        return version_1 == version_2
    elif op == '!=' or op == '<>':
        return version_1 != version_2
    raise ValueError('unknown operator %s %s %s' % (version_1, op, version_2))


def get_subfile(ar_file, name_regexp='control.tar.'):
    """Find the file whose names matches the given regexp
    :param ar_file:
    :type ar_file: :class:`ArFile`
    :param name_regexp:
    :type name_regexp: :class:`str`
    :return: the tuple (file descriptor, name)
    :rtype: :class:`tuple`
    """
    for name in ar_file.getnames():
        if re.match(name_regexp, name):
            return ar_file.extractfile(name), name
    return None, None


def get_control_data(filename):
    """ Extract control data from a `.deb` file
    A `.deb` is an `.ar` file that contains `control.tar.XXX`, that contains a `control` file.

    :param filename: complete filepath of a `.deb` file
    :type filename: :class:`str`
    :return:
    :rtype: :class:`dict`
    """
    # open the four files (.deb, .ar, control.tar.XXX, control)
    deb_file = open(filename, mode='rb')
    ar_file = ArFile(filename, mode='r', fileobj=deb_file)
    control_file, control_file_name = get_subfile(ar_file, '^control\.tar\..*$')
    mode = 'r:*'
    if control_file_name.endswith('.xz') or control_file_name.endswith('.lzma'):
        # special case when lzma is used from backport (Python 3.2, 2.7)
        control_file_content = control_file.read()
        control_file_content_uncompressed = lzma.decompress(control_file_content)
        control_file.close()
        control_file = io.BytesIO(control_file_content_uncompressed)
        mode = 'r'
    tar_file = tarfile.open(name='control', mode=mode, fileobj=control_file)
    control_data = tar_file.extractfile('./control')
    # we got the data!
    control_data_value = control_data.read().decode('utf-8')
    # ok, we close the previous file descriptors
    control_data.close()
    tar_file.close()
    ar_file.close()
    deb_file.close()
    # here we are
    parsed_data = parse_control_data(control_data_value)
    return parsed_data

# -*- coding: utf-8 -*-
"""Generate Debian packages for all installed packages

python multideb.py

You should use a `stdeb.cfg` configuration file
"""
from __future__ import unicode_literals, print_function
import argparse
import codecs
import glob
from importlib import import_module
import os
import shutil
import subprocess
from tempfile import mkdtemp

# noinspection PyPackageRequirements
from pip import get_installed_distributions
# noinspection PyPackageRequirements,PyProtectedMember
from pip._vendor.pkg_resources import Distribution
# noinspection PyPackageRequirements
from stdeb.downloader import get_source_tarball
# noinspection PyPackageRequirements
from stdeb.util import check_call, expand_sdist_file
import sys

try:
    import configparser
except ImportError:
    # noinspection PyUnresolvedReferences,PyPep8Naming
    import ConfigParser as configparser

__author__ = 'Matthieu Gallet'


def normalize_package_name(name):
    return name.lower().replace('_', '-').strip()


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    module_path, sep, class_name = dotted_path.rpartition('.')
    if sep != '.':
        raise ImportError("%s doesn't look like a module path" % dotted_path)
    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (module_path, class_name))


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--config', '-f', action='store', help='Base configuration file', default='stdeb.cfg')
    args_parser.add_argument('--freeze', '-r', action='store_true', help='add packages listed in `pip freeze`', default=False)
    args_parser.add_argument('--only', action='append', help='only these packages', default=[])
    args_parser.add_argument('--allow-unsafe-download', action='store_true', help='Allow unsafe downloads', default=False)
    args_parser.add_argument('--dest-dir', help='Destination dir', default='deb')
    args_parser.add_argument('-x', '--extra-cfg-file', default=[], action='append', help='Extra configuration file')
    args_parser.add_argument('--verbose', '-v', help='verbose mode', default=False, action='store_true')
    args_parser.add_argument('--keep-temp', '-k', help='keep temporary files', default=False, action='store_true')
    args_parser.add_argument('--dry', help='show what should be done', default=False, action='store_true')
    args_parser.add_argument('--exclude', default=[], action='append', help='modules to exclude from packaging')
    args_parser.add_argument('--include', default=[], action='append', help='other modules to package')

    args = args_parser.parse_args()
    dry = args.dry
    config_parser = configparser.ConfigParser()
    all_config_files = args.extra_cfg_file + [args.config]
    for filename in all_config_files:
        if os.path.isfile(filename):
            print('config. file %s added to configuration' % filename)
        else:
            print('config. file %s does not exist' % filename)
    config_parser.read(all_config_files)
    allow_unsafe_download = args.allow_unsafe_download
    add_freeze = args.freeze
    destination_dir = args.dest_dir
    only_packages = args.only
    verbose = args.verbose
    keep_temp = args.keep_temp

    installed_packages = {}
    normalized_to_name = {}
    installed_distributions = get_installed_distributions(local_only=True)
    for distrib in installed_distributions:
        assert isinstance(distrib, Distribution)
        normalized_to_name[normalize_package_name(distrib.project_name)] = distrib.project_name
        installed_packages[distrib.project_name] = distrib.version

    packages_to_create = {}
    for value in args.include:
        package_name, sep, package_version = value.partition('=')
        normalized_package_name = normalize_package_name(package_name)
        if sep != '=' and normalized_package_name not in normalized_to_name:
            print('%s not installed: please specify its version (e.g. %s %s=1.0.0)' %
                  (package_name, sys.argv[0], package_name))
        elif sep == '=':
            packages_to_create[package_name] = package_version
        else:
            package_name = normalized_to_name[normalized_package_name]
            packages_to_create[package_name] = installed_packages[package_name]

    if add_freeze:
        packages_to_create.update(installed_packages)

    exclude_option = 'exclude' if sys.version_info[0] == 2 else 'exclude3'
    if config_parser.has_option('multideb', exclude_option):
        excluded_packages = {x for x in config_parser.get('multideb', exclude_option).splitlines() if x.strip()}
    else:
        excluded_packages = set()
    excluded_packages |= {x for x in args.exclude}

    if config_parser.has_section('multideb-packages'):
        for option_name in config_parser.options('multideb-packages'):
            option_value = config_parser.get('multideb-packages', option_name)
            package_name, sep, package_version = option_value.partition('==')
            packages_to_create[package_name] = package_version

    deb_dest_dir = os.path.abspath(destination_dir)
    if not os.path.isdir(deb_dest_dir):
        os.makedirs(deb_dest_dir)
    if excluded_packages:
        print('List of packages excluded from deb. generation:')
        for package_name in excluded_packages:
            print(package_name)
    excluded_packages = {normalize_package_name(x) for x in excluded_packages}

    if only_packages:
        packages_to_create = {package_name: package_version
                              for (package_name, package_version) in packages_to_create.items()
                              if package_name in set(only_packages)}

    # create a temp dir and do the work
    cwd = os.getcwd()
    package_names = [x for x in packages_to_create]
    package_names.sort()
    for package_name in package_names:
        package_version = packages_to_create[package_name]
        if normalize_package_name(package_name) in excluded_packages:
            print('%s is excluded' % package_name)
            continue
        print('packaging %s...' % package_name)
        if dry:
            continue
        temp_dir = mkdtemp(suffix='-multideb')
        os.chdir(temp_dir)
        prepare_package(package_name, package_version, deb_dest_dir, config_parser, allow_unsafe_download, verbose=verbose)
        if not keep_temp:
            shutil.rmtree(temp_dir)
        else:
            print('%s-%s: %s' % (package_name, package_version, temp_dir))
    os.chdir(cwd)


def prepare_package(package_name, package_version, deb_dest_dir, multideb_config_parser, allow_unsafe_download, verbose=True):
    """
    :param package_name: name of the package to prepare
    :type package_name: :class:`str`
    :param package_version: version of the package to prepare
    :type package_version: :class:`str`
    :param deb_dest_dir: directory where to put created Debian packages
    :type deb_dest_dir: :class:`str`
    :param multideb_config_parser: multideb configuration file
    :type multideb_config_parser: :class:`configparser.ConfigParser`
    :param allow_unsafe_download:  allow unsafe downloads?  (see pip documentation)
    :type allow_unsafe_download: :class:`bool`
    """
    assert isinstance(multideb_config_parser, configparser.ConfigParser)
    print('downloading %s %s' % (package_name, package_version))
    filename = get_source_tarball(package_name, verbose=False, release=package_version, allow_unsafe_download=allow_unsafe_download)
    # expand source file
    expand_sdist_file(os.path.abspath(filename), cwd=os.getcwd())
    directories = [x for x in os.listdir(os.getcwd()) if os.path.isdir(os.path.join(os.getcwd(), x))]
    if len(directories) != 1:
        raise ValueError('Require a single directory in %s' % os.getcwd())
    os.chdir(directories[0])
    subprocess.check_output("rm -rf `find * | grep \\.pyc$`", shell=True)
    run_hook(package_name, package_version, 'pre_source', None, multideb_config_parser)

    # config file for each package?
    new_config_parser = configparser.ConfigParser()
    new_config_parser.read(['stdeb.cfg'])
    section_names = (package_name, )
    if sys.version_info[0] == 3:
        section_names = (package_name, package_name + '-python3')
    for section_name in section_names:
        if multideb_config_parser.has_section(section_name):
            for option_name in multideb_config_parser.options(section_name):
                option_value = multideb_config_parser.get(section_name, option_name)
                new_config_parser.set('DEFAULT', option_name, option_value)
    with codecs.open('stdeb.cfg', 'w', encoding='utf-8') as fd:
        new_config_parser.write(fd)
    call_kwargs = {} if verbose else {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
    print('preparing Debian source')
    check_call(['python', 'setup.py', '--command-packages', 'stdeb.command', 'sdist_dsc'], **call_kwargs)

    # find the actual debian source dir
    directories = [x for x in os.listdir('deb_dist') if x != 'tmp_py2dsc' and os.path.isdir(os.path.join('deb_dist', x))]
    if len(directories) != 1:
        raise ValueError('Require a single directory in %s/deb_dist' % os.getcwd())
    debian_source_dir = os.path.abspath(os.path.join('deb_dist', directories[0]))
    # check if we have a post-source to execute
    run_hook(package_name, package_version, 'post_source', debian_source_dir, multideb_config_parser)
    # build .deb from the source
    print('creating package')
    check_call(['dpkg-buildpackage', '-rfakeroot', '-uc', '-b'], cwd=debian_source_dir, **call_kwargs)
    # move the .deb to destination dir
    packages = glob.glob('deb_dist/*.deb')
    if not packages:
        raise ValueError('Unable to create %s-%s' % (package_name, package_version))
    print('moving %s' % os.path.basename(packages[0]))
    shutil.move(packages[0], os.path.join(deb_dest_dir, os.path.basename(packages[0])))


def run_hook(package_name, package_version, hook_name, debian_source_dir, multideb_config_parser):
    if multideb_config_parser.has_option(package_name, hook_name):
        hook_name = multideb_config_parser.get(package_name, hook_name)
        print("Using %s as %s hook for %s" % (hook_name, hook_name, package_name))
        source_hook = import_string(hook_name)
        source_hook(package_name, package_version, debian_source_dir)


# noinspection PyUnusedLocal
def remove_tests_dir(package_name, package_version, deb_src_dir):
    """ Post source hook for removing `tests` dir """
    if os.path.isdir('tests'):
        shutil.rmtree('tests')

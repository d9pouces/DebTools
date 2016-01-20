multideb
========

Create several Debian packages at once.
Fetch the list of installed Python packages in the current virtualenv and package them as .deb packages using the standard `stdeb` tool.
You can also:

  * define the packages to create in a configuration file,
  * specify options for any of these packages,
  * run Python commands after archive expansion and between the creation of Debian source and the creation of the Debian package.

To create Debian packages for all currently installed Python packages, use the following command:

.. code-block:: bash

    multideb --freeze

All options must be defined in a `stdeb.cfg` configuration file.
In the [multideb-packages] section of `stdeb.cfg`, you can define extra packages to create: option name is the name of the package, option value is the required version.
In the [multideb] section of `stdeb.cfg`, you can exclude some packages from .deb creation:

.. code-block:: bash

    [multideb]
    exclude = celery
        django
        gunicorn

You can define specific options for a given package. In addition of standard `stdeb` options, you can also define `pre_source` and `post_source` options.
Values must be an importable Python function, which will be called with the following arguments `my_callable(package_name, package_version, deb_src_dir)`.

Here is the list of actions:

  * download .tar.gz of the source code,
  * expand this file,
  * run the `pre_source` function (if defined),
  * run `python setup.py sdist_dsc`,
  * run the `post_source` function (if defined),
  * create the package with `dpkg-buildpackage`.

Usage:

.. code-block:: bash

    multideb

Here is a sample `stdeb.cfg` file:

.. code-block:: ini

    [multideb-packages]
    django = 1.8.3

    [multideb]
    exclude = funcsigs
        django-allauth
        gunicorn

    [django]
    pre_source = multideb.remove_tests_dir

    [celery]
    post_source = multideb.fix_celery

    ; list of standard stdeb options
    [other_package]
    Source = debian/control Source: (Default: <source-debianized-setup-name>)
    Package = debian/control Package: (Default: python-<debianized-setup-name>)
    Suite = suite (e.g. stable, lucid) in changelog (Default: unstable)
    Maintainer = debian/control Maintainer: (Default: <setup-maintainer-or-author>)
    Section = debian/control Section: (Default: python)
    Epoc = version epoch
    Depends = debian/control Depends:
    Depends3 = debian/control Depends: for python3
    Suggests = debian/control Suggests:
    Suggests3 = debian/control Suggests: for python3
    Recommends = debian/control Recommends:
    Recommends3 = debian/control Recommends: for python3
    Conflicts = debian/control Conflicts:
    Uploaders = uploaders
    Conflicts3 = debian/control Conflicts: for python3
    Provides = debian/control Provides:
    Provides3 = debian/control Provides: for python3
    Replaces = debian/control Replaces:
    Replaces3 = debian/control Replaces: for python3
    Copyright-File = copyright file
    Build-Conflicts = debian/control Build-Conflicts:
    MIME-File = MIME file
    Udev-Rules = file with rules to install to udev
    Debian-Version = debian version (Default: 1)
    Build-Depends = debian/control Build-Depends:
    Forced-Upstream-Version = forced upstream version
    Upstream-Version-Suffix = upstream version suffix
    Stdeb-Patch-File = file containing patches for stdeb to apply
    XS-Python-Version = debian/control XS-Python-Version:
    Dpkg-Shlibdeps-Params = parameters passed to dpkg-shlibdeps
    Stdeb-Patch-Level = patch level provided to patch command
    Upstream-Version-Prefix = upstream version prefix
    X-Python3-Version = debian/control X-Python3-Version:
    MIME-Desktop-Files = MIME desktop files
    Shared-MIME-File = shared MIME file
    Setup-Env-Vars = environment variables passed to setup.py

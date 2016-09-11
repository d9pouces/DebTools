aptenv
======

When your application is meant to be deployed using the official Ubuntu or Debian packages (like `python-django`).
`aptenv` takes a list of Python packages (a standard requirements files, like the one produced by the `pip freeze command`) or the list of currently installed packages and fetch the list of available versions in the Ubuntu or Debian mirrors.

.. code-block:: bash

   aptenv -u xenial -u xenial-updates --python 3 -r requirements.txt


You can also fetch the available Python version
.. code-block:: bash

   aptenv -u xenial -u xenial-updates --python 3 -P
   python3.5
   aptenv -u trusty -u trusty-updates --python 3 -P
   python3.4
   aptenv -u precise -u precise-updates --python 3 -P
   python3.2
   aptenv -u trusty -u trusty-updates --python 2 -P
   python2.7


By default, the debianized name of a Python package starts by `python-` or `python3-`. Some packages have a specific name.
For example, the debian name of `ansible` is `ansible`.
You can specify a file with all your exceptions, and the mapping for a few well-known Python packages is provided, you can use it with `-M`. You can also use this system for excluding some packages:

.. code-block:: bash

  echo "PyYAML==3.12" > requirements.txt
  aptenv -u xenial -u xenial-updates --python 3 -r requirements.txt
  Unable to find any version for PyYAML
  echo "PyYAML=python-yaml" > map
  aptenv -u xenial -u xenial-updates --python 3 -r requirements.txt -m map
  PyYAML==3.11
  aptenv -u xenial -u xenial-updates --python 3 -r requirements.txt -M
  PyYAML==3.11
  echo "PyYAML=" > map
  aptenv -u xenial -u xenial-updates --python 3 -r requirements.txt -m map


Then you can create a virtualenv corresponding to a plain Ubuntu Xenial or a Debian Stable installation:

.. code-block:: bash

  aptenv -u xenial -u xenial-updates --python 3 -r requirements.txt > requirements-ubuntu-xenial.rst
  mkvirtualenv ubuntu-xenial -p `aptenv -u xenial -u xenial-updates --python 3 -P` -r requirements-ubuntu-xenial.rst

.. code-block:: bash

  aptenv -u jessie -u jessie-backports --python 3 -r requirements.txt > requirements-debian-jessie.rst
  mkvirtualenv ubuntu-xenial -p `aptenv -u jessie -u jessie-backports --python 3 -P` -r requirements-debian-jessie.rst
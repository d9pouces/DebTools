Installing
==========

DebTools is compatible with Python 2.7.x and Python 3.2+.
Two dependencies are required:

  * stdeb
  * backports.lzma (only required on Python 2.7 and 3.2/3.3)

The easiest way is to use pip:

.. code-block:: bash

  pip install debtools

If debtools was already installed:

.. code-block:: bash

  pip install debtools --upgrade


If you prefer install directly from the source:

.. code-block:: bash

  cd DebTools
  python setup.py install


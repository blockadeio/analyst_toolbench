Blockade Analyst Bench
======================

.. image:: https://img.shields.io/pypi/dm/blockade-toolkit.svg
    :target: https://pypi.python.org/pypi/blockade-toolkit/

.. image:: https://img.shields.io/pypi/v/blockade-toolkit.svg
   :target: https://pypi.python.org/pypi/blockade-toolkit

.. image:: https://img.shields.io/badge/blockade-toolkit-2.7-blue.svg
    :target: https://pypi.python.org/pypi/blockade-toolkit/

.. image:: https://img.shields.io/pypi/l/blockade-toolkit.svg
    :target: https://pypi.python.org/pypi/blockade-toolkit/

Introduction
------------

*Python client for Blockade.io services*

Command-line scripts
--------------------

The following command line scripts are installed with the library:

- **blockade-cfg**: utility to set or query API configuration options for the
  library (email and API key).
- **blockade**: primary client to interface with the blockade backend services.

See the *Usage* section for more information.

Installation
------------

From the downloaded source distribution::

    $ python setup.py install

Or from PyPI::

    $ pip install blockade [--upgrade]

The package depends on the `requests`, `grequests` and `tldextract`. If these are not present, they will be installed.

Setup
-----

Users must supply their email and API key in order for this library to function. On the first setup run, validated whitelists will be downloaded and stored within the configuration directory. First-time setup requires configuring your API email and private key for authentication::

    $ blockade-cfg setup <EMAIL> <API_KEY>

At any time, the current API configuration parameters can be queried using the same utility::

    $ blockade-cfg show

Configuration parameters are stored in **$HOME/.config/blockade/api_config.json**.

Upgrades
--------

Our libraries support Python 3 through futures. On certain platforms, this causes issues when doing upgrades of the library. When performing an update, use the following:

    sudo pip install blockade --upgrade --ignore-installed six

Usage
-----

Every command-line script has several sub-commands that may be passed to it. The
commands usage may be described with the ``-h/--help`` option.

For example::

    $ blockade -h
    usage: blockade [-h] {ioc} ...

    Blockade Analyst Bench

    positional arguments:
      {ioc}
        ioc       Perform actions with IOCs

    optional arguments:
      -h, --help  show this help message and exit

Every sub-command has further help options:::

    $ blockade ios -h
    usage: blockade ioc [-h] [--single SINGLE] [--file FILE]

    optional arguments:
      -h, --help            show this help message and exit
      --single SINGLE, -s SINGLE
                            Send a single IOC
      --file FILE, -f FILE  Parse a file of IOCs

Support
-------

Please use the issues_ section for any bug reporting, comments or other feedback.

.. _issues: https://github.com/blockadeio/analyst_toolbench/issues
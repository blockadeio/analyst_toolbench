Installation
------------
From the downloaded source distribution::

    $ python setup.py install

Or from PyPI::

    $ pip install blockade-toolkit [--upgrade]

The package depends on several external libraries. If these are not present, they will be installed automatically. A ``requirements.txt`` file is included in the repository which outlines these dependencies in detail.

Setup
-----
Users must supply their email and API key in order for this library to function. On the first setup run, validated whitelists will be downloaded and stored within the configuration directory. First-time setup requires configuring your API email and private key for authentication::

    $ blockade-cfg setup <EMAIL> <API_KEY>

At any time, the current API configuration parameters can be queried using the same utility::

    $ blockade-cfg show

Configuration parameters are stored in **$HOME/.config/blockade/api_config.json**.

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
#!/usr/bin/env python
"""Python setup file to install the blockade toolset."""
from setuptools import setup, find_packages

setup(
    name='blockade',
    version='1.0.0',
    description='Analyst client for administering Blockade.io',
    url="https://github.com/blockadeio/chrome_extension",
    author="Brandon Dixon",
    author_email="info@blockade.io",
    license="GPLv2",
    packages=find_packages(),
    install_requires=['requests', 'ez_setup', 'future', 'grequests',
                      'tldextract'],
    long_description="Blockade brings antivirus-like capabilities to users who run the Chrome browser. Built as an extension, Blockade blocks malicious resources from being viewed or loaded inside of the browser.",
    classifiers=[],
    entry_points={
        'console_scripts': [
            'blockade-cfg = blockade.cli.config:main',
            'blockade = blockade.cli.client:main'
        ],
    },
    package_data={
        'blockade': [],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=['threats', 'research', 'analysis'],
    download_url='https://github.com/blockadeio/chrome_extension/archive/master.zip'
)

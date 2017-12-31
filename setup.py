#!/usr/bin/env python
"""Python setup file to install the blockade toolset."""
from setuptools import setup, find_packages

setup(
    name='blockade-toolkit',
    version='1.0.2',
    description='Analyst client for administering Blockade.io',
    url="https://github.com/blockadeio/analyst_toolbench",
    author="Brandon Dixon",
    author_email="info@blockade.io",
    license="GPLv2",
    packages=find_packages(),
    install_requires=['requests', 'ez_setup', 'future', 'grequests',
                      'tldextract', 'boto3'],
    long_description="Blockade brings antivirus-like capabilities to users who run the Chrome browser. Built as an extension, Blockade blocks malicious resources from being viewed or loaded inside of the browser.",
    classifiers=[],
    entry_points={
        'console_scripts': [
            'blockade-cfg = blockade.cli.config:main',
            'blockade-aws-deploy = blockade.cli.aws_serverless:main',
            'blockade = blockade.cli.client:main'
        ],
    },
    package_data={
        'blockade-toolkit': [],
        '': ['*.zip']
    },
    include_package_data=True,
    zip_safe=False,
    keywords=['threats', 'research', 'analysis', 'information security'],
    download_url='https://github.com/blockadeio/analyst_toolbench/archive/master.zip'
)

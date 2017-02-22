#!/usr/bin/env python
"""Init the configuration for the toolset."""
__author__ = 'Brandon Dixon'
__version__ = '1.0.0'

from blockade.config import Config
from argparse import ArgumentParser
from datetime import datetime


def show_config(config):
    """Show the current configuration."""
    print("\nCurrent Configuration:\n")
    for k, v in sorted(config.config.items()):
        print("{0:15}: {1}".format(k, v))


def main():
    """Run the core."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')

    setup_parser = subs.add_parser('setup')
    setup_parser.add_argument('email', help="Email associated with the \
                                                API key and account")
    setup_parser.add_argument('key', help='API key')
    setup_parser.add_argument('--api-node', '--node', default='api.blockade.io',
                              help='Node to store indicators')
    setup_parser.add_argument('--http-proxy', '--http', default='',
                              help='proxy to use for http requests')
    setup_parser.add_argument('--https-proxy', '--https', default='',
                              help='proxy to use for https requests')
    subs.add_parser('show', help='show current API configuration')
    args = parser.parse_args()

    if args.cmd == 'show':
        config = Config()
        show_config(config)
    elif args.cmd == 'setup':
        config_options = {}
        config_options['api_key'] = args.key
        config_options['email'] = args.email
        config_options['api_server'] = args.api_node
        config_options['http_proxy'] = args.http_proxy
        config_options['https_proxy'] = args.https_proxy
        config_options['whitelist_date'] = datetime.now().strftime('%Y-%m-%d')
        config = Config(**config_options)
        show_config(config)

if __name__ == '__main__':
    main()

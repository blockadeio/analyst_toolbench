#!/usr/bin/env python
"""Init the configuration for the toolset."""
import json
import requests
from blockade.config import Config
from argparse import ArgumentParser
from datetime import datetime


def show_config(config):
    """Show the current configuration."""
    print("\nCurrent Configuration:\n")
    for k, v in sorted(config.config.items()):
        print("{0:15}: {1}".format(k, v))


def create_cloud_user(cfg, args):
    """Attempt to create the user on the cloud node."""
    url = cfg['api_server'] + "admin/add-user"
    params = {'user_email': args.user_email, 'user_name': args.user_name,
              'user_role': args.user_role, 'email': cfg['email'],
              'api_key': cfg['api_key']}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(params),
                             headers=headers)
    if response.status_code not in range(200, 299):
        raise Exception("Errors contacting the cloud node: %s" % (response.content))
    loaded = json.loads(response.content)
    return loaded


def main():
    """Run the core."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')

    setup_parser = subs.add_parser('add-user')
    setup_parser.add_argument('--user-email', required=True,
                              help='Email address of the new user')
    setup_parser.add_argument('--user-name', required=True,
                              help='Name of the new user')
    setup_parser.add_argument('--user-role', choices=['admin', 'analyst'],
                              required=True, help='Role of the new user')
    setup_parser.add_argument('--replace-config', action='store_false',
                              help='Replace the existing credentials with the new user')

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
    elif args.cmd == 'add-user':
        config = Config().config
        api_node = config.get('api_server', None)
        email = config.get('email', None)
        api_key = config.get('api_key', None)
        if not api_node or not email or not api_key:
            raise Exception("Perform initial configuration using `setup` before adding users!")
        config = {'api_server': api_node, 'email': email, 'api_key': api_key}
        user = create_cloud_user(config, args)
        print("User successfully created:")
        print("Blockade Email: %s" % (user['email']))
        print("Blockade API Key: %s" % (user['api_key']))


if __name__ == '__main__':
    main()

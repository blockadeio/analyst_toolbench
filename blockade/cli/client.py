#!/usr/bin/env python
"""Client to interact with blockade."""
__author__ = 'Brandon Dixon'
__version__ = '1.0.0'

import sys
import os.path
from argparse import ArgumentParser
from blockade.libs.indicators import IndicatorClient


def process_ioc(args):
    """Process actions related to the IOC switch."""
    client = IndicatorClient.from_config()
    client.set_debug(True)
    if args.single:
        response = client.add_indicators([args.single])
    else:
        if not os.path.isfile(args.file):
            raise Exception("File path isn't valid!")
        indicators = [x.strip() for x in open(args.file, 'r').readlines()]
        response = client.add_indicators(indicators)
    return response


def main():
    """Run the code."""
    parser = ArgumentParser(description="Blockade Analyst Bench")
    subs = parser.add_subparsers(dest='cmd')

    ioc = subs.add_parser('ioc', help="Perform actions with IOCs")
    ioc.add_argument('--single', '-s', help="Send a single IOC")
    ioc.add_argument('--file', '-f', help="Parse a file of IOCs")
    args, unknown = parser.parse_known_args()

    try:
        if args.cmd == 'ioc':
            if (args.single and args.file):
                raise Exception("Can't use single and file together!")
            response = process_ioc(args)
        else:
            parser.print_usage()
            sys.exit(1)
    except ValueError as e:
        parser.print_usage()
        sys.stderr.write('{}\n'.format(str(e)))
        sys.exit(1)

    print response['message']

if __name__ == "__main__":
    main()

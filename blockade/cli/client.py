#!/usr/bin/env python
"""Client to interact with blockade."""
__author__ = 'Brandon Dixon'
__version__ = '1.0.0'

import sys
import os.path
from argparse import ArgumentParser
from blockade.libs.indicators import IndicatorClient
from blockade.libs.events import EventsClient


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


def process_events(args):
    """Process actions related to events switch."""
    client = EventsClient.from_config()
    client.set_debug(True)
    if args.get:
        response = client.get_events()
    return response


def main():
    """Run the code."""
    parser = ArgumentParser(description="Blockade Analyst Bench")
    subs = parser.add_subparsers(dest='cmd')

    ioc = subs.add_parser('ioc', help="Perform actions with IOCs")
    ioc.add_argument('--single', '-s', help="Send a single IOC")
    ioc.add_argument('--file', '-f', help="Parse a file of IOCs")

    events = subs.add_parser('events', help="Perform actions with Events")
    events.add_argument('--get', '-g', action='store_true', help="Get recent events")
    events.add_argument('--flush', '-f', action='store_true', help="Flush all events from cloud node")

    args, unknown = parser.parse_known_args()

    try:
        if args.cmd == 'ioc':
            if (args.single and args.file):
                raise Exception("Can't use single and file together!")
            if (not args.single and not args.file):
                ioc.print_help()
                sys.exit(1)
            response = process_ioc(args)
        elif args.cmd == 'events':
            if (not args.get and not args.flush):
                events.print_help()
                sys.exit(1)
            response = process_events(args)
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

#!/usr/bin/env python
"""Indicator interface for blockade."""

__author__ = 'Brandon Dixon'
__version__ = '1.0.0'

import math
import time
from blockade.api import Client
from blockade.common.utils import (cache_items, check_whitelist,
                                   clean_indicators, hash_values, prune_cached)


class IndicatorClient(Client):

    """Client to interface with indicators for blockade."""

    def __init__(self, *args, **kwargs):
        """Setup the primary client instance."""
        super(IndicatorClient, self).__init__(*args, **kwargs)

    def add_indicators(self, indicators=list(), private=False, tags=list()):
        """Add indicators to the remote instance."""
        if len(indicators) == 0:
            raise Exception("No indicators were identified.")
        self.logger.debug("Checking {} indicators".format(len(indicators)))
        cleaned = clean_indicators(indicators)
        self.logger.debug("Cleaned {} indicators".format(len(cleaned)))
        whitelisted = check_whitelist(cleaned)
        self.logger.debug("Non-whitelisted {} indicators".format(len(whitelisted)))
        indicators = prune_cached(whitelisted)
        hashed = hash_values(indicators)
        self.logger.debug("Non-cached {} indicators".format(len(indicators)))
        self.logger.debug("Processing {} indicators".format(len(indicators)))
        request_count = int(math.ceil(len(indicators)/100.0))
        if request_count == 0:
            mesg = "[!] No indicators were left to process after "
            mesg += "cleaning, whitelisting and checking the cache."
            return {'message': mesg}
        stats = {'success': 0, 'failure': 0, 'requests': request_count,
                 'written': 0}
        mesg = "{} indicators found, making {} requests"
        self.logger.debug(mesg.format(len(indicators), request_count))

        if private:
            indicators = hashed

        if type(tags) == str:
            tags = [t.strip().lower() for t in tags.split(',')]

        start, end = (0, 100)
        for i, idx in enumerate(range(0, request_count)):
            if idx > 0:
                time.sleep(3)  # Ensure we never trip the limit
                self.logger.debug("Waiting 3 seconds before next request.")
            to_send = {'indicators': indicators[start:end], 'tags': tags}
            r = self._send_data('POST', 'admin', 'add-indicators', to_send)
            start, end = (end, end + 100)
            if not r['success']:
                stats['failure'] += 1
                continue
            stats['success'] += 1
            stats['written'] += r['writeCount']
            cache_items(to_send['indicators'])
        msg = ""
        msg += "{written} indicators written using {requests} requests: "
        msg += "{success} success, {failure} failure"
        stats['message'] = msg.format(**stats)
        return stats

    def get_indicators(self):
        """List indicators available on the remote instance."""
        response = self._get('', 'get-indicators')
        response['message'] = "%i indicators:\n%s" % (
            len(response['indicators']),
            "\n".join(response['indicators'])
        )
        return response

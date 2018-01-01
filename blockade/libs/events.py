#!/usr/bin/env python
"""Events interface for blockade."""

__author__ = 'Claudio Guarnieri'
__version__ = '1.0.0'

from blockade.api import Client


class EventsClient(Client):

    """Client to interface with events for blockade."""

    def __init__(self, *args, **kwargs):
        """Setup the primary client instance."""
        super(EventsClient, self).__init__(*args, **kwargs)

    def get_events(self):
        """Get events from the cloud node."""
        to_send = {'limit': 50}
        response = self._send_data('POST', 'admin', 'get-events', to_send)

        output = {'message': ""}
        for event in response['events']:
            event['url'] = event['metadata']['url']
            event['method'] = event['metadata']['method']
            event['type'] = event['metadata']['type']

            desc = "Source IP: {sourceIp}\n"
            desc += "Datetime: {analysisTime}\n"
            desc += "Indicator: {indicatorMatch}\n"
            desc += "Method: {method}\n"
            desc += "URL: {url}\n"
            desc += "Request Type: {type}\n"
            desc += "User-Agent: {userAgent}\n"
            desc += "Contact: {contact}\n"
            desc += "\n"
            output['message'] += desc.format(**event)

        return output

    def flush_events(self):
        """Flush events from the cloud node."""
        response = self._send_data('DELETE', 'admin', 'flush-events', {})

        if response['success']:
            msg = "Events flushed"
        else:
            msg = "Flushing of events failed"
        output = {'message': msg}

        return output

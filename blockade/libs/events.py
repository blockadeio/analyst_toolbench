#!/usr/bin/env python
"""Events interface for blockade."""

__author__ = 'Brandon Dixon'
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
        response = self._send_data('GET', 'admin', 'get-events', to_send)
        output = {'message': ""}
        for event in response['events']:
            desc = "Event from IP: {ip}\n"
            desc += "Date and time: {time}\n"
            desc += "Match: {match}\n"
            desc += "URL: {url}\n"
            desc += "User-Agent: {userAgent}\n"
            desc += "\n"
            output['message'] += desc.format(**event)
        return output

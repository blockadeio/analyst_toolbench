#!/usr/bin/env python
"""Events interface for blockade."""

__author__ = 'Brandon Dixon'
__version__ = '1.0.0'

import math
import time
from blockade.api import Client

class EventsClient(Client):

    """Client to interface with events for blockade."""

    def __init__(self, *args, **kwargs):
        """Setup the primary client instance."""
        super(EventsClient, self).__init__(*args, **kwargs)

    def get_events(self):
        to_send = {'limit': 50}
        response = self._send_data('GET', 'admin', 'get-events', to_send)
        output = {'message': "Fetched events"}
        return output

#!/usr/bin/env python
"""Abstraction over the Blockade.io admin API."""
import json
import requests
from blockade.config import Config
from blockade.common.utils import get_logger


class Client(object):

    """Base client that all data sources will inherit from."""

    DEFAULT_SERVER = 'api.blockade.io'
    TIMEOUT = 30

    def __init__(self, email, api_key, server=DEFAULT_SERVER,
                 http_proxy=None, https_proxy=None, verify=True, headers=None,
                 debug=False):
        """Initial loading of the client.

        :param str email: Email of the blockade user
        :param str api_key: API key for the blockade user
        :param str server: Hostname for the API
        :param str http_proxy: HTTP proxy to use (optional)
        :param str https_proxy: HTTPS proxy to use (optional)
        """
        self.logger = get_logger('blockade-request')
        if server.endswith('/'):
            server = server.rstrip('/')
        self.api_base = server
        if server[0:4].lower() != 'http':
            self.api_base = 'https://%s' % (server)
        self.email = email
        self.api_key = api_key
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        self.proxies = {}
        if http_proxy:
            self.proxies['http'] = http_proxy
        if https_proxy:
            self.proxies['https'] = https_proxy
        if headers:
            self.headers.update(headers)
        self.verify = verify
        if '127.0.0.1' in server:
            self.verify = False

    @classmethod
    def from_config(cls):
        """Method to return back a loaded instance."""
        config = Config()
        client = cls(
            email=config.get('email'),
            api_key=config.get('api_key'),
            server=config.get('api_server'),
            http_proxy=config.get('http_proxy'),
            https_proxy=config.get('https_proxy'),
        )
        return client

    def set_debug(self, status):
        """Control the logging state."""
        if status:
            self.logger.setLevel('DEBUG')
        else:
            self.logger.setLevel('INFO')

    def _endpoint(self, endpoint, action, *url_args):
        """Return the URL for the action.

        :param str endpoint: The controller
        :param str action: The action provided by the controller
        :param url_args: Additional endpoints(for endpoints that take part of
                         the url as option)
        :return: Full URL for the requested action
        """
        args = (self.api_base, endpoint, action)
        if action == '':
            args = (self.api_base, endpoint)
        api_url = "/".join(args)
        if url_args:
            if len(url_args) == 1:
                api_url += "/" + url_args[0]
            else:
                api_url += "/".join(url_args)
        return api_url

    def _json(self, response):
        """JSON response from server.

        :param response: Response from the server
        :throws ValueError: from requests' response.json() error
        :return: response deserialized from JSON
        """
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as e:
            raise ValueError(
                'Exception: %s\n'
                'request: %s, response code: %s, response: %s' % (
                    str(e), response.request.url, response.status_code,
                    response.content,
                )
            )

    def _get(self, endpoint, action, *url_args, **url_params):
        """Request API Endpoint - for GET methods.

        :param str endpoint: Endpoint
        :param str action: Endpoint Action
        :param url_args: Additional endpoints(for endpoints that take part of
                         the url as option)
        :param url_params: Parameters to pass to url, typically query string
        :return: response deserialized from JSON
        """
        api_url = self._endpoint(endpoint, action, *url_args)
        kwargs = {'headers': self.headers, 'params': url_params,
                  'timeout': Client.TIMEOUT, 'verify': self.verify}
        if self.proxies:
            kwargs['proxies'] = self.proxies
        self.logger.debug("Requesting: %s, %s" % (api_url, str(kwargs)))
        response = requests.get(api_url, **kwargs)
        return self._json(response)

    def _send_data(self, method, endpoint, action,
                   data, *url_args, **url_params):
        """Submit to API Endpoint - for DELETE, PUT, POST methods.

        :param str method: Method to use for the request
        :param str endpoint: Endpoint
        :param str action: Endpoint Action
        :param url_args: Additional endpoints(for endpoints that take part of
                         the url as option)
        :param url_params: Parameters to pass to url, typically query string
        :return: response deserialized from JSON
        """
        api_url = self._endpoint(endpoint, action, *url_args)
        data.update({'email': self.email, 'api_key': self.api_key})
        data = json.dumps(data)
        kwargs = {'headers': self.headers, 'params': url_params,
                  'verify': self.verify, 'data': data}
        if self.proxies:
            kwargs['proxies'] = self.proxies
        self.logger.debug("Requesting: %s %s, %s" % (method, api_url,
                                                     str(kwargs)))
        response = requests.request(method, api_url, **kwargs)
        self.logger.debug("Response: %d, %s" % (response.status_code,
                                                response.content))
        return self._json(response)

"""The primary module for pypco containing main wrapper logic."""

import time
import logging

import requests

from .auth_config import PCOAuthConfig
from .exceptions import PCORequestTimeoutException

class PCO():
    """The entry point to the PCO API.

    Attributes:
        auth_config (PCOAuthConfig): The authentication configuration for this instance.
    """

    def __init__(
            self,
            api_base,
            application_id=None,
            secret=None,
            token=None,
            timeout=60,
            upload_timeout=300,
            timeout_retries=3
        ):
        """Initialize the PCO entry point.

        Args:
            api_base (str): The base URL against which REST calls will be made.
            application_id (str): The application_id; secret must also be specified.
            secret (str): The secret for your app; application_id must also be specified.
            token (str): OAUTH token for your app; application_id and secret must not be specified.
            timeout (int): How long to wait (seconds) for requests to timeout. Default 60.
            upload_timeout (int): How long to wait (seconds) for uploads to timeout. Default 300.
            timeout_retries (int): How many times to retry requests that have timed out. Default 3.

        Note:
            You must specify either an application ID and a secret or an oauth token.
            If you specify an invalid combination of these arguments, an exception will be
            raised when you attempt to make API calls.
        """

        self._log = logging.getLogger(__name__)

        self.api_base = api_base

        self._auth_config = PCOAuthConfig(application_id, secret, token)
        self._auth_header = self._auth_config.auth_header

        self.timeout = timeout
        self.upload_timeout = upload_timeout
        self.timeout_retries = timeout_retries

        self._log.info("Pypco has been initialized!")

    def _do_request(self, method, url, payload=None, upload=None, **params):
        """Builds, executes, and performs a single request against the PCO API.

        Executed request could be one of the standard HTTP verbs or a file upload.

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Returns:
            (requests.Response): The response to this request.
        """

        # Standard header
        headers = {
            'User-Agent': 'pypco',
            'Authorization': self._auth_header,
        }

        # Standard params
        request_params = {
            'headers':headers,
            'params':params,
            'json':payload,
            'timeout': self.upload_timeout if upload else self.timeout
        }

        # Add files param if upload specified
        if upload:
            request_params['files'] = {'file': open(upload, 'rb')}

        self._log.debug("Executing %s request to '%s' with args %s", method, url, request_params)

        # The moment we've been waiting for...execute the request
        return requests.request(
            method,
            url,
            **request_params
        )

    def _do_timeout_managed_request(self, method, url, payload=None, upload=None, **params):

        timeout_count = 0

        while True:
            try:
                return self._do_request(method, url, payload, upload, **params)

            except requests.exceptions.Timeout as exc:
                timeout_count += 1

                self._log.debug("The request to \"%s\" timed out after %d tries.", \
                    url, timeout_count)

                if timeout_count == self.timeout_retries:
                    self._log.debug("Maximum retries (%d) hit. Will raise exception.", \
                        self.timeout_retries)

                    raise PCORequestTimeoutException( \
                        "The request to \"%s\" timed out after %d tries." \
                        % (url, timeout_count)) from exc

                continue

    def _do_ratelimit_managed_request(self, method, url, payload=None, upload=None, **params):

        while True:

            response = self._do_timeout_managed_request(method, url, payload, upload, **params)

            if response.status_code == 429:
                self._log.debug("Received rate limit response. Will try again after %d sec(s).", \
                    int(response.headers['Retry-After']))

                time.sleep(int(response.headers['Retry-After']))
                continue

            return response

    def _do_url_managed_request(self, method, url, payload=None, upload=None, **params):
        pass

    def request(self):
        # TODO: The generic public entry point for requests
        # This will be called by shortcut methods or can be called
        # externally by the user

        # TODO: Make this throw a custom error class
        # response.raise_for_status()

        # return response.json()
        pass

    def get(self, url, **params):
        return self._do_request('GET', url, **params)

    def post(self, url, payload=None, **params):
        return self._do_request('POST', url, payload, **params)

    def put(self, url, payload=None, **params):
        return self._do_request('PUT', url, payload, **params)

    def delete(self, url, **params):
        return self._do_request('DELETE', url, **params)

    def iterate(self):
        # TODO: Consider appropriate way to handle includes
        pass

    def upload(self, file_path):
        pass

    @staticmethod
    def new(object_type):
        # TODO: Add quick template function to create new objects
        pass

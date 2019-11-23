"""The primary module for pypco containing main wrapper logic."""

import time
import logging
import re

import requests

from .auth_config import PCOAuthConfig
from .exceptions import PCORequestTimeoutException, \
    PCORequestException

class PCO():
    """The entry point to the PCO API.

    Note:
        You must specify either an application ID and a secret or an oauth token.
        If you specify an invalid combination of these arguments, an exception will be
        raised when you attempt to make API calls.

    Args:
        api_base (str): The base URL against which REST calls will be made.
        application_id (str): The application_id; secret must also be specified.
        secret (str): The secret for your app; application_id must also be specified.
        token (str): OAUTH token for your app; application_id and secret must not be specified.
        timeout (int): How long to wait (seconds) for requests to timeout. Default 60.
        upload_timeout (int): How long to wait (seconds) for uploads to timeout. Default 300.
        timeout_retries (int): How many times to retry requests that have timed out. Default 3.
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

        self._log = logging.getLogger(__name__)

        self.api_base = api_base

        self._auth_config = PCOAuthConfig(application_id, secret, token)
        self._auth_header = self._auth_config.auth_header

        self.timeout = timeout
        self.upload_timeout = upload_timeout
        self.timeout_retries = timeout_retries

        self._log.debug("Pypco has been initialized!")

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
        """Performs a single request against the PCO API with automatic retried in case of timeout.

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
        """Performs a single request against the PCO API with automatic rate limit handling.

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


        while True:

            response = self._do_timeout_managed_request(method, url, payload, upload, **params)

            if response.status_code == 429:
                self._log.debug("Received rate limit response. Will try again after %d sec(s).", \
                    int(response.headers['Retry-After']))

                time.sleep(int(response.headers['Retry-After']))
                continue

            return response

    def _do_url_managed_request(self, method, url, payload=None, upload=None, **params):
        """Performs a single request against the PCO API, automatically cleaning up the URL.

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

        self._log.debug("URL cleaning input: \"%s\"", url)

        url = url if url.startswith(self.api_base) else f'{self.api_base}{url}'
        url = re.subn(r'(?<!:)[/]{2,}', '/', url)[0]

        self._log.debug("URL cleaning output: \"%s\"", url)

        return self._do_ratelimit_managed_request(method, url, payload, upload, **params)

    def request_response(self, method, url, payload=None, upload=None, **params):
        """A generic entry point for making a managed request against PCO.

        This function will return a Requests response object, allowing access to
        all request data and metadata. Executed request could be one of the standard
        HTTP verbs or a file upload. If you're just looking for your data (json), use
        the request_json() function or get(), post(), etc.

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Raises:
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            (requests.Response): The response to this request.
        """

        response = self._do_url_managed_request(method, url, payload, upload, **params)

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            self._log.debug("Request resulted in API error: \"%s\"", str(err))
            raise PCORequestException(response.status_code, str(err)) from err

        return response

    def request_json(self, method, url, payload=None, upload=None, **params):
        """A generic entry point for making a managed request against PCO.

        This function will return the payload from the PCO response (a dict).

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Returns:
            (dict): The payload from the response to this request.
        """

        return self.request_response(method, url, payload, upload, **params).json()

    def get(self, url, **params):
        """Perform a GET request against the PCO API.

        Performs a fully managed GET request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Returns:
            (dict): The payload returned by the API for this request.
        """

        return self.request_json('GET', url, **params)

    def post(self, url, payload=None, **params):
        """Perform a POST request against the PCO API.

        Performs a fully managed POST request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            payload (dict): The payload for the POST request. Must be serializable to JSON!
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Returns:
            (dict): The payload returned by the API for this request.
        """

        return self.request_json('POST', url, payload, **params)

    def patch(self, url, payload=None, **params):
        """Perform a PATCH request against the PCO API.

        Performs a fully managed PATCH request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            payload (dict): The payload for the PUT request. Must be serializable to JSON!
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Returns:
            (dict): The payload returned by the API for this request.
        """

        return self.request_json('PATCH', url, payload, **params)

    def delete(self, url, **params):
        return self._do_request('DELETE', url, **params)

    def iterate(self):
        # TODO: Consider appropriate way to handle includes
        pass

    def upload(self, file_path):
        pass

    @staticmethod
    def template(object_type, attributes=None):
        """Get template JSON for creating a new object.

        Args:
            object_type (str): The type of object to be created.
            attributes (dict): The new objects attributes. Defaults to empty.

        Returns:
            (dict): A template from which to set the new object's attributes.
        """

        return {
            'data': {
                'type': object_type,
                'attributes': {} if attributes is None else attributes
            }
        }

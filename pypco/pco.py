"""The primary module for pypco containing main wrapper logic."""

import time
import logging
import re

from typing import Any, Iterator, Optional
import requests

from .auth_config import PCOAuthConfig
from .exceptions import PCORequestTimeoutException, \
    PCORequestException, PCOUnexpectedRequestException


class PCO:  # pylint: disable=too-many-instance-attributes
    """The entry point to the PCO API.

    Note:
        You must specify either an application ID and a secret or an oauth token.
        If you specify an invalid combination of these arguments, an exception will be
        raised when you attempt to make API calls.

    Args:
        application_id (str): The application_id; secret must also be specified.
        secret (str): The secret for your app; application_id must also be specified.
        token (str): OAUTH token for your app; application_id and secret must not be specified.
        api_base (str): The base URL against which REST calls will be made.
            Default: https://api.planningcenteronline.com
        timeout (int): How long to wait (seconds) for requests to timeout. Default 60.
        upload_url (str): The URL to which files will be uploaded.
            Default: https://upload.planningcenteronline.com/v2/files
        upload_timeout (int): How long to wait (seconds) for uploads to timeout. Default 300.
        timeout_retries (int): How many times to retry requests that have timed out. Default 3.
    """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            application_id: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            secret: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            token: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            cc_name: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            api_base: str = 'https://api.planningcenteronline.com',
            timeout: int = 60,
            upload_url: str = 'https://upload.planningcenteronline.com/v2/files',
            upload_timeout: int = 300,
            timeout_retries: int = 3,
    ):

        self._log = logging.getLogger(__name__)

        self._auth_config = PCOAuthConfig(application_id, secret, token, cc_name)
        self._auth_header = self._auth_config.auth_header

        self.api_base = api_base
        self.timeout = timeout

        self.upload_url = upload_url
        self.upload_timeout = upload_timeout

        self.timeout_retries = timeout_retries

        self.session = requests.Session()

        self._log.debug("Pypco has been initialized!")

    def _do_request(
            self,
            method: str,
            url: str,
            payload: Optional[Any] = None,  # pylint: disable=unsubscriptable-object
            upload: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            **params
    ) -> requests.Response:
        """Builds, executes, and performs a single request against the PCO API.

        Executed request could be one of the standard HTTP verbs or a file upload.

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Returns:
            requests.Response: The response to this request.
        """

        # Standard header
        headers = {
            'User-Agent': 'pypco',
            'Authorization': self._auth_header,
        }

        # Standard params
        request_params = {
            'headers': headers,
            'params': params,
            'json': payload,
            'timeout': self.upload_timeout if upload else self.timeout
        }

        # Add files param if upload specified
        if upload:
            upload_fh = open(upload, 'rb')
            request_params['files'] = {'file': upload_fh}

        self._log.debug(
            "Executing %s request to '%s' with args %s",
            method,
            url,
            {param: value for (param, value) in request_params.items() if param != 'headers'}
        )

        # The moment we've been waiting for...execute the request
        try:
            response = self.session.request(
                method,
                url,
                **request_params # type: ignore[arg-type]
            )
        finally:
            if upload:
                upload_fh.close()

        return response

    def _do_timeout_managed_request(
            self,
            method: str,
            url: str,
            payload: Optional[Any] = None,  # pylint: disable=unsubscriptable-object
            upload: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            **params
        ) -> requests.Response:
        """Performs a single request against the PCO API with automatic retried in case of timeout.

        Executed request could be one of the standard HTTP verbs or a file upload.

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.

        Returns:
            requests.Response: The response to this request.
        """

        timeout_count = 0

        while True:
            try:
                return self._do_request(method, url, payload, upload, **params)

            except requests.exceptions.Timeout as exc:
                timeout_count += 1

                self._log.debug("The request to \"%s\" timed out after %d tries.",
                                url, timeout_count)

                if timeout_count == self.timeout_retries:
                    self._log.debug("Maximum retries (%d) hit. Will raise exception.",
                                    self.timeout_retries)

                    raise PCORequestTimeoutException(
                        f"The request to \"{url}\" timed out after {timeout_count} tries.") from exc

                continue

    def _do_ratelimit_managed_request(
            self,
            method: str,
            url: str,
            payload: Optional[Any] = None,  # pylint: disable=unsubscriptable-object
            upload: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            **params
        ) -> requests.Response:
        """Performs a single request against the PCO API with automatic rate limit handling.

        Executed request could be one of the standard HTTP verbs or a file upload.

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.

        Returns:
            requests.Response: The response to this request.
        """

        while True:

            response = self._do_timeout_managed_request(method, url, payload, upload, **params)

            if response.status_code == 429:
                self._log.debug("Received rate limit response. Will try again after %d sec(s).",
                                int(response.headers['Retry-After']))

                time.sleep(int(response.headers['Retry-After']))
                continue

            return response

    def _do_url_managed_request(
            self,
            method: str,
            url: str,
            payload: Optional[Any] = None,  # pylint: disable=unsubscriptable-object
            upload: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            **params
        ) -> requests.Response:
        """Performs a single request against the PCO API, automatically cleaning up the URL.

        Executed request could be one of the standard HTTP verbs or a file upload.

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.

        Returns:
            requests.Response: The response to this request.
        """

        self._log.debug("URL cleaning input: \"%s\"", url)

        if not upload:
            url = url if url.startswith(self.api_base) else f'{self.api_base}{url}'
            url = re.subn(r'(?<!:)[/]{2,}', '/', url)[0]

        self._log.debug("URL cleaning output: \"%s\"", url)

        return self._do_ratelimit_managed_request(method, url, payload, upload, **params)

    def request_response(
            self,
            method: str,
            url: str,
            payload: Optional[Any] = None,  # pylint: disable=unsubscriptable-object
            upload: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            **params
        ) -> requests.Response:
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
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            requests.Response: The response to this request.
        """

        try:
            response = self._do_url_managed_request(method, url, payload, upload, **params)
        except Exception as err:
            self._log.debug("Request resulted in unexpected error: \"%s\"", str(err))
            raise PCOUnexpectedRequestException(str(err)) from err

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            self._log.debug("Request resulted in API error: \"%s\"", str(err))
            raise PCORequestException(
                response.status_code,
                str(err),
                response_body=response.text
            ) from err

        return response

    def request_json(
            self,
            method: str,
            url: str,
            payload: Optional[Any] = None,  # pylint: disable=unsubscriptable-object
            upload: Optional[str] = None,  # pylint: disable=unsubscriptable-object
            **params: str
    ) -> Optional[dict]:  # pylint: disable=unsubscriptable-object
        """A generic entry point for making a managed request against PCO.

        This function will return the payload from the PCO response (a dict).

        Args:
            method (str): The HTTP method to use for this request.
            url (str): The URL against which this request will be executed.
            payload (obj): A json-serializable Python object to be sent as the post/put payload.
            upload(str): The path to a file to upload.
            params (obj): A dictionary or list of tuples or bytes to send in the query string.

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            dict: The payload from the response to this request.
        """

        response = self.request_response(method, url, payload, upload, **params)
        if response.status_code == 204:
            return_value = None
        else:
            return_value = response.json()

        return return_value

    def get(self, url: str, **params) -> Optional[dict]:  # pylint: disable=unsubscriptable-object
        """Perform a GET request against the PCO API.

        Performs a fully managed GET request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            params: Any named arguments will be passed as query parameters.

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            dict: The payload returned by the API for this request.
        """

        return self.request_json('GET', url, **params)

    def post(
            self,
            url: str,
            payload: Optional[dict] = None,  # pylint: disable=unsubscriptable-object
            **params: str
        ) -> Optional[dict]:  # pylint: disable=unsubscriptable-object
        """Perform a POST request against the PCO API.

        Performs a fully managed POST request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            payload (dict): The payload for the POST request. Must be serializable to JSON!
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            dict: The payload returned by the API for this request.
        """

        return self.request_json('POST', url, payload, **params)

    def patch(
            self,
            url: str,
            payload: Optional[dict] = None,  # pylint: disable=unsubscriptable-object
            **params: str
        ) -> Optional[dict]:  # pylint: disable=unsubscriptable-object
        """Perform a PATCH request against the PCO API.

        Performs a fully managed PATCH request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            payload (dict): The payload for the PUT request. Must be serializable to JSON!
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            dict: The payload returned by the API for this request.
        """

        return self.request_json('PATCH', url, payload, **params)

    def delete(self, url: str, **params: str) -> requests.Response:
        """Perform a DELETE request against the PCO API.

        Performs a fully managed DELETE request (handles ratelimiting, timeouts, etc.).

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            requests.Response: The response object returned by the API for this request.
            A successful delete request will return a response with an empty payload,
            so we return the response object here instead.
        """

        return self.request_response('DELETE', url, **params)

    def iterate(self, url: str, offset: int = 0, per_page: int = 25, **params: str) -> Iterator[dict]:  # pylint: disable=too-many-branches
        """Iterate a list of objects in a response, handling pagination.

        Basically, this function wraps get in a generator function designed for
        processing requests that will return multiple objects. Pagination is
        transparently handled.

        Objects specified as includes will be injected into their associated
        object and returned.

        Args:
            url (str): The URL against which to perform the request. Can include
                what's been set as api_base, which will be ignored if this value is also
                present in your URL.
            offset (int): The offset at which to start. Usually going to be 0 (the default).
            per_page (int): The number of results that should be requested in a single page.
                Valid values are 1 - 100, defaults to the PCO default of 25.
            params: Any additional named arguments will be passed as query parameters. Values must
                be of type str!

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Yields:
            dict: Each object returned by the API for this request. Returns "data",
            "included", and "meta" nodes for each response. Note that data is processed somewhat
            before being returned from the API. Namely, includes are injected into the object(s)
            with which they are associated. This makes it easier to process includes associated with
            specific objects since they are accessible directly from each returned object.
        """

        while True:  # pylint: disable=too-many-nested-blocks

            response = self.get(url, offset=offset, per_page=per_page, **params)

            if response is None:
                return

            for cur in response['data']:
                record = {
                    'data': cur,
                    'included': [],
                    'meta': {}
                }

                if 'can_include' in response['meta']:
                    record['meta']['can_include'] = response['meta']['can_include']

                if 'parent' in response['meta']:
                    record['meta']['parent'] = response['meta']['parent']

                if 'relationships' in cur:
                    for key in cur['relationships']:
                        relationships = cur['relationships'][key]['data']

                        if relationships is not None:
                            if isinstance(relationships, dict):
                                for include in response['included']:
                                    if include['type'] == relationships['type'] and \
                                            include['id'] == relationships['id']:
                                        record['included'].append(include)

                            elif isinstance(relationships, list):
                                for relationship in relationships:
                                    for include in response['included']:
                                        if include['type'] == relationship['type'] and \
                                                include['id'] == relationship['id']:
                                            record['included'].append(include)

                yield record

            offset += per_page

            if 'next' not in response['links']:
                break

    def upload(self, file_path: str, **params) -> Optional[dict]:  # pylint: disable=unsubscriptable-object
        """Upload the file at the specified path to PCO.

        Args:
            file_path (str): The path to the file to be uploaded to PCO.
            params: Any named arguments will be passed as query parameters. Values must
                be of type str!

        Raises:
            PCORequestTimeoutException: The request to PCO timed out the maximum number of times.
            PCOUnexpectedRequestException: An unexpected error occurred when making your request.
            PCORequestException: The response from the PCO API indicated an error with your request.

        Returns:
            dict: The PCO response from the file upload.
        """

        return self.request_json('POST', self.upload_url, upload=file_path, **params)

    def __del__(self):
        """Close the requests session when the PCO object goes out of scope."""

        self.session.close()

    @staticmethod
    def template(
            object_type: str,
            attributes: Optional[dict] = None  # pylint: disable=unsubscriptable-object
    ) -> dict:
        """Get template JSON for creating a new object.

        Args:
            object_type (str): The type of object to be created.
            attributes (dict): The new objects attributes. Defaults to empty.

        Returns:
            dict: A template from which to set the new object's attributes.
        """

        return {
            'data': {
                'type': object_type,
                'attributes': {} if attributes is None else attributes
            }
        }

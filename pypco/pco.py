import time
import logging

import requests

from .auth_config import PCOAuthConfig

class PCO(object):
    """The entry point to the PCO API.

    Attributes:
        auth_config (PCOAuthConfig): The authentication configuration for this instance.
    """

    def __init__(self, api_base, application_id=None, secret=None, token=None):
        """Initialize the PCO entry point.

        Args:
            api_base (str): The base URL against which REST calls will be made.
            application_id (str): The application_id; secret must also be specified.
            secret (str): The secret for your app; application_id must also be specified.
            token (str): OAUTH token for your app; application_id and secret must not be specified.

        Note:
            You must specify either an application ID and a secret or an oauth token.
            If you specify an invalid combination of these arguments, an exception will be
            raised when you attempt to make API calls.
        """

        self._log = logging.getLogger(__name__)
        self._log.info("Initializing the PCO wrapper.")

        self.api_base = api_base

        self.auth_config = PCOAuthConfig(application_id, secret, token)
        self._log.debug("Initialized the auth_config object.")

    def _get_auth(self):
        pass

    def _dispatch_request(self, method, url, params=None, json=None):

        while True:

            timeout_count = 0

            while True:
                try:
                    headers = {'User-Agent': 'python-rocks'}

                    if method in ['POST', 'PUT']:
                        headers['Content-Type'] = 'application/json'

                    response = requests.request(
                        method,
                        f'{self.api_base}{url}',
                        auth=self._get_auth(),
                        params=params,
                        json=json,
                        headers=headers,
                        timeout=60
                    )

                    # No timeout, exit loop
                    break

                except requests.exceptions.Timeout as exc:
                    timeout_count += 1

                    if timeout_count == 3:
                        raise Exception("The request to \"%s\" timed out after %d tries." % (url, timeout_count)) from exc

                    continue

            if response.status_code == 429:
                time.sleep(int(response.headers['Retry-After']))
                continue

            response.raise_for_status()

            return response.json()

    def get(self, url, params=None, json=None):
        return self._dispatch_request('GET', url, params, json)

    def post(self, url, params=None, json=None):
        return self._dispatch_request('POST', url, params, json)

    def put(self, url, params=None, json=None):
        return self._dispatch_request('PUT', url, params, json)

    def delete(self, url, params=None, json=None):
        return self._dispatch_request('DELETE', url, params, json)

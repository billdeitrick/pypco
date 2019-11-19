"""Test the primary pypco entry point -- the PCO object"""

#pylint: disable=protected-access

from unittest.mock import Mock, patch

import requests

import pypco
from pypco.exceptions import PCORequestTimeoutException
from tests import BasePCOTestCase, BasePCOVCRTestCase

# Side effect functions and global vars

## Timeout testing
REQUEST_COUNT = 0
TIMEOUTS = 0

def timeout_se(*args, **kwargs):
    """A function to mock requests timeouts over multiple responses.

    You must set REQUEST_COUNT global variable to 0 and TIMEOUTS global variable to desired
    number before this function is be called.

    Returns:
        Mock: A mock response object.
    """

    global REQUEST_COUNT, TIMEOUTS #pylint: disable=global-statement

    REQUEST_COUNT += 1

    if REQUEST_COUNT == TIMEOUTS + 1:
        response = Mock()
        response.text = ''
        response.status_code = 200

        return response

    raise requests.exceptions.Timeout()

class TestPrivateRequestFunctions(BasePCOTestCase):
    """Test low-level request mechanisms."""

    @patch('requests.request')
    @patch('builtins.open')
    def test_do_request(self, mock_fh, mock_request):
        """Test dispatching single requests; HTTP verbs, file uploads, etc."""

        # Setup PCO object and request mock
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret'
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"hello": "world"}'
        mock_request.return_value = mock_response

        # GET
        pco._do_request(
            'GET',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            include='test',
            per_page=100
        )

        mock_request.assert_called_with(
            'GET',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            params={
                'include':'test',
                'per_page':100
            },
            headers={
                'User-Agent': 'pypco',
                'Authorization': 'Basic YXBwX2lkOnNlY3JldA==',
            },
            json=None,
            timeout=60,
        )

        # POST
        pco._do_request(
            'POST',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            payload={
                'type': 'Person',
                'attributes': {
                    'a': 1,
                    'b': 2
                }
            }
        )

        mock_request.assert_called_with(
            'POST',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            json={
                'type': 'Person',
                'attributes': {
                    'a': 1,
                    'b': 2
                }
            },
            headers={
                'User-Agent': 'pypco',
                'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='
            },
            params={},
            timeout=60
        )

        # File Upload
        mock_fh.name = "open()"

        pco._do_request(
            'POST',
            'https://api.planningcenteronline.com/somewhere/v2/something',
            upload='/file/path',
        )

        mock_fh.assert_called_once_with('/file/path', 'rb')

    @patch('requests.request', side_effect=timeout_se)
    def test_do_timeout_managed_request(self, mock_request):
        """Test requests that automatically will retry on timeout."""

        global REQUEST_COUNT, TIMEOUTS #pylint: disable=global-statement

        # Setup PCO object and request mock
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret'
        )

        REQUEST_COUNT = 0
        TIMEOUTS = 0

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 1, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 1

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 2, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 1

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 2, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 2

        pco._do_timeout_managed_request(
            'GET',
            '/test',
        )

        self.assertEqual(REQUEST_COUNT, 3, "Successful request not executed exactly once.")

        REQUEST_COUNT = 0
        TIMEOUTS = 3

        with self.assertRaises(PCORequestTimeoutException):
            pco._do_timeout_managed_request(
                'GET',
                '/test',
            )

        mock_request.assert_called_with(
            'GET',
            '/test',
            headers={'User-Agent': 'pypco', 'Authorization': 'Basic YXBwX2lkOnNlY3JldA=='},
            json=None,
            params={},
            timeout=60
        )

        # Let's try with only two retries permitted
        pco = pypco.PCO(
            'https://api.planningcenteronline.com',
            application_id='app_id',
            secret='secret',
            timeout_retries=2
        )

        REQUEST_COUNT = 0
        TIMEOUTS = 2

        with self.assertRaises(PCORequestTimeoutException):
            pco._do_timeout_managed_request(
                'GET',
                '/test',
            )

    def test_do_ratelimit_managed_request(self):
        pass

    def test_do_url_managed_request(self):
        pass

class TestPublicRequestFunctions(BasePCOVCRTestCase):
    """Test public PCO request functions."""
